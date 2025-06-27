import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtGui import QRegion
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QTimer

from PyQt5.QtWidgets import QStackedLayout, QLabel, QProgressBar, QTextEdit
import subprocess
import os
import ast
import venv
import sys
from pathlib import Path
import glob
import json
import threading
from concurrent.futures import ThreadPoolExecutor

class DependencyInstaller:
    """Enhanced dependency detection and virtual environment setup"""
    
    def __init__(self):
        self.standard_libs = self._get_standard_libs()
        self.dependency_map = {
            # PyQt5 and related
            'PyQt5': 'PyQt5',
            'PyQt5.QtWidgets': 'PyQt5',
            'PyQt5.QtGui': 'PyQt5',
            'PyQt5.QtCore': 'PyQt5',
            'PyQt5.QtWebEngineWidgets': 'PyQtWebEngine',
            'PyQt5.QtWebChannel': 'PyQtWebEngine',
            
            # Scientific computing
            'sympy': 'sympy',
            'matplotlib': 'matplotlib',
            'numpy': 'numpy',
            'scipy': 'scipy',
            'pandas': 'pandas',
            
            # Web and data
            'requests': 'requests',
            'urllib3': 'urllib3',
            'json': None,  # Built-in
            
            # Math and calculations
            'fractions': None,  # Built-in
            'math': None,       # Built-in
            'cmath': None,      # Built-in
            'decimal': None,    # Built-in
            'statistics': None, # Built-in
            
            # System and file operations
            'os': None,         # Built-in
            'sys': None,        # Built-in
            'subprocess': None, # Built-in
            'pathlib': None,    # Built-in
            'glob': None,       # Built-in
            'shutil': None,     # Built-in
            'tempfile': None,   # Built-in
            
            # Parsing and AST
            'ast': None,        # Built-in
            're': None,         # Built-in
            
            # Virtual environments
            'venv': None,       # Built-in
            
            # Threading and concurrency
            'threading': None,  # Built-in
            'concurrent': None, # Built-in (concurrent.futures)
            'asyncio': None,    # Built-in
            
            # Date and time
            'datetime': None,   # Built-in
            'time': None,       # Built-in
            
            # Collections and utilities
            'collections': None, # Built-in
            'itertools': None,   # Built-in
            'functools': None,   # Built-in
            'operator': None,    # Built-in
            
            # Testing and development
            'unittest': None,   # Built-in
            'logging': None,    # Built-in
            'warnings': None,   # Built-in
            
            # Additional common packages
            'pillow': 'Pillow',
            'PIL': 'Pillow',
            'cv2': 'opencv-python',
            'sklearn': 'scikit-learn',
            'torch': 'torch',
            'tensorflow': 'tensorflow',
            'flask': 'Flask',
            'django': 'Django',
            'fastapi': 'fastapi',
            'sqlalchemy': 'SQLAlchemy',
        }
        
        # Additional packages that might be needed for PyQt5 web functionality
        self.recommended_packages = [
            'PyQtWebEngine',  # For QWebEngineView
            'setuptools',     # Often needed for package installation
            'wheel',          # For better package installation
            'pip',            # Ensure latest pip
        ]
    
    def _get_standard_libs(self):
        """Get comprehensive list of Python standard library modules"""
        # Use sys.stdlib_module_names if available (Python 3.10+)
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
            'selectors', 'signal', 'mmap', 'ctypes', 'platform',
        }
    
    def extract_imports_from_file(self, filepath):
        """Extract all import statements from a Python file with enhanced parsing"""
        imports = set()
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get the top-level package name
                        package_name = alias.name.split('.')[0]
                        imports.add(package_name)
                        # Also add the full module path for better mapping
                        imports.add(alias.name)
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Get the top-level package name
                        package_name = node.module.split('.')[0]
                        imports.add(package_name)
                        # Also add the full module path
                        imports.add(node.module)
        
        except SyntaxError as e:
            print(f"Syntax error in {filepath}: {e}")
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
        
        return imports
    
    def scan_directory_for_python_files(self, directory):
        """Scan directory for all Python files"""
        python_files = []
        directory = Path(directory)
        
        # Find all .py files in the directory
        for py_file in directory.glob("*.py"):
            if py_file.name != '__pycache__':
                python_files.append(str(py_file))
        
        return python_files
    
    def get_all_dependencies(self, directory=None, script_paths=None):
        """Get all unique dependencies from Python files in directory or specific paths"""
        all_imports = set()
        
        if directory:
            script_paths = self.scan_directory_for_python_files(directory)
        
        if not script_paths:
            script_paths = []
        
        print(f"Scanning {len(script_paths)} Python files for dependencies...")
        
        for script_path in script_paths:
            if os.path.exists(script_path):
                print(f"  Analyzing: {os.path.basename(script_path)}")
                file_imports = self.extract_imports_from_file(script_path)
                all_imports.update(file_imports)
                print(f"    Found imports: {sorted(file_imports)}")
        
        print(f"All unique imports found: {sorted(all_imports)}")
        
        # Filter out standard library modules and map to packages
        external_deps = set()
        unmapped_imports = set()
        
        for imp in all_imports:
            if imp not in self.standard_libs:
                if imp in self.dependency_map:
                    package = self.dependency_map[imp]
                    if package:  # Not None (built-in)
                        external_deps.add(package)
                else:
                    # Try to map common variations
                    base_import = imp.split('.')[0]
                    if base_import in self.dependency_map:
                        package = self.dependency_map[base_import]
                        if package:
                            external_deps.add(package)
                    else:
                        unmapped_imports.add(imp)
        
        if unmapped_imports:
            print(f"Warning: Unmapped imports found: {sorted(unmapped_imports)}")
            print("These may need to be installed manually or added to the dependency map.")
        
        # Add recommended packages
        external_deps.update(self.recommended_packages)
        
        final_deps = sorted(external_deps)
        print(f"Final external dependencies: {final_deps}")
        
        return final_deps, sorted(unmapped_imports)
    
    def create_virtual_environment(self, venv_path, progress_callback=None):
        """Create a virtual environment with enhanced error handling"""
        try:
            if progress_callback:
                progress_callback(f"Creating virtual environment at: {venv_path}")
            
            # Remove existing venv if it exists
            if os.path.exists(venv_path):
                if progress_callback:
                    progress_callback("Removing existing virtual environment...")
                import shutil
                shutil.rmtree(venv_path)
            
            # Create new virtual environment
            venv.create(venv_path, with_pip=True, clear=True)
            
            if progress_callback:
                progress_callback("Virtual environment created successfully!")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error creating virtual environment: {e}")
            return False
    
    def get_venv_paths(self, venv_path):
        """Get paths for virtual environment executables"""
        if sys.platform == "win32":
            return {
                'python': os.path.join(venv_path, "Scripts", "python.exe"),
                'pip': os.path.join(venv_path, "Scripts", "pip.exe"),
                'activate': os.path.join(venv_path, "Scripts", "activate.bat")
            }
        else:
            return {
                'python': os.path.join(venv_path, "bin", "python"),
                'pip': os.path.join(venv_path, "bin", "pip"),
                'activate': os.path.join(venv_path, "bin", "activate")
            }
    
    def upgrade_pip(self, venv_path, progress_callback=None):
        """Upgrade pip in the virtual environment"""
        try:
            paths = self.get_venv_paths(venv_path)
            
            if progress_callback:
                progress_callback("Upgrading pip...")
            
            result = subprocess.run(
                [paths['python'], "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback("Pip upgraded successfully!")
                return True
            else:
                if progress_callback:
                    progress_callback(f"Pip upgrade warning: {result.stderr}")
                return True  # Continue even if pip upgrade fails
                
        except Exception as e:
            if progress_callback:
                progress_callback(f"Pip upgrade failed: {e}")
            return True  # Continue even if pip upgrade fails
    
    def install_dependencies(self, venv_path, dependencies, progress_callback=None):
        """Install dependencies in the virtual environment with enhanced error handling"""
        paths = self.get_venv_paths(venv_path)
        
        if not os.path.exists(paths['pip']):
            if progress_callback:
                progress_callback(f"Error: pip not found at {paths['pip']}")
            return False
        
        # First upgrade pip
        self.upgrade_pip(venv_path, progress_callback)
        
        success_count = 0
        failed_packages = []
        
        for dep in dependencies:
            try:
                if progress_callback:
                    progress_callback(f"Installing {dep}...")
                
                # Use --no-cache-dir to avoid cache issues
                result = subprocess.run(
                    [paths['pip'], "install", "--no-cache-dir", dep],
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout per package
                )
                
                if result.returncode == 0:
                    if progress_callback:
                        progress_callback(f"✅ Successfully installed {dep}")
                    success_count += 1
                else:
                    if progress_callback:
                        progress_callback(f"❌ Failed to install {dep}: {result.stderr}")
                    failed_packages.append(dep)
            
            except subprocess.TimeoutExpired:
                if progress_callback:
                    progress_callback(f"⏰ Timeout installing {dep}")
                failed_packages.append(dep)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"❌ Error installing {dep}: {e}")
                failed_packages.append(dep)
        
        if progress_callback:
            progress_callback(f"\n📊 Installation Summary:")
            progress_callback(f"   Successful: {success_count}/{len(dependencies)}")
            if failed_packages:
                progress_callback(f"   Failed: {', '.join(failed_packages)}")
        
        return len(failed_packages) == 0
    
    def create_requirements_file(self, venv_path, output_dir, progress_callback=None):
        """Create a requirements.txt file from the virtual environment"""
        try:
            paths = self.get_venv_paths(venv_path)
            
            if progress_callback:
                progress_callback("Generating requirements.txt...")
            
            result = subprocess.run(
                [paths['pip'], "freeze"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                requirements_path = os.path.join(output_dir, "requirements.txt")
                with open(requirements_path, 'w') as f:
                    f.write(result.stdout)
                
                if progress_callback:
                    progress_callback(f"Requirements saved to: {requirements_path}")
                
                return True
            else:
                if progress_callback:
                    progress_callback(f"Failed to generate requirements: {result.stderr}")
                return False
                
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error generating requirements: {e}")
            return False
    
    def create_launcher_script(self, venv_path, script_name, target_script, output_dir):
        """Create a launcher script that uses the virtual environment"""
        paths = self.get_venv_paths(venv_path)
        launcher_path = os.path.join(output_dir, f"run_{script_name}")
        
        if sys.platform == "win32":
            launcher_path += ".bat"
            launcher_content = f"""@echo off
cd /d "{output_dir}"
"{paths['python']}" "{target_script}" %*
"""
        else:
            launcher_path += ".sh"
            launcher_content = f"""#!/bin/bash
cd "{output_dir}"
"{paths['python']}" "{target_script}" "$@"
"""
        
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        # Make executable on Unix systems
        if sys.platform != "win32":
            os.chmod(launcher_path, 0o755)
        
        return launcher_path

class InstallationWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Installing Dependencies")
        self.setFixedSize(600, 500)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.Window | Qt.MSWindowsFixedSizeDialogHint)
        
        # Create circular mask
        region = QRegion(QRect(0, 0, 600, 500), QRegion.Ellipse)
        self.setMask(region)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #252525;
                color: white;
                font-family: Arial;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 10px;
                text-align: center;
                background-color: #353535;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 8px;
            }
            QTextEdit {
                background-color: #353535;
                border: 1px solid #555;
                border-radius: 8px;
                color: white;
                font-size: 11px;
                font-family: 'Courier New', monospace;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
        """)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Dependency Installation & Virtual Environment Setup")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(250)
        layout.addWidget(self.status_text)
        
        # Button layout
        button_layout = QVBoxLayout()
        
        # Close button (initially disabled)
        self.close_button = QPushButton("Close")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        # Open folder button
        self.open_folder_button = QPushButton("Open Installation Folder")
        self.open_folder_button.setEnabled(False)
        self.open_folder_button.clicked.connect(self.open_folder)
        button_layout.addWidget(self.open_folder_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.installation_folder = None
    
    def update_status(self, message):
        """Update the status text"""
        self.status_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        # Process events to update UI
        QApplication.processEvents()
    
    def set_progress_range(self, min_val, max_val):
        """Set progress bar range"""
        self.progress_bar.setRange(min_val, max_val)
    
    def set_progress_value(self, value):
        """Set progress bar value"""
        self.progress_bar.setValue(value)
    
    def installation_complete(self, success, folder_path=None):
        """Called when installation is complete"""
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.close_button.setEnabled(True)
        
        if folder_path:
            self.installation_folder = folder_path
            self.open_folder_button.setEnabled(True)
        
        if success:
            self.update_status("\n🎉 Installation completed successfully!")
            self.update_status("Virtual environment is ready for all Math Solver applications.")
            if folder_path:
                self.update_status(f"Installation folder: {folder_path}")
        else:
            self.update_status("\n⚠️ Installation completed with some errors.")
            self.update_status("Some dependencies may need manual installation.")
    
    def open_folder(self):
        """Open the installation folder"""
        if self.installation_folder and os.path.exists(self.installation_folder):
            if sys.platform == "win32":
                os.startfile(self.installation_folder)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", self.installation_folder])
            else:  # Linux
                subprocess.run(["xdg-open", self.installation_folder])

class AnimatedStackedWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Math Solver")
        self.setFixedSize(500, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #232323;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                font-family: Arial;
                font-weight: bold;
                font-size: 24px;
                border: none;
                margin: 20px;
            }
            QPushButton:hover {
                color: #bbbbbb;
            }
            QLabel {
                color: white;
                font-family: Arial;
                font-weight: bold;
                font-size: 32px;
                margin: 20px;
            }
        """)
        self.setWindowFlags(Qt.Window | Qt.MSWindowsFixedSizeDialogHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        region = QRegion(QRect(0, 0, 500, 500), QRegion.Ellipse)
        self.setMask(region)

        self.stacked_layout = QStackedLayout()
        self.setLayout(self.stacked_layout)

        # Get script directory
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.venv_path = os.path.join(self.script_dir, "math_solver_venv")

        # Home Page
        self.home_widget = QWidget()
        self.home_layout = QVBoxLayout()
        self.home_layout.setAlignment(Qt.AlignCenter)
        self.home_widget.setLayout(self.home_layout)

        self.home_buttons = []
        self.home_animations = []

        btn_zeroes = QPushButton("Find zeroes")
        btn_integration = QPushButton("Integration")
        btn_credits = QPushButton("Credits")
        btn_install_deps = QPushButton("Setup Environment")
        btn_install_deps.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-family: Arial;
                font-weight: bold;
                font-size: 18px;
                border: none;
                border-radius: 8px;
                margin: 10px;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.home_layout.addWidget(btn_zeroes)
        self.home_layout.addWidget(btn_integration)
        self.home_layout.addWidget(btn_credits)
        self.home_layout.addWidget(btn_install_deps)
        
        self.home_buttons.append(btn_zeroes)
        self.home_buttons.append(btn_integration)
        self.home_buttons.append(btn_credits)
        self.home_buttons.append(btn_install_deps)

        for btn in self.home_buttons:
            opacity_effect = QGraphicsOpacityEffect(btn)
            btn.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(0)

        # Credits Page
        self.credits_widget = QWidget()
        self.credits_layout = QVBoxLayout()
        self.credits_layout.setAlignment(Qt.AlignCenter)
        self.credits_layout.setSpacing(2)
        self.credits_widget.setLayout(self.credits_layout)

        self.credits_buttons = []
        self.credits_animations = []

        label_title = QLabel("Credits")
        label_title.setAlignment(Qt.AlignCenter)
        label_title.setStyleSheet("QLabel { font-size: 36px; margin-bottom: 2px; }")
        self.credits_layout.addWidget(label_title)
        self.credits_buttons.append(label_title)

        label_prog = QLabel("Programming by Jaxson Morrow")
        label_prog.setAlignment(Qt.AlignCenter)
        label_prog.setStyleSheet("QLabel { font-size: 24px; margin-bottom: 2px; }")
        self.credits_layout.addWidget(label_prog)
        self.credits_buttons.append(label_prog)

        label_instagram = QLabel("@jxxnmade on Instagram,")
        label_instagram.setAlignment(Qt.AlignCenter)
        label_instagram.setStyleSheet("QLabel { font-size: 20px; margin-bottom: 2px; }")
        self.credits_layout.addWidget(label_instagram)
        self.credits_buttons.append(label_instagram)

        label_socials = QLabel("Twitter, Tiktok, and Github")
        label_socials.setAlignment(Qt.AlignCenter)
        label_socials.setStyleSheet("QLabel { font-size: 20px; margin-bottom: 2px; }")
        self.credits_layout.addWidget(label_socials)
        self.credits_buttons.append(label_socials)

        self.btn_back = QPushButton("Back")
        self.credits_layout.addWidget(self.btn_back)
        self.credits_buttons.append(self.btn_back)

        for btn in self.credits_buttons:
            opacity_effect = QGraphicsOpacityEffect(btn)
            btn.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(0)

        self.stacked_layout.addWidget(self.home_widget)
        self.stacked_layout.addWidget(self.credits_widget)
        self.stacked_layout.setCurrentWidget(self.home_widget)

        QTimer.singleShot(100, self.animate_home_in)

        btn_credits.clicked.connect(self.transition_to_credits)
        self.btn_back.clicked.connect(self.transition_to_home)
        btn_install_deps.clicked.connect(self.install_dependencies)

    def install_dependencies(self):
        """Handle comprehensive dependency installation"""
        # Create installer
        installer = DependencyInstaller()
        
        # Get all dependencies from the directory
        dependencies, unmapped = installer.get_all_dependencies(directory=self.script_dir)
        
        if not dependencies and not unmapped:
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle("No Dependencies")
            msg.setText("No external dependencies found that need installation.")
            msg.setIcon(QMessageBox.Information)
            msg.exec_()
            return
        
        # Create installation window
        self.install_window = InstallationWindow(self)
        self.install_window.show()
        
        # Show found dependencies
        self.install_window.update_status("🔍 Dependency Analysis Complete")
        self.install_window.update_status(f"📦 Found {len(dependencies)} packages to install:")
        for dep in dependencies:
            self.install_window.update_status(f"   • {dep}")
        
        if unmapped:
            self.install_window.update_status(f"\n⚠️ Found {len(unmapped)} unmapped imports:")
            for imp in unmapped:
                self.install_window.update_status(f"   • {imp}")
        
        # Start installation in a separate thread
        self.installer = installer
        self.dependencies = dependencies
        
        # Use QTimer to run installation steps
        self.installation_steps = [
            ("create_venv",),
            ("install_deps",),
            ("create_requirements",),
            ("create_launchers",)
        ]
        self.current_step = 0
        
        QTimer.singleShot(1000, self.process_installation_step)
    
    def process_installation_step(self):
        """Process installation steps one by one"""
        if self.current_step >= len(self.installation_steps):
            self.install_window.installation_complete(True, self.script_dir)
            return
        
        step = self.installation_steps[self.current_step]
        
        try:
            if step[0] == "create_venv":
                self.install_window.set_progress_range(0, 0)  # Indeterminate
                success = self.installer.create_virtual_environment(
                    self.venv_path, 
                    self.install_window.update_status
                )
                if not success:
                    self.install_window.installation_complete(False, self.script_dir)
                    return
            
            elif step[0] == "install_deps":
                self.install_window.set_progress_range(0, len(self.dependencies))
                success = self.installer.install_dependencies(
                    self.venv_path,
                    self.dependencies,
                    self.install_window.update_status
                )
                # Continue even if some packages failed
                
            elif step[0] == "create_requirements":
                self.installer.create_requirements_file(
                    self.venv_path,
                    self.script_dir,
                    self.install_window.update_status
                )
                
            elif step[0] == "create_launchers":
                self.install_window.update_status("\n🚀 Creating launcher scripts...")
                
                # Create launchers for all Python files
                python_files = self.installer.scan_directory_for_python_files(self.script_dir)
                for py_file in python_files:
                    filename = os.path.basename(py_file)
                    if filename.startswith('Dev') or filename == '__init__.py':
                        continue
                    
                    script_name = os.path.splitext(filename)[0]
                    launcher_path = self.installer.create_launcher_script(
                        self.venv_path, 
                        script_name.lower(), 
                        py_file, 
                        self.script_dir
                    )
                    self.install_window.update_status(f"   Created: {os.path.basename(launcher_path)}")
            
        except Exception as e:
            self.install_window.update_status(f"❌ Error in step {step[0]}: {e}")
        
        self.current_step += 1
        QTimer.singleShot(500, self.process_installation_step)

    def run_script_with_venv(self, script_name):
        """Run a script using the virtual environment if it exists"""
        script_path = os.path.join(self.script_dir, script_name)
        
        if os.path.exists(self.venv_path):
            # Use virtual environment
            venv_paths = DependencyInstaller().get_venv_paths(self.venv_path)
            python_path = venv_paths['python']
            
            if os.path.exists(python_path):
                if sys.platform == "win32":
                    subprocess.Popen([python_path, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen([python_path, script_path])
                return
        
        # Fallback to system Python
        if sys.platform == "win32":
            subprocess.Popen([sys.executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen([sys.executable, script_path])

    def animate_home_in(self):
        self.home_animations = []
        for i, btn in enumerate(self.home_buttons):
            btn_rect = btn.geometry()
            parent_rect = btn.parentWidget().rect()
            btn_size = btn.size()
            centered_rect = QRect(
                (parent_rect.width() - btn_size.width()) // 2,
                btn_rect.top(),
                btn_size.width(),
                btn_size.height()
            )
            btn.setGeometry(centered_rect)
            btn_rect = btn.geometry()
            start_rect = QRect(btn_rect)
            start_rect.moveLeft(btn_rect.left() - 200)

            geom_anim = QPropertyAnimation(btn, b"geometry")
            geom_anim.setDuration(700)
            geom_anim.setStartValue(start_rect)
            geom_anim.setEndValue(btn_rect)
            geom_anim.setEasingCurve(QEasingCurve.OutQuart)

            opacity_anim = QPropertyAnimation(btn.graphicsEffect(), b"opacity")
            opacity_anim.setDuration(700)
            opacity_anim.setStartValue(0)
            opacity_anim.setEndValue(1)
            opacity_anim.setEasingCurve(QEasingCurve.OutQuart)

            group = QParallelAnimationGroup()
            group.addAnimation(geom_anim)
            group.addAnimation(opacity_anim)

            QTimer.singleShot(i * 120, group.start)
            self.home_animations.append(group)

    def animate_home_out(self, callback=None):
        self.home_animations = []
        for i, btn in enumerate(self.home_buttons):
            btn_rect = btn.geometry()
            end_rect = QRect(btn_rect)
            end_rect.moveLeft(btn_rect.left() - 200)

            geom_anim = QPropertyAnimation(btn, b"geometry")
            geom_anim.setDuration(500)
            geom_anim.setStartValue(btn_rect)
            geom_anim.setEndValue(end_rect)
            geom_anim.setEasingCurve(QEasingCurve.InQuad)

            opacity_anim = QPropertyAnimation(btn.graphicsEffect(), b"opacity")
            opacity_anim.setDuration(500)
            opacity_anim.setStartValue(1)
            opacity_anim.setEndValue(0)
            opacity_anim.setEasingCurve(QEasingCurve.InQuad)

            group = QParallelAnimationGroup()
            group.addAnimation(geom_anim)
            group.addAnimation(opacity_anim)

            if i == len(self.home_buttons) - 1 and callback:
                group.finished.connect(callback)

            QTimer.singleShot(i * 80, group.start)
            self.home_animations.append(group)

    def animate_credits_in(self):
        self.credits_animations = []
        for i, btn in enumerate(self.credits_buttons):
            btn_rect = btn.geometry()
            parent_rect = btn.parentWidget().rect()
            btn_size = btn.size()
            centered_rect = QRect(
                (parent_rect.width() - btn_size.width()) // 2,
                btn_rect.top(),
                btn_size.width(),
                btn_size.height()
            )
            btn.setGeometry(centered_rect)
            btn_rect = btn.geometry()
            start_rect = QRect(btn_rect)
            start_rect.moveLeft(btn_rect.left() + 200)

            geom_anim = QPropertyAnimation(btn, b"geometry")
            geom_anim.setDuration(700)
            geom_anim.setStartValue(start_rect)
            geom_anim.setEndValue(btn_rect)
            geom_anim.setEasingCurve(QEasingCurve.OutQuart)

            opacity_anim = QPropertyAnimation(btn.graphicsEffect(), b"opacity")
            opacity_anim.setDuration(700)
            opacity_anim.setStartValue(0)
            opacity_anim.setEndValue(1)
            opacity_anim.setEasingCurve(QEasingCurve.OutQuart)

            group = QParallelAnimationGroup()
            group.addAnimation(geom_anim)
            group.addAnimation(opacity_anim)

            QTimer.singleShot(i * 120, group.start)
            self.credits_animations.append(group)

    def animate_credits_out(self, callback=None):
        self.credits_animations = []
        for i, btn in enumerate(self.credits_buttons):
            btn_rect = btn.geometry()
            end_rect = QRect(btn_rect)
            end_rect.moveLeft(btn_rect.left() + 200)

            geom_anim = QPropertyAnimation(btn, b"geometry")
            geom_anim.setDuration(500)
            geom_anim.setStartValue(btn_rect)
            geom_anim.setEndValue(end_rect)
            geom_anim.setEasingCurve(QEasingCurve.InQuad)

            opacity_anim = QPropertyAnimation(btn.graphicsEffect(), b"opacity")
            opacity_anim.setDuration(500)
            opacity_anim.setStartValue(1)
            opacity_anim.setEndValue(0)
            opacity_anim.setEasingCurve(QEasingCurve.InQuad)

            group = QParallelAnimationGroup()
            group.addAnimation(geom_anim)
            group.addAnimation(opacity_anim)

            if i == len(self.credits_buttons) - 1 and callback:
                group.finished.connect(callback)

            QTimer.singleShot(i * 80, group.start)
            self.credits_animations.append(group)

    def transition_to_credits(self):
        def after_home_out():
            self.stacked_layout.setCurrentWidget(self.credits_widget)
            QTimer.singleShot(100, self.animate_credits_in)
        self.animate_home_out(after_home_out)

    def transition_to_home(self):
        def after_credits_out():
            self.stacked_layout.setCurrentWidget(self.home_widget)
            QTimer.singleShot(100, self.animate_home_in)
        self.animate_credits_out(after_credits_out)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnimatedStackedWindow()
    window.show()
    
    # Connect buttons to launch scripts with virtual environment
    def open_poly_script():
        def after_home_out():
            window.run_script_with_venv("Polynomial.py")
            window.close()
        window.animate_home_out(after_home_out)

    def open_integration_script():
        def after_home_out():
            window.run_script_with_venv("Integration.py")
            window.close()
        window.animate_home_out(after_home_out)

    window.home_buttons[0].clicked.connect(open_poly_script)
    window.home_buttons[1].clicked.connect(open_integration_script)

    sys.exit(app.exec_())