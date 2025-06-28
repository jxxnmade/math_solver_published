#!/usr/bin/env python3
"""
Math Solver Global Installer - Installs dependencies globally
Designed to work when installer.exe is placed alongside Python files
"""

import sys
import os
import subprocess
import platform
import threading
import time
import shutil
import ast
import re
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

# Try to import tkinter for GUI, fallback to CLI if not available
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

class GlobalMathSolverInstaller:
    """Global installer that installs dependencies to system Python"""
    
    def __init__(self):
        # Determine the directory where the installer is located
        self.installer_directory = self.get_installer_directory()
        
        # Set target directory to the same location as installer
        self.target_directory = self.installer_directory
        
        # Python files to look for (both cases)
        self.python_files = [
            'Home.py', 'home.py',
            'Polynomial.py', 'polynomial.py', 
            'Integration.py', 'integration.py'
        ]
        
        # Found Python files
        self.found_python_files = []
        
        # Installation status
        self.installation_log = []
        self.failed_packages = []
        self.success_count = 0
        self._log_lock = threading.Lock()
        
        # Dependency detection
        self.detected_dependencies = set()
        self.dependency_map = self._get_dependency_map()
        self.standard_libs = self._get_standard_libs()
        
    def get_installer_directory(self):
        """Get the directory where the installer is located"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return os.path.dirname(sys.executable)
        else:
            # Running as script
            return os.path.dirname(os.path.abspath(__file__))
    
    def _get_dependency_map(self):
        """Comprehensive dependency mapping"""
        return {
            # PyQt5 and related
            'PyQt5': 'PyQt5>=5.15.0',
            'PyQt5.QtWidgets': 'PyQt5>=5.15.0',
            'PyQt5.QtGui': 'PyQt5>=5.15.0',
            'PyQt5.QtCore': 'PyQt5>=5.15.0',
            'PyQt5.QtWebEngineWidgets': 'PyQtWebEngine>=5.15.0',
            'PyQt5.QtWebChannel': 'PyQtWebEngine>=5.15.0',
            
            # Scientific computing
            'sympy': 'sympy>=1.9.0',
            'matplotlib': 'matplotlib>=3.5.0',
            'numpy': 'numpy>=1.21.0',
            'scipy': 'scipy>=1.7.0',
            'pandas': 'pandas>=1.3.0',
            
            # Web and data
            'requests': 'requests>=2.25.0',
            'urllib3': 'urllib3>=1.26.0',
            
            # System packages that are built-in
            'json': None, 'os': None, 'sys': None, 'subprocess': None,
            'pathlib': None, 'glob': None, 'shutil': None, 'tempfile': None,
            'ast': None, 're': None, 'venv': None, 'threading': None,
            'concurrent': None, 'asyncio': None, 'datetime': None, 'time': None,
            'collections': None, 'itertools': None, 'functools': None,
            'operator': None, 'unittest': None, 'logging': None, 'warnings': None,
            'math': None, 'cmath': None, 'fractions': None, 'decimal': None,
            'statistics': None, 'random': None, 'platform': None,
            
            # Additional common packages
            'PIL': 'Pillow>=8.0.0',
            'cv2': 'opencv-python>=4.5.0',
            'sklearn': 'scikit-learn>=1.0.0',
            'torch': 'torch>=1.9.0',
            'tensorflow': 'tensorflow>=2.6.0',
            'flask': 'Flask>=2.0.0',
            'django': 'Django>=3.2.0',
            'fastapi': 'fastapi>=0.70.0',
            'sqlalchemy': 'SQLAlchemy>=1.4.0',
        }
    
    def _get_standard_libs(self):
        """Get comprehensive list of Python standard library modules"""
        if hasattr(sys, 'stdlib_module_names'):
            return set(sys.stdlib_module_names)
        
        # Fallback for older Python versions
        return {
            'os', 'sys', 'subprocess', 'ast', 'venv', 'pathlib', 'glob', 'shutil',
            'tempfile', 'math', 'cmath', 'fractions', 'decimal', 'statistics',
            'collections', 'itertools', 'functools', 'operator', 're', 'json',
            'datetime', 'time', 'random', 'threading', 'multiprocessing',
            'concurrent', 'asyncio', 'unittest', 'logging', 'warnings',
            'urllib', 'http', 'email', 'html', 'xml', 'csv', 'configparser',
            'argparse', 'getopt', 'io', 'string', 'textwrap', 'codecs',
            'unicodedata', 'stringprep', 'readline', 'rlcompleter',
            'pickle', 'copyreg', 'shelve', 'marshal', 'dbm', 'sqlite3',
            'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile',
            'hashlib', 'hmac', 'secrets', 'ssl', 'socket', 'select',
            'selectors', 'signal', 'mmap', 'ctypes', 'platform', 'tkinter'
        }
    
    def log(self, message):
        """Add message to installation log with thread safety"""
        with self._log_lock:
            if message not in self.installation_log:
                self.installation_log.append(message)
                print(message)
    
    def find_python_files(self):
        """Find Python files in the installer directory"""
        self.found_python_files = []
        
        self.log(f"📁 Scanning for Python files in: {self.installer_directory}")
        
        for filename in self.python_files:
            file_path = os.path.join(self.installer_directory, filename)
            if os.path.exists(file_path):
                self.found_python_files.append(file_path)
                self.log(f"   ✅ Found: {filename}")
        
        if not self.found_python_files:
            self.log("   ❌ No Python application files found!")
            self.log("   Expected files: Home.py, Polynomial.py, Integration.py")
            return False
        
        self.log(f"   📊 Total files found: {len(self.found_python_files)}")
        return True
    
    def extract_imports_from_file(self, filepath):
        """Extract all import statements from a Python file"""
        imports = set()
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        package_name = alias.name.split('.')[0]
                        imports.add(package_name)
                        imports.add(alias.name)
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        package_name = node.module.split('.')[0]
                        imports.add(package_name)
                        imports.add(node.module)
        
        except SyntaxError as e:
            self.log(f"⚠️  Syntax error in {os.path.basename(filepath)}: {e}")
        except Exception as e:
            self.log(f"⚠️  Error parsing {os.path.basename(filepath)}: {e}")
        
        return imports
    
    def detect_dependencies(self):
        """Detect all dependencies from found Python files"""
        if not self.found_python_files:
            return []
        
        self.log("🔍 Analyzing dependencies...")
        all_imports = set()
        
        for py_file in self.found_python_files:
            self.log(f"   Scanning: {os.path.basename(py_file)}")
            file_imports = self.extract_imports_from_file(py_file)
            all_imports.update(file_imports)
            
            # Log some found imports for this file
            external_imports = [imp for imp in file_imports if imp not in self.standard_libs][:5]
            if external_imports:
                self.log(f"      Found: {', '.join(external_imports)}...")
        
        # Filter and map to actual packages
        external_deps = set()
        unmapped_imports = set()
        
        for imp in all_imports:
            if imp not in self.standard_libs:
                if imp in self.dependency_map:
                    package = self.dependency_map[imp]
                    if package:  # Not None (built-in)
                        external_deps.add(package)
                else:
                    # Try base module name
                    base_import = imp.split('.')[0]
                    if base_import in self.dependency_map:
                        package = self.dependency_map[base_import]
                        if package:
                            external_deps.add(package)
                    else:
                        unmapped_imports.add(imp)
        
        # Add essential packages that are commonly needed
        essential_packages = [
            'setuptools>=60.0.0',
            'wheel>=0.37.0',
        ]
        external_deps.update(essential_packages)
        
        final_deps = sorted(external_deps)
        
        self.log(f"📦 Dependencies to install: {len(final_deps)}")
        for dep in final_deps:
            self.log(f"   • {dep}")
        
        if unmapped_imports:
            self.log(f"⚠️  Unmapped imports (may need manual installation): {len(unmapped_imports)}")
            for imp in sorted(unmapped_imports)[:5]:  # Show first 5
                self.log(f"   • {imp}")
            if len(unmapped_imports) > 5:
                self.log(f"   ... and {len(unmapped_imports) - 5} more")
        
        self.detected_dependencies = final_deps
        return final_deps
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        version = sys.version_info
        if version < (3, 7):
            self.log("❌ ERROR: Python 3.7 or higher is required!")
            self.log(f"   Current version: {sys.version}")
            return False
        
        self.log(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    
    def test_internet_connection(self):
        """Test internet connection"""
        self.log("🌐 Testing internet connection...")
        try:
            urlopen('https://pypi.org', timeout=10)
            self.log("✅ Internet connection verified")
            return True
        except URLError:
            self.log("❌ No internet connection detected!")
            self.log("   Internet access is required to download packages.")
            return False
    
    def check_pip_availability(self):
        """Check if pip is available and working"""
        self.log("🔧 Checking pip availability...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                pip_version = result.stdout.strip()
                self.log(f"✅ Pip is available: {pip_version}")
                return True
            else:
                self.log(f"❌ Pip check failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking pip: {e}")
            return False
    
    def upgrade_pip(self):
        """Upgrade pip to latest version"""
        self.log("⬆️  Upgrading pip...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("✅ Pip upgraded successfully")
                return True
            else:
                self.log(f"⚠️  Pip upgrade warning: {result.stderr}")
                return True  # Continue anyway
                
        except Exception as e:
            self.log(f"⚠️  Pip upgrade failed: {e}")
            return True  # Continue anyway
    
    def check_package_installed(self, package_name):
        """Check if a package is already installed"""
        try:
            # Extract package name without version specifier
            clean_name = package_name.split('>=')[0].split('==')[0].split('[')[0]
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", clean_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def install_package(self, package):
        """Install a single package globally"""
        try:
            # Check if already installed
            if self.check_package_installed(package):
                self.log(f"   ✅ {package} already installed (skipping)")
                self.success_count += 1
                return True
            
            self.log(f"   Installing {package}...")
            
            # Use --user flag to avoid permission issues, but prefer global install
            cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir", package]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                self.log(f"   ✅ {package} installed successfully")
                self.success_count += 1
                return True
            else:
                # Try with --user flag if global install fails
                self.log(f"   Global install failed, trying user install...")
                cmd_user = [sys.executable, "-m", "pip", "install", "--user", "--no-cache-dir", package]
                
                result_user = subprocess.run(
                    cmd_user,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result_user.returncode == 0:
                    self.log(f"   ✅ {package} installed successfully (user install)")
                    self.success_count += 1
                    return True
                else:
                    self.log(f"   ❌ Failed to install {package}")
                    error_msg = result.stderr[:200] if result.stderr else "Unknown error"
                    self.log(f"      Error: {error_msg}...")
                    self.failed_packages.append(package)
                    return False
                
        except subprocess.TimeoutExpired:
            self.log(f"   ⏰ Timeout installing {package}")
            self.failed_packages.append(package)
            return False
        except Exception as e:
            self.log(f"   ❌ Error installing {package}: {e}")
            self.failed_packages.append(package)
            return False
    
    def install_all_packages(self):
        """Install all detected packages globally"""
        if not self.detected_dependencies:
            self.log("⚠️  No dependencies detected to install")
            return True
        
        self.log(f"📥 Installing {len(self.detected_dependencies)} packages globally...")
        self.log("   This may take several minutes...")
        
        # Upgrade pip first
        self.upgrade_pip()
        
        # Install packages one by one
        for i, package in enumerate(self.detected_dependencies, 1):
            self.log(f"\n   [{i}/{len(self.detected_dependencies)}] {package}")
            self.install_package(package)
        
        # Print summary
        self.log(f"\n📊 Installation Summary:")
        self.log(f"   ✅ Successful: {self.success_count}/{len(self.detected_dependencies)}")
        
        if self.failed_packages:
            self.log(f"   ❌ Failed: {len(self.failed_packages)}")
            self.log("   Failed packages:")
            for pkg in self.failed_packages:
                self.log(f"     • {pkg}")
        
        return len(self.failed_packages) == 0
    
    def create_requirements_file(self):
        """Create requirements.txt file based on detected dependencies"""
        self.log("📝 Creating requirements.txt...")
        
        try:
            requirements_path = os.path.join(self.target_directory, "requirements.txt")
            with open(requirements_path, 'w') as f:
                f.write("# Math Solver Requirements\n")
                f.write("# Generated by Math Solver Installer\n\n")
                for dep in sorted(self.detected_dependencies):
                    f.write(f"{dep}\n")
            
            self.log("✅ Requirements saved to requirements.txt")
            return True
                
        except Exception as e:
            self.log(f"❌ Error generating requirements: {e}")
            return False
    
    def create_launcher_scripts(self):
        """Create launcher scripts for found Python files"""
        self.log("🚀 Creating launcher scripts...")
        
        if not self.found_python_files:
            self.log("⚠️  No Python files found to create launchers for")
            return False
        
        scripts_created = []
        
        for py_file_path in self.found_python_files:
            filename = os.path.basename(py_file_path)
            script_name = os.path.splitext(filename)[0].lower()
            
            # Skip duplicate names (home.py and Home.py)
            launcher_path = os.path.join(self.target_directory, f"run_{script_name}.bat")
            if os.path.exists(launcher_path):
                continue
            
            # Create launcher script that uses system Python (where packages are now installed)
            if platform.system() == "Windows":
                launcher_content = f'''@echo off
title Math Solver - {filename}
echo Starting {filename}...
cd /d "{self.target_directory}"
python "{py_file_path}" %*
if errorlevel 1 (
    echo.
    echo Error occurred while running {filename}
    echo Press any key to close...
    pause >nul
) else (
    echo.
    echo {filename} closed normally.
)
'''
            else:
                launcher_content = f'''#!/bin/bash
echo "Starting {filename}..."
cd "{self.target_directory}"
python3 "{py_file_path}" "$@"
if [ $? -ne 0 ]; then
    echo ""
    echo "Error occurred while running {filename}"
    read -p "Press Enter to continue..."
fi
'''
            
            try:
                with open(launcher_path, 'w') as f:
                    f.write(launcher_content)
                
                # Make executable on Unix systems
                if platform.system() != "Windows":
                    os.chmod(launcher_path, 0o755)
                
                scripts_created.append(os.path.basename(launcher_path))
                self.log(f"   ✅ Created: {os.path.basename(launcher_path)}")
                
            except Exception as e:
                self.log(f"   ❌ Failed to create launcher for {filename}: {e}")
        
        if scripts_created:
            self.log(f"✅ Created {len(scripts_created)} launcher scripts")
            return True
        else:
            self.log("❌ No launcher scripts created")
            return False
    
    def create_direct_run_script(self):
        """Create a script to run applications directly"""
        self.log("📋 Creating direct run script...")
        
        if platform.system() == "Windows":
            run_script = os.path.join(self.target_directory, "run_math_solver.bat")
            content = f'''@echo off
echo.
echo ===============================================
echo   Math Solver Application Launcher
echo ===============================================
echo.
echo Available applications:
'''
            
            # Add found Python files to menu
            for i, py_file in enumerate(self.found_python_files, 1):
                filename = os.path.basename(py_file)
                if not filename.lower().startswith('home'):  # Skip duplicate home files
                    continue
                content += f'echo   {i}. {filename}\n'
                break  # Just show Home.py as main entry point
            
            content += '''echo.
echo Starting main application...
cd /d "%~dp0"
python "Home.py" %*
if errorlevel 1 (
    echo.
    echo Error: Could not start application
    echo Make sure Python is installed and dependencies are available
    echo.
    pause
)
'''
        else:
            run_script = os.path.join(self.target_directory, "run_math_solver.sh")
            content = f'''#!/bin/bash
echo ""
echo "==============================================="
echo "   Math Solver Application Launcher"
echo "==============================================="
echo ""
echo "Starting main application..."
cd "$(dirname "$0")"
python3 "Home.py" "$@"
if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Could not start application"
    echo "Make sure Python is installed and dependencies are available"
    echo ""
    read -p "Press Enter to continue..."
fi
'''
        
        try:
            with open(run_script, 'w') as f:
                f.write(content)
            
            if platform.system() != "Windows":
                os.chmod(run_script, 0o755)
            
            self.log(f"✅ Created: {os.path.basename(run_script)}")
            return True
        except Exception as e:
            self.log(f"❌ Failed to create run script: {e}")
            return False
    
    def test_installation(self):
        """Test the installation by importing key packages"""
        self.log("🧪 Testing installation...")
        
        if not self.detected_dependencies:
            self.log("   No dependencies to test")
            return True
        
        # Extract package names from versioned requirements
        test_packages = []
        for dep in self.detected_dependencies:
            package_name = dep.split('>=')[0].split('==')[0].split('[')[0]
            if package_name not in ['setuptools', 'wheel']:
                test_packages.append(package_name)
        
        test_packages = test_packages[:5]  # Test first 5 packages
        
        for package in test_packages:
            try:
                result = subprocess.run(
                    [sys.executable, "-c", f"import {package}; print(f'{package}: OK')"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self.log(f"   ✅ {package}: OK")
                else:
                    self.log(f"   ❌ {package}: Failed to import")
                    
            except Exception as e:
                self.log(f"   ❌ {package}: Error testing - {e}")
        
        self.log("✅ Installation test completed")
        return True
    
    def run_installation(self):
        """Run the complete installation process"""
        self.log("=" * 70)
        self.log("  MATH SOLVER GLOBAL INSTALLER")
        self.log("=" * 70)
        self.log(f"Python Version: {sys.version}")
        self.log(f"Platform: {platform.system()} {platform.release()}")
        self.log(f"Installer Location: {self.installer_directory}")
        self.log(f"Target Directory: {self.target_directory}")
        self.log("=" * 70)
        
        # Step 1: Find Python files
        if not self.find_python_files():
            return False
        
        # Step 2: Detect dependencies
        if not self.detect_dependencies():
            self.log("⚠️  No dependencies detected, but continuing...")
        
        # Step 3: Check Python version
        if not self.check_python_version():
            return False
        
        # Step 4: Check pip availability
        if not self.check_pip_availability():
            return False
        
        # Step 5: Test internet connection
        if not self.test_internet_connection():
            return False
        
        # Step 6: Install packages globally
        success = self.install_all_packages()
        if not success:
            self.log("⚠️  Some packages failed to install, but continuing...")
        
        # Step 7: Create additional files
        self.create_requirements_file()
        self.create_launcher_scripts()
        self.create_direct_run_script()
        
        # Step 8: Test installation
        self.test_installation()
        
        # Step 9: Final message
        self.print_completion_message()
        
        return len(self.failed_packages) == 0
    
    def print_completion_message(self):
        """Print installation completion message"""
        self.log("\n" + "=" * 70)
        if len(self.failed_packages) == 0:
            self.log("  🎉 INSTALLATION COMPLETED SUCCESSFULLY! 🎉")
        else:
            self.log("  ⚠️  INSTALLATION COMPLETED WITH WARNINGS")
        self.log("=" * 70)
        
        self.log("\n📁 Files created:")
        self.log("   • requirements.txt")
        self.log("   • Launcher scripts (run_*.bat)")
        self.log("   • Main launcher (run_math_solver.bat)")
        
        self.log("\n🚀 How to use:")
        self.log("   1. Double-click 'run_math_solver.bat' to start the main application")
        self.log("   2. Or double-click any 'run_*.bat' file to start a specific application")
        self.log("   3. Or run 'python Home.py' directly from command line")
        
        if self.found_python_files:
            self.log("\n📱 Available applications:")
            seen_names = set()
            for py_file in self.found_python_files:
                filename = os.path.basename(py_file)
                script_name = os.path.splitext(filename)[0].lower()
                if script_name not in seen_names:
                    seen_names.add(script_name)
                    self.log(f"   • {filename} → run_{script_name}.bat")
        
        if self.failed_packages:
            self.log(f"\n⚠️  Note: {len(self.failed_packages)} packages failed to install.")
            self.log("   Try running the installer as Administrator if you encounter issues.")
            self.log("   You can also install failed packages manually using:")
            self.log("   pip install <package_name>")
        
        self.log("\n💡 Tips:")
        self.log("   • Packages are installed globally to your Python installation")
        self.log("   • No virtual environment is needed")
        self.log("   • You can run the Python files directly after installation")
        
        self.log("\n" + "=" * 70)

class GlobalInstallerGUI:
    """Enhanced GUI for the global installer"""
    
    def __init__(self):
        self.installer = GlobalMathSolverInstaller()
        self.root = tk.Tk()
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        self.root.title("Math Solver Global Installer")
        self.root.geometry("750x650")
        self.root.resizable(True, True)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Math Solver Global Installer", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="Installs dependencies globally to your Python installation")
        subtitle_label.pack(pady=(0, 20))
        
        # Directory info
        dir_frame = ttk.LabelFrame(main_frame, text="Installation Information:", padding="10")
        dir_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Show installer location
        ttk.Label(dir_frame, text=f"Installer Location: {self.installer.installer_directory}", 
                 font=("Arial", 9)).pack(anchor=tk.W)
        
        # Show found files
        self.installer.find_python_files()
        if self.installer.found_python_files:
            ttk.Label(dir_frame, text="Found Python Files:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(10,0))
            seen_files = set()
            for py_file in self.installer.found_python_files:
                filename = os.path.basename(py_file).lower()
                if filename not in seen_files:
                    seen_files.add(filename)
                    display_name = os.path.basename(py_file)
                    ttk.Label(dir_frame, text=f"  • {display_name}", font=("Arial", 9), foreground="green").pack(anchor=tk.W)
        else:
            ttk.Label(dir_frame, text="⚠️ No Python application files found!", 
                     font=("Arial", 9), foreground="red").pack(anchor=tk.W, pady=(10,0))
            ttk.Label(dir_frame, text="Expected: Home.py, Polynomial.py, Integration.py", 
                     font=("Arial", 9)).pack(anchor=tk.W)
        
        # Info section
        info_frame = ttk.LabelFrame(main_frame, text="What will be installed:", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_text = """• Dependencies installed globally to your Python installation
• PyQt5, matplotlib, numpy, sympy, and other required packages
• Launcher scripts (.bat files) for easy execution  
• Main application launcher script
• Requirements file for reference

⚠️ No virtual environment - packages install to system Python
✅ Avoids virtual environment compatibility issues
✅ Simpler deployment and execution"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, foreground="navy").pack(anchor=tk.W)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Installation Progress:", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready to install")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(progress_frame, height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Install button
        install_enabled = len(self.installer.found_python_files) > 0
        self.install_btn = ttk.Button(button_frame, text="Start Installation", 
                                     command=self.start_installation,
                                     state='normal' if install_enabled else 'disabled')
        self.install_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Close button
        self.close_btn = ttk.Button(button_frame, text="Close", command=self.root.quit)
        self.close_btn.pack(side=tk.LEFT)
        
        # Center window
        self.center_window()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def log_message(self, message):
        """Add message to log text area"""
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_installation(self):
        """Start the installation process"""
        if not self.installer.found_python_files:
            messagebox.showerror("Error", "No Python application files found in the same directory as the installer!")
            return
        
        # Disable install button and start progress
        self.install_btn.configure(state='disabled')
        self.progress_bar.start()
        self.log_text.delete(1.0, tk.END)
        
        # Override installer log method to update GUI
        original_log = self.installer.log
        def gui_log(message):
            original_log(message)
            self.root.after_idle(lambda: self.log_message(message))
            if any(keyword in message for keyword in ["Installing", "Checking", "Testing"]):
                self.root.after_idle(lambda: self.status_var.set(message[:50] + "..."))
        
        self.installer.log = gui_log
        
        # Run installation in thread
        def run_install():
            try:
                success = self.installer.run_installation()
                self.root.after_idle(lambda: self.installation_finished(success))
            except Exception as e:
                self.root.after_idle(lambda: self.installation_error(str(e)))
        
        install_thread = threading.Thread(target=run_install)
        install_thread.daemon = True
        install_thread.start()
    
    def installation_finished(self, success):
        """Called when installation completes"""
        self.progress_bar.stop()
        self.install_btn.configure(state='normal')
        
        if success:
            self.status_var.set("Installation completed successfully!")
            messagebox.showinfo("Success", 
                "Installation completed successfully!\n\n" +
                "Dependencies have been installed globally to your Python installation.\n\n" +
                "You can now:\n" +
                "• Double-click 'run_math_solver.bat' to start the main application\n" +
                "• Use any of the individual launcher scripts\n" +
                "• Run 'python Home.py' directly from command line")
        else:
            self.status_var.set("Installation completed with warnings")
            messagebox.showwarning("Completed with Warnings", 
                "Installation completed but some packages failed.\n\n" +
                "Check the log for details. Try running as Administrator if issues persist.\n\n" +
                "You can also install failed packages manually using:\n" +
                "pip install <package_name>")
    
    def installation_error(self, error):
        """Called when installation encounters an error"""
        self.progress_bar.stop()
        self.install_btn.configure(state='normal')
        self.status_var.set("Installation failed")
        messagebox.showerror("Error", f"Installation failed:\n\n{error}")
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        # Always use the directory where the installer is located
        installer = GlobalMathSolverInstaller()
        
        # Check for command line arguments
        if len(sys.argv) > 1 and sys.argv[1].lower() in ['--cli', '-c', '--console']:
            # Force CLI mode
            success = installer.run_installation()
            
            if platform.system() == "Windows":
                input("\nPress Enter to exit...")
            
            sys.exit(0 if success else 1)
        
        elif HAS_GUI:
            # Run GUI version
            app = GlobalInstallerGUI()
            app.run()
        else:
            # Fallback to CLI if GUI not available
            print("GUI not available, running in console mode...")
            success = installer.run_installation()
            
            if platform.system() == "Windows":
                input("\nPress Enter to exit...")
            
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if platform.system() == "Windows":
            input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()