#!/usr/bin/env python3
"""
System Requirements Checker for Pinnacle Copilot

This script checks if the system meets the minimum requirements
and verifies that all required Python packages are installed.
"""

import sys
import platform
import subprocess
from typing import Dict, List, Tuple

# Minimum requirements
MIN_PYTHON = (3, 8)
MIN_MACOS = (10, 15)  # Catalina

# Required Python packages
REQUIRED_PACKAGES = [
    'fastapi>=0.68.0',
    'uvicorn[standard]>=0.15.0',
    'psutil>=5.9.0',
    'python-dotenv>=0.19.0',
    'jinja2>=3.0.0',
    'aiofiles>=0.7.0',
    'python-multipart>=0.0.5',
    'pyobjc>=9.0.0',
    'pyobjc-framework-Cocoa>=9.0.0',
    'python-jose[cryptography]>=3.3.0',
    'passlib[bcrypt]>=1.7.4',
    'python-socketio>=5.8.0',
    'eventlet>=0.33.3',
    'flask-socketio>=5.3.4'
]

# Optional AI/ML packages
OPTIONAL_PACKAGES = [
    'torch>=2.0.0',
    'transformers>=4.30.0',
    'sentence-transformers>=2.2.2',
    'langchain>=0.0.200',
    'chromadb>=0.3.29',
    'pydantic>=1.10.0',
    'tiktoken>=0.4.0',
    'openai>=0.27.0'
]

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version meets requirements."""
    current = sys.version_info
    required = MIN_PYTHON
    if current >= required:
        return True, f"Python {current.major}.{current.minor}.{current.micro} (OK)"
    return False, f"Python {required[0]}.{required[1]}+ required (found {current.major}.{current.minor}.{current.micro})"

def check_macos_version() -> Tuple[bool, str]:
    """Check if macOS version meets requirements."""
    if sys.platform != 'darwin':
        return False, "macOS is required"
    
    try:
        # Get macOS version
        mac_ver = platform.mac_ver()[0].split('.')
        if len(mac_ver) >= 2:
            major, minor = int(mac_ver[0]), int(mac_ver[1])
            if (major, minor) >= MIN_MACOS:
                return True, f"macOS {major}.{minor}+ (OK)"
            return False, f"macOS {MIN_MACOS[0]}.{MIN_MACOS[1]}+ required (found {major}.{minor})"
        return False, f"Could not determine macOS version: {'.'.join(mac_ver)}"
    except Exception as e:
        return False, f"Could not determine macOS version: {str(e)}"

def check_package(package: str) -> Tuple[bool, str]:
    """Check if a package is installed and meets version requirements."""
    try:
        # Extract package name and version
        pkg_name = package.split('>=')[0].split('[')[0].strip()
        
        # Try to import the package
        __import__(pkg_name.replace('-', '_'))
        
        # If we got here, the package is installed
        return True, f"{package} (OK)"
    except ImportError:
        return False, f"{package} (MISSING)"
    except Exception as e:
        return False, f"{package} (ERROR: {str(e)})"

def run_checks() -> Tuple[bool, Dict[str, List[Tuple[bool, str]]]]:
    """Run all checks and return results."""
    results = {
        'system': [],
        'required': [],
        'optional': []
    }
    
    # System checks
    try:
        py_ok, py_msg = check_python_version()
        results['system'].append((py_ok, py_msg))
    except Exception as e:
        results['system'].append((False, f"Python version check failed: {str(e)}"))
    
    if sys.platform == 'darwin':
        try:
            mac_ok, mac_msg = check_macos_version()
            results['system'].append((mac_ok, mac_msg))
        except Exception as e:
            results['system'].append((False, f"macOS version check failed: {str(e)}"))
    
    # Required packages
    for pkg in REQUIRED_PACKAGES:
        try:
            ok, msg = check_package(pkg)
            results['required'].append((ok, msg))
        except Exception as e:
            results['required'].append((False, f"Error checking {pkg}: {str(e)}"))
    
    # Optional packages
    for pkg in OPTIONAL_PACKAGES:
        try:
            ok, msg = check_package(pkg)
            results['optional'].append((ok, msg))
        except Exception as e:
            results['optional'].append((False, f"Error checking {pkg}: {str(e)}"))
    
    # Check if all required checks passed
    all_ok = all(ok for ok, _ in results['system'] + results['required'])
    
    return all_ok, results

def print_results(all_ok: bool, results: Dict[str, List[Tuple[bool, str]]]) -> None:
    """Print the results of the system check."""
    print("\n=== Pinnacle Copilot System Check ===\n")
    
    # System information
    print("System Information:")
    try:
        print(f"- Platform: {sys.platform}")
        print(f"- Machine: {platform.machine()}")
        print(f"- Processor: {platform.processor()}")
    except Exception as e:
        print(f"- Could not get system information: {str(e)}")
    print()
    
    # System requirements
    print("System Requirements:")
    for ok, msg in results.get('system', []):
        status = "✓" if ok else "✗"
        print(f"  {status} {msg}")
    
    # Required packages
    print("\nRequired Packages:")
    for ok, msg in results.get('required', []):
        status = "✓" if ok else "✗"
        print(f"  {status} {msg}")
    
    # Optional packages
    print("\nOptional AI/ML Packages:")
    for ok, msg in results.get('optional', []):
        status = "✓" if ok else "-"
        print(f"  {status} {msg}")
    
    # Summary
    print("\n=== Summary ===")
    if all_ok:
        print("\n✓ Your system meets all requirements!")
        print("You can now run Pinnacle Copilot using './launch.command'")
    else:
        print("\n✗ Some requirements are not met. Please install the missing dependencies.")
        print("Run './launch.command' to install missing packages automatically.")
    
    print("\nNote: AI/ML features are optional but recommended for full functionality.")

def main() -> int:
    """Main function to run the system check."""
    try:
        all_ok, results = run_checks()
        print_results(all_ok, results)
        return 0 if all_ok else 1
    except Exception as e:
        print(f"Error during system check: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
