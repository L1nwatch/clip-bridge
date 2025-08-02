#!/usr/bin/env python3
"""
Test script to verify VS Code virtual environment configuration.
"""

import sys
import os
from pathlib import Path

def main():
    print("🔍 Virtual Environment Test")
    print("=" * 40)
    
    # Check if we're in a virtual environment
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"✅ Virtual environment detected: {venv_path}")
    else:
        print("❌ No virtual environment detected")
    
    # Check Python executable path
    python_path = sys.executable
    print(f"🐍 Python executable: {python_path}")
    
    # Check if Python is from .venv
    workspace_folder = Path(__file__).parent.parent
    venv_python = workspace_folder / ".venv" / "bin" / "python"
    
    if Path(python_path).resolve() == venv_python.resolve():
        print("✅ Using virtual environment Python")
    else:
        print("❌ Not using virtual environment Python")
        print(f"   Expected: {venv_python}")
        print(f"   Actual: {python_path}")
    
    # Check Python version
    print(f"📦 Python version: {sys.version}")
    
    # Check installed packages
    try:
        import pkg_resources
        installed_packages = [d.project_name for d in pkg_resources.working_set]
        print(f"📚 Installed packages: {len(installed_packages)} found")
        
        # Check for key packages
        key_packages = ['flask', 'loguru', 'pillow', 'pyperclip']
        for package in key_packages:
            if package in installed_packages:
                print(f"   ✅ {package}")
            else:
                print(f"   ❌ {package} (missing)")
                
    except ImportError:
        print("⚠️ Cannot check installed packages (pkg_resources not available)")
    
    print("=" * 40)
    print("🎯 Configuration test complete!")

if __name__ == "__main__":
    main()
