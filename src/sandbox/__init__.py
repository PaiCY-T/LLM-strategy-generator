"""
Docker Sandbox Security Module

Provides secure isolated execution environment for autonomous strategy backtesting.
Implements security validation, Docker containerization, and resource monitoring.

Modules:
- security_validator: AST-based code validation before execution
- docker_config: Configuration management for Docker settings
- docker_executor: Container lifecycle management with resource limits
- container_monitor: Container resource tracking and cleanup
"""

__all__ = [
    'SecurityValidator',
    'DockerConfig',
    'DockerExecutor',
    'ContainerMonitor',
]
