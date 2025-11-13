#!/usr/bin/env python3
"""
Automated API Audit Tool
=========================

This tool automatically detects API mismatches in the codebase by:
1. Scanning method calls in source files
2. Comparing with actual method signatures in target classes
3. Validating parameter names and counts
4. Generating detailed audit reports

Based on API_FIXES_DEBUG_HISTORY.md analysis.

Usage:
    python tools/api_audit.py
    python tools/api_audit.py --verbose
    python tools/api_audit.py --output report.json
"""

import ast
import inspect
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import importlib.util


@dataclass
class MethodCall:
    """Represents a method call found in source code."""
    file: str
    line: int
    class_name: str
    method_name: str
    args: List[str] = field(default_factory=list)
    kwargs: List[str] = field(default_factory=list)
    full_context: str = ""


@dataclass
class MethodSignature:
    """Represents the actual method signature from a class."""
    class_name: str
    method_name: str
    params: List[str]
    required_params: List[str]
    optional_params: Dict[str, Any]
    file_path: str
    line_number: Optional[int] = None


@dataclass
class APIMismatch:
    """Represents an API mismatch between call and signature."""
    severity: str  # 'error', 'warning', 'info'
    type: str  # 'method_not_found', 'wrong_params', 'missing_required_params'
    call: MethodCall
    expected_signature: Optional[MethodSignature] = None
    message: str = ""


class MethodCallVisitor(ast.NodeVisitor):
    """AST visitor to find method calls in Python source code."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.calls: List[MethodCall] = []
        self.current_line = 0

    def visit_Call(self, node: ast.Call):
        """Visit function/method call nodes."""
        # Extract method name and object
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr

            # Try to extract class/object name
            obj_name = self._extract_object_name(node.func.value)

            if obj_name:
                # Extract arguments
                args = []
                kwargs = []

                for arg in node.args:
                    args.append(ast.unparse(arg))

                for keyword in node.keywords:
                    kwargs.append(keyword.arg)

                # Get source context
                try:
                    context = ast.get_source_segment(
                        open(self.filepath).read(),
                        node
                    ) or ""
                except:
                    context = ""

                call = MethodCall(
                    file=self.filepath,
                    line=node.lineno,
                    class_name=obj_name,
                    method_name=method_name,
                    args=args,
                    kwargs=kwargs,
                    full_context=context[:200]  # Limit context length
                )
                self.calls.append(call)

        self.generic_visit(node)

    def _extract_object_name(self, node) -> Optional[str]:
        """Extract object/class name from various AST node types."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle self.something.method()
            base = self._extract_object_name(node.value)
            if base:
                return f"{base}.{node.attr}"
        return None


class APIAuditor:
    """Main API audit tool."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.src_dir = self.root_dir / "src"

        # Known API classes and their locations
        self.api_classes = {
            "IterationHistory": "src.learning.iteration_history",
            "ChampionTracker": "src.learning.champion_tracker",
            "FeedbackGenerator": "src.learning.feedback_generator",
            "ErrorClassifier": "src.backtest.error_classifier",
            "SuccessClassifier": "src.backtest.classifier",
            "InnovationEngine": "src.innovation.innovation_engine",
            "IterationExecutor": "src.learning.iteration_executor",
            "LearningLoop": "src.learning.learning_loop",
        }

        # Cache for loaded signatures
        self.signature_cache: Dict[str, Dict[str, MethodSignature]] = {}

        # Results
        self.all_calls: List[MethodCall] = []
        self.mismatches: List[APIMismatch] = []

    def scan_directory(self, directory: Path = None) -> List[MethodCall]:
        """Scan all Python files in directory for method calls."""
        if directory is None:
            directory = self.src_dir

        calls = []
        for py_file in directory.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                calls.extend(self._scan_file(str(py_file)))
            except Exception as e:
                print(f"Warning: Failed to scan {py_file}: {e}")

        return calls

    def _scan_file(self, filepath: str) -> List[MethodCall]:
        """Scan a single Python file for method calls."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=filepath)

            visitor = MethodCallVisitor(filepath)
            visitor.visit(tree)
            return visitor.calls
        except SyntaxError as e:
            print(f"Syntax error in {filepath}: {e}")
            return []

    def load_api_signature(self, class_name: str) -> Dict[str, MethodSignature]:
        """Load method signatures for a class."""
        if class_name in self.signature_cache:
            return self.signature_cache[class_name]

        if class_name not in self.api_classes:
            return {}

        module_path = self.api_classes[class_name]

        try:
            # Import the module
            module = self._import_module(module_path)
            if not module:
                return {}

            # Get the class
            cls = getattr(module, class_name, None)
            if not cls:
                return {}

            # Extract method signatures
            signatures = {}
            for name, method in inspect.getmembers(cls, inspect.isfunction):
                if name.startswith('_') and not name.startswith('__'):
                    continue  # Skip private methods

                sig = inspect.signature(method)
                params = []
                required = []
                optional = {}

                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue

                    params.append(param_name)

                    if param.default == inspect.Parameter.empty:
                        required.append(param_name)
                    else:
                        optional[param_name] = param.default

                # Get source file and line number
                try:
                    source_file = inspect.getsourcefile(method)
                    source_lines = inspect.getsourcelines(method)
                    line_num = source_lines[1]
                except:
                    source_file = module_path
                    line_num = None

                signatures[name] = MethodSignature(
                    class_name=class_name,
                    method_name=name,
                    params=params,
                    required_params=required,
                    optional_params=optional,
                    file_path=source_file or module_path,
                    line_number=line_num
                )

            self.signature_cache[class_name] = signatures
            return signatures

        except Exception as e:
            print(f"Warning: Failed to load signatures for {class_name}: {e}")
            return {}

    def _import_module(self, module_path: str):
        """Dynamically import a module."""
        try:
            parts = module_path.split('.')
            file_path = self.root_dir / '/'.join(parts) / '__init__.py'
            if not file_path.exists():
                file_path = self.root_dir / '/'.join(parts[:-1]) / f"{parts[-1]}.py"

            if not file_path.exists():
                return None

            spec = importlib.util.spec_from_file_location(module_path, file_path)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_path] = module
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            print(f"Failed to import {module_path}: {e}")
            return None

    def audit_call(self, call: MethodCall) -> Optional[APIMismatch]:
        """Audit a single method call against known API."""
        # Extract base class name (remove "self." prefix if present)
        class_name = call.class_name.replace("self.", "")

        # Check if this is a known API class
        signatures = self.load_api_signature(class_name)
        if not signatures:
            return None  # Not an API class we're tracking

        # Check if method exists
        if call.method_name not in signatures:
            return APIMismatch(
                severity='error',
                type='method_not_found',
                call=call,
                expected_signature=None,
                message=f"Method '{call.method_name}' not found in {class_name}. "
                       f"Available methods: {', '.join(signatures.keys())}"
            )

        # Check parameter compatibility
        signature = signatures[call.method_name]

        # Check required parameters
        missing_required = []
        for required_param in signature.required_params:
            if required_param not in call.kwargs:
                # Also check positional args
                param_index = signature.params.index(required_param)
                if param_index >= len(call.args):
                    missing_required.append(required_param)

        if missing_required:
            return APIMismatch(
                severity='error',
                type='missing_required_params',
                call=call,
                expected_signature=signature,
                message=f"Missing required parameters: {', '.join(missing_required)}. "
                       f"Expected: {signature.params}"
            )

        # Check for unknown parameters
        unknown_params = []
        for kwarg in call.kwargs:
            if kwarg not in signature.params:
                unknown_params.append(kwarg)

        if unknown_params:
            return APIMismatch(
                severity='warning',
                type='unknown_params',
                call=call,
                expected_signature=signature,
                message=f"Unknown parameters: {', '.join(unknown_params)}. "
                       f"Expected: {signature.params}"
            )

        return None  # No mismatch found

    def run_audit(self) -> List[APIMismatch]:
        """Run complete audit on the codebase."""
        print("🔍 Starting API audit...")

        # Scan for method calls
        print(f"📂 Scanning {self.src_dir}...")
        self.all_calls = self.scan_directory()
        print(f"✅ Found {len(self.all_calls)} method calls")

        # Audit each call
        print("🔎 Auditing method calls...")
        self.mismatches = []
        for call in self.all_calls:
            mismatch = self.audit_call(call)
            if mismatch:
                self.mismatches.append(mismatch)

        # Group and report
        errors = [m for m in self.mismatches if m.severity == 'error']
        warnings = [m for m in self.mismatches if m.severity == 'warning']

        print(f"\n📊 Audit Results:")
        print(f"   🔴 Errors: {len(errors)}")
        print(f"   🟡 Warnings: {len(warnings)}")

        return self.mismatches

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate detailed audit report."""
        report = []
        report.append("=" * 80)
        report.append("API AUDIT REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        errors = [m for m in self.mismatches if m.severity == 'error']
        warnings = [m for m in self.mismatches if m.severity == 'warning']

        report.append("Summary:")
        report.append(f"  Total method calls scanned: {len(self.all_calls)}")
        report.append(f"  Errors found: {len(errors)}")
        report.append(f"  Warnings found: {len(warnings)}")
        report.append("")

        # Errors
        if errors:
            report.append("-" * 80)
            report.append("🔴 ERRORS")
            report.append("-" * 80)
            for i, mismatch in enumerate(errors, 1):
                report.append(f"\n{i}. {mismatch.type.upper()}")
                report.append(f"   File: {mismatch.call.file}:{mismatch.call.line}")
                report.append(f"   Call: {mismatch.call.class_name}.{mismatch.call.method_name}()")
                report.append(f"   Message: {mismatch.message}")
                if mismatch.expected_signature:
                    report.append(f"   Expected signature: {mismatch.expected_signature.method_name}("
                                f"{', '.join(mismatch.expected_signature.params)})")

        # Warnings
        if warnings:
            report.append("")
            report.append("-" * 80)
            report.append("🟡 WARNINGS")
            report.append("-" * 80)
            for i, mismatch in enumerate(warnings, 1):
                report.append(f"\n{i}. {mismatch.type.upper()}")
                report.append(f"   File: {mismatch.call.file}:{mismatch.call.line}")
                report.append(f"   Call: {mismatch.call.class_name}.{mismatch.call.method_name}()")
                report.append(f"   Message: {mismatch.message}")

        report.append("")
        report.append("=" * 80)

        report_text = "\n".join(report)

        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n📄 Report saved to: {output_file}")

        return report_text

    def generate_json_report(self, output_file: str):
        """Generate JSON format report."""
        data = {
            "summary": {
                "total_calls": len(self.all_calls),
                "total_mismatches": len(self.mismatches),
                "errors": len([m for m in self.mismatches if m.severity == 'error']),
                "warnings": len([m for m in self.mismatches if m.severity == 'warning'])
            },
            "mismatches": [
                {
                    "severity": m.severity,
                    "type": m.type,
                    "file": m.call.file,
                    "line": m.call.line,
                    "class": m.call.class_name,
                    "method": m.call.method_name,
                    "message": m.message,
                    "expected_signature": {
                        "method": m.expected_signature.method_name,
                        "params": m.expected_signature.params,
                        "required": m.expected_signature.required_params
                    } if m.expected_signature else None
                }
                for m in self.mismatches
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"📄 JSON report saved to: {output_file}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='API Audit Tool')
    parser.add_argument('--root', default='.', help='Root directory of the project')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--output', help='Output report file (text format)')
    parser.add_argument('--json', help='Output report file (JSON format)')

    args = parser.parse_args()

    # Run audit
    auditor = APIAuditor(root_dir=args.root)
    mismatches = auditor.run_audit()

    # Generate reports
    if args.output:
        auditor.generate_report(output_file=args.output)
    else:
        print("\n" + auditor.generate_report())

    if args.json:
        auditor.generate_json_report(args.json)

    # Exit with error code if errors found
    errors = [m for m in mismatches if m.severity == 'error']
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
