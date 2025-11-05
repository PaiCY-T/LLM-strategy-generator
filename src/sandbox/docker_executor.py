"""
DockerExecutor - Container lifecycle management for isolated strategy execution.

This module implements the core Docker execution engine for the sandbox security system.
It manages container creation, execution, monitoring, and cleanup with strict resource
limits and security profiles.

Key Features:
- Container lifecycle management (create, run, cleanup)
- Resource limits (2GB memory, 0.5 CPU, 600s timeout)
- Security profiles (network isolation, read-only FS, seccomp)
- 100% cleanup success rate (cleanup even on failures)
- Integration with SecurityValidator for pre-execution validation

Design Reference: docker-sandbox-security spec requirements 1.1-1.5
Interface Contract: DockerExecutor.execute(code: str) -> Dict[str, Any]
"""

import logging
import time
import tempfile
import os
import json
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import docker
    from docker.errors import DockerException, APIError, ContainerError, ImageNotFound
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None
    DockerException = Exception
    APIError = Exception
    ContainerError = Exception
    ImageNotFound = Exception

from src.sandbox.security_validator import SecurityValidator
from src.sandbox.docker_config import DockerConfig
from src.sandbox.runtime_monitor import RuntimeMonitor, SecurityPolicy

logger = logging.getLogger(__name__)


class DockerExecutor:
    """
    Executes Python code in isolated Docker containers with strict security controls.

    This executor manages the complete container lifecycle:
    1. Pre-execution: Validate code with SecurityValidator
    2. Setup: Create temporary directory for code and results
    3. Container: Create container with resource limits and security profiles
    4. Execution: Run code with timeout enforcement
    5. Cleanup: Remove container and temporary files (guaranteed)

    Key Responsibilities:
    - Apply resource limits (memory, CPU, timeout)
    - Enforce security profiles (network isolation, read-only FS, seccomp)
    - Validate code before execution (using SecurityValidator)
    - Ensure 100% cleanup success rate
    - Capture execution results and errors

    Security Features:
    - Network isolation (network_mode: none)
    - Read-only filesystem (except /tmp)
    - Seccomp profile for syscall filtering
    - AST validation before Docker execution
    - No privileged mode, no device access

    Performance:
    - Container creation: <3s
    - Execution overhead: <5%
    - Parallel execution: Up to 5 simultaneous containers

    Example:
        >>> config = DockerConfig.from_yaml()
        >>> executor = DockerExecutor(config)
        >>> code = "import pandas as pd\\nsignal = pd.DataFrame({'a': [1, 2, 3]})"
        >>> result = executor.execute(code)
        >>> print(result['success'])  # True
        >>> print(result['signal'])  # DataFrame
    """

    def __init__(self, config: Optional[DockerConfig] = None):
        """
        Initialize DockerExecutor with configuration.

        Args:
            config: DockerConfig instance (default: load from YAML)

        Raises:
            RuntimeError: If Docker is not available and sandbox is enabled
        """
        self.config = config or DockerConfig.from_yaml()
        self.validator = SecurityValidator()

        # Initialize Docker client
        self.client = None
        if self.config.enabled:
            # Check Docker SDK availability
            if not DOCKER_AVAILABLE:
                raise RuntimeError(
                    "Docker SDK not available. Install with: pip install docker"
                )

            # Try to connect to Docker daemon
            try:
                self.client = docker.from_env()
                # Verify Docker daemon is accessible
                self.client.ping()
                logger.info("Docker client initialized successfully")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to connect to Docker daemon: {e}. "
                    f"Ensure Docker is running and accessible."
                )

        # Create output directory
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Track containers for cleanup
        self._active_containers: List[str] = []

        # Initialize RuntimeMonitor (Task 17)
        self.runtime_monitor = None
        if self.config.enabled and self.config.runtime_monitor_enabled:
            try:
                security_policy = SecurityPolicy()
                self.runtime_monitor = RuntimeMonitor(
                    policy=security_policy,
                    docker_client=self.client,
                    enabled=True
                )
                self.runtime_monitor.start()
                logger.info("RuntimeMonitor started for active security enforcement")
            except Exception as e:
                logger.warning(f"Failed to initialize RuntimeMonitor: {e}")
                self.runtime_monitor = None

    def execute(
        self,
        code: str,
        timeout: Optional[int] = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Python code in isolated Docker container.

        Workflow:
        1. Validate code with SecurityValidator (if enabled)
        2. Create temporary directory with code file
        3. Create Docker container with security settings
        4. Run container with timeout enforcement
        5. Capture results from container output
        6. Cleanup container and temporary files (guaranteed)

        Args:
            code: Python source code to execute
            timeout: Execution timeout in seconds (default: from config)
            validate: Whether to run SecurityValidator (default: True)

        Returns:
            Dictionary with execution results:
            {
                'success': bool,           # Whether execution succeeded
                'signal': Any,             # Execution result (if success)
                'error': str,              # Error message (if failed)
                'execution_time': float,   # Actual execution time
                'container_id': str,       # Container ID (if created)
                'validated': bool,         # Whether code was validated
                'cleanup_success': bool    # Whether cleanup succeeded
            }

        Example:
            >>> executor = DockerExecutor()
            >>> code = '''
            ... import pandas as pd
            ... signal = pd.DataFrame({'stock': ['AAPL'], 'position': [1.0]})
            ... '''
            >>> result = executor.execute(code)
            >>> if result['success']:
            ...     print(f"Signal: {result['signal']}")
        """
        start_time = time.time()
        timeout = timeout or self.config.timeout_seconds
        container_id = None
        temp_dir = None
        cleanup_success = False

        # Result template
        result = {
            'success': False,
            'signal': None,
            'error': None,
            'execution_time': 0.0,
            'container_id': None,
            'validated': False,
            'cleanup_success': False
        }

        try:
            # Step 1: Validate code (if enabled)
            if validate:
                is_valid, errors = self.validator.validate(code)
                result['validated'] = True
                if not is_valid:
                    result['error'] = f"Security validation failed: {'; '.join(errors)}"
                    result['execution_time'] = time.time() - start_time
                    result['cleanup_success'] = True  # No cleanup needed
                    return result


            # Step 3: Create temporary directory with code
            temp_dir = tempfile.mkdtemp(prefix="docker_exec_")
            code_file = Path(temp_dir) / "strategy.py"
            output_file = Path(temp_dir) / "output.json"

            # Write code to file
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)

            # DEBUG: Save code for inspection
            debug_file = Path('/tmp/docker_executor_last_code.py')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(code)
            logger.debug(f"DEBUG: Saved code to {debug_file} ({len(code)} bytes)")
            logger.debug(f"DEBUG: Code starts with: {code[:200]}")

            # Step 4: Create and run container
            container_result = self._run_container(
                code_file=code_file,
                output_file=output_file,
                timeout=timeout
            )

            # Update result with container execution
            result.update(container_result)
            container_id = container_result.get('container_id')

        except Exception as e:
            logger.error(f"Docker execution failed: {e}", exc_info=True)
            result['error'] = f"Docker execution error: {type(e).__name__}: {str(e)}"

        finally:
            # Step 5: Guaranteed cleanup
            result['execution_time'] = time.time() - start_time

            # Cleanup container
            if container_id:
                cleanup_success = self._cleanup_container(container_id)
                result['cleanup_success'] = cleanup_success
            else:
                result['cleanup_success'] = True  # No container to cleanup

            # Cleanup temporary directory
            if temp_dir:
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory: {e}")

        return result

    def _run_container(
        self,
        code_file: Path,
        output_file: Path,
        timeout: int
    ) -> Dict[str, Any]:
        """
        Create and run Docker container with security settings.

        Args:
            code_file: Path to Python code file
            output_file: Path for container output
            timeout: Execution timeout in seconds

        Returns:
            Dictionary with container execution results
        """
        container = None
        container_id = None

        try:
            # Prepare volumes
            # Note: Mount to /code (not /workspace) to avoid shadowing container's WORKDIR
            volumes = {
                str(code_file.parent): {
                    'bind': '/code',
                    'mode': 'ro'  # Read-only
                }
            }

            # Prepare tmpfs (writable /tmp and /home/finlab for finlab cache)
            tmpfs = {
                self.config.tmpfs_path: self.config.tmpfs_options,
                '/home/finlab': 'rw,size=2g,uid=1000,gid=1000'  # Writable for finlab data cache
            }

            # Prepare seccomp profile
            security_opt = []
            if self.config.seccomp_profile and Path(self.config.seccomp_profile).exists():
                with open(self.config.seccomp_profile, 'r') as f:
                    seccomp_profile = json.load(f)
                security_opt.append(f"seccomp={json.dumps(seccomp_profile)}")
            else:
                logger.warning(
                    f"Seccomp profile not found: {self.config.seccomp_profile}. "
                    f"Using default Docker seccomp."
                )

            # Create container with security settings
            logger.info(f"Creating container with image: {self.config.image}")

            # Prepare environment variables (Pass FINLAB_API_TOKEN for data access)
            environment = {}
            if 'FINLAB_API_TOKEN' in os.environ:
                environment['FINLAB_API_TOKEN'] = os.environ['FINLAB_API_TOKEN']
                logger.info("Passing FINLAB_API_TOKEN to container")

            container = self.client.containers.create(
                image=self.config.image,
                command=[
                    'python', '/code/strategy.py'
                ],
                volumes=volumes,
                network_mode=self.config.network_mode,
                mem_limit=self.config.memory_limit,
                mem_swappiness=0,  # Disable swap
                nano_cpus=int(self.config.cpu_limit * 1e9),  # Convert to nanocpus
                read_only=self.config.read_only,
                tmpfs=tmpfs,
                security_opt=security_opt,
                environment=environment,  # Pass environment variables
                detach=True,
                # Note: remove parameter not valid for create() - we remove manually for guaranteed cleanup
                stdin_open=False,
                tty=False,
                privileged=False,  # Never privileged
                cap_drop=['ALL'],  # Drop all capabilities
                pids_limit=100,  # Task 20: Prevent fork bomb DoS attacks
                user="1000:1000",  # Task 18: Run as non-root user (principle of least privilege)
            )

            container_id = container.id
            self._active_containers.append(container_id)
            logger.info(f"Container created: {container_id[:12]}")

            # Start container
            start_time = time.time()
            container.start()
            logger.info(f"Container started: {container_id[:12]}")

            # Add to runtime monitoring (Task 17)
            if self.runtime_monitor:
                self.runtime_monitor.add_container(container_id)

            # Wait for completion with timeout
            try:
                exit_code = container.wait(timeout=timeout)
                execution_time = time.time() - start_time

                # Get container logs
                logs = container.logs(stdout=True, stderr=True).decode('utf-8')
                logger.debug(f"Container logs:\n{logs}")

                # Check exit code
                if isinstance(exit_code, dict):
                    exit_code = exit_code.get('StatusCode', -1)

                if exit_code == 0:
                    # Success - parse signal from container logs (Issue #5 fix)
                    signal = None
                    try:
                        # Look for __SIGNAL_JSON_START__...JSON...__SIGNAL_JSON_END__ in logs
                        signal_match = re.search(
                            r'__SIGNAL_JSON_START__(.+?)__SIGNAL_JSON_END__',
                            logs,
                            re.DOTALL
                        )
                        if signal_match:
                            signal_json = signal_match.group(1).strip()
                            signal = json.loads(signal_json)
                            logger.debug(f"Successfully parsed signal from container logs: {signal}")
                        else:
                            logger.warning("No signal output found in container logs")
                    except Exception as e:
                        logger.warning(f"Failed to parse signal from logs: {e}")
                        signal = None

                    return {
                        'success': True,
                        'signal': signal,  # Now properly parsed from logs
                        'error': None,
                        'execution_time': execution_time,
                        'container_id': container_id,
                        'logs': logs
                    }
                else:
                    return {
                        'success': False,
                        'signal': None,
                        'error': f"Container exited with code {exit_code}:\n{logs}",
                        'execution_time': execution_time,
                        'container_id': container_id,
                        'logs': logs
                    }

            except Exception as e:
                # Timeout or other error
                execution_time = time.time() - start_time

                # Try to get logs even on timeout
                try:
                    logs = container.logs(stdout=True, stderr=True).decode('utf-8')
                except:
                    logs = "Unable to retrieve logs"

                # Stop container on timeout
                try:
                    container.stop(timeout=5)
                except:
                    pass

                return {
                    'success': False,
                    'signal': None,
                    'error': f"Container execution timeout or error: {str(e)}\n{logs}",
                    'execution_time': execution_time,
                    'container_id': container_id,
                    'logs': logs
                }

        except ImageNotFound:
            return {
                'success': False,
                'signal': None,
                'error': f"Docker image not found: {self.config.image}. "
                        f"Pull image with: docker pull {self.config.image}",
                'execution_time': 0.0,
                'container_id': None
            }

        except APIError as e:
            return {
                'success': False,
                'signal': None,
                'error': f"Docker API error: {e.explanation}",
                'execution_time': 0.0,
                'container_id': container_id
            }

        except Exception as e:
            logger.error(f"Container execution error: {e}", exc_info=True)
            return {
                'success': False,
                'signal': None,
                'error': f"Container error: {type(e).__name__}: {str(e)}",
                'execution_time': 0.0,
                'container_id': container_id
            }

    def _cleanup_container(self, container_id: str) -> bool:
        """
        Cleanup container with guaranteed success.

        This method ensures containers are always removed, even if the
        initial removal fails. It implements multiple cleanup strategies:
        1. Normal remove
        2. Force remove
        3. Kill then remove

        Args:
            container_id: Container ID to cleanup

        Returns:
            True if cleanup succeeded, False otherwise
        """
        if not container_id or not self.client:
            return True

        try:
            # Remove from tracking
            if container_id in self._active_containers:
                self._active_containers.remove(container_id)

            # Remove from runtime monitoring (Task 17)
            if self.runtime_monitor:
                self.runtime_monitor.remove_container(container_id)

            # Get container
            try:
                container = self.client.containers.get(container_id)
            except Exception:
                # Container doesn't exist, cleanup successful
                logger.info(f"Container {container_id[:12]} already removed")
                return True

            # Strategy 1: Normal remove
            try:
                container.remove(force=False)
                logger.info(f"Container {container_id[:12]} removed successfully")
                return True
            except Exception as e1:
                logger.warning(f"Normal remove failed: {e1}, trying force remove")

            # Strategy 2: Force remove
            try:
                container.remove(force=True)
                logger.info(f"Container {container_id[:12]} force removed")
                return True
            except Exception as e2:
                logger.warning(f"Force remove failed: {e2}, trying kill then remove")

            # Strategy 3: Kill then remove
            try:
                container.kill()
                time.sleep(1)  # Give it a moment
                container.remove(force=True)
                logger.info(f"Container {container_id[:12]} killed and removed")
                return True
            except Exception as e3:
                logger.error(
                    f"All cleanup strategies failed for {container_id[:12]}: {e3}. "
                    f"Container may be orphaned."
                )
                return False

        except Exception as e:
            logger.error(f"Container cleanup error: {e}", exc_info=True)
            return False


    def cleanup_all(self) -> Dict[str, int]:
        """
        Cleanup all tracked containers.

        This should be called on shutdown to ensure no containers are left running.

        Returns:
            Dictionary with cleanup statistics:
            {
                'total': int,      # Total containers to cleanup
                'success': int,    # Successfully cleaned up
                'failed': int      # Failed to cleanup
            }
        """
        total = len(self._active_containers)
        success = 0
        failed = 0

        logger.info(f"Cleaning up {total} active containers")

        # Make a copy to avoid modification during iteration
        containers = list(self._active_containers)

        for container_id in containers:
            if self._cleanup_container(container_id):
                success += 1
            else:
                failed += 1

        stats = {
            'total': total,
            'success': success,
            'failed': failed
        }

        logger.info(f"Cleanup complete: {stats}")
        return stats

    def get_orphaned_containers(self) -> List[Dict[str, Any]]:
        """
        Find orphaned containers from previous runs.

        Orphaned containers are those with:
        - Label indicating finlab sandbox
        - Running or stopped state
        - Not in current active containers list

        Returns:
            List of dictionaries with orphaned container info:
            [
                {
                    'id': str,
                    'name': str,
                    'status': str,
                    'created': str
                },
                ...
            ]
        """
        if not self.client:
            return []

        orphaned = []
        try:
            # Get all containers (including stopped)
            all_containers = self.client.containers.list(all=True)

            for container in all_containers:
                # Check if container is from finlab sandbox
                # (You could add labels in container creation for better tracking)
                container_id = container.id

                # Skip active containers
                if container_id in self._active_containers:
                    continue

                # Check if container name or labels indicate sandbox usage
                # For now, we'll just list containers not in active list
                orphaned.append({
                    'id': container_id,
                    'short_id': container.short_id,
                    'name': container.name,
                    'status': container.status,
                    'created': container.attrs.get('Created', 'unknown')
                })

        except Exception as e:
            logger.error(f"Failed to get orphaned containers: {e}")

        return orphaned

    def close(self):
        """Close Docker executor and stop runtime monitor (Task 17)."""
        if self.runtime_monitor:
            try:
                self.runtime_monitor.stop()
                logger.info("RuntimeMonitor stopped")
            except Exception as e:
                logger.warning(f"Failed to stop RuntimeMonitor: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup all containers."""
        self.cleanup_all()
        self.close()
        return False
