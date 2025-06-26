import sys
import os
import subprocess
import sympy as sp
from sympy import symbols, integrate, latex, simplify, sympify
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')
import re
import json

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QComboBox, QLineEdit, QGraphicsOpacityEffect, 
                             QHBoxLayout, QScrollArea, QPushButton, QSizePolicy,
                             QTextEdit, QFrame)
from PyQt5.QtGui import (QPainter, QBrush, QColor, QFont, QTextCursor, 
                         QTextCharFormat, QTextDocument, QPalette)
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QPoint, QTimer, QEasingCurve, QUrl, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel

class MathDisplayWidget(QWidget):
    """Widget to display mathematical expressions using matplotlib"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 1), facecolor='#252525')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.setStyleSheet("background: transparent;")
        
    def display_math(self, latex_expr, color='white', fontsize=16):
        """Display mathematical expression using LaTeX"""
        self.figure.clear()
        ax = self.figure.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_facecolor('#252525')
        
        try:
            ax.text(0.5, 0.5, f'${latex_expr}$', 
                   horizontalalignment='center',
                   verticalalignment='center',
                   fontsize=fontsize,
                   color=color,
                   transform=ax.transAxes)
        except Exception:
            # Fallback to plain text if LaTeX fails
            ax.text(0.5, 0.5, latex_expr, 
                   horizontalalignment='center',
                   verticalalignment='center',
                   fontsize=fontsize,
                   color=color,
                   transform=ax.transAxes)
        
        self.figure.patch.set_facecolor('#252525')
        self.canvas.draw()
        
    def clear_display(self):
        """Clear the mathematical display"""
        self.figure.clear()
        self.canvas.draw()

class JavaScriptBridge(QWidget):
    """Bridge for communication between Python and JavaScript"""
    
    mathChanged = pyqtSignal(str, str)  # latex, plain_text
    
    def __init__(self):
        super().__init__()
        
    def update_math(self, latex, plain_text):
        """Called from JavaScript when math content changes"""
        self.mathChanged.emit(latex, plain_text)

class MathQuillWidget(QWidget):
    """Widget that provides MathQuill input via QWebEngineView"""
    
    mathChanged = pyqtSignal(str, str)  # latex, plain_text
    
    def __init__(self, parent=None, placeholder="Enter function..."):
        super().__init__(parent)
        self.placeholder = placeholder
        self.current_latex = ""
        self.current_plain_text = ""
        
        # Create the web engine view
        self.web_view = QWebEngineView(self)
        self.web_view.setFixedHeight(60)
        
        # Set up the web channel for JavaScript communication
        self.channel = QWebChannel(self)
        self.bridge = JavaScriptBridge()
        self.bridge.mathChanged.connect(self._on_math_changed)
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.web_view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Load the HTML content
        self._load_mathquill_html()
        
    def _load_mathquill_html(self):
        """Load the MathQuill HTML content"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MathQuill Input</title>
    
    <!-- MathQuill CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/mathquill/0.10.1/mathquill.css" />
    
    <style>
        body {{
            margin: 0;
            padding: 10px;
            background-color: #252525;
            font-family: 'Times New Roman', serif;
            display: flex;
            align-items: center;
            height: 40px;
            overflow: hidden;
        }}
        
        #math-field {{
            width: 100%;
            min-height: 40px;
            padding: 8px 12px;
            border: 2px solid #555;
            border-radius: 8px;
            background-color: #353535;
            color: white;
            font-size: 20px;
            box-sizing: border-box;
        }}
        
        #math-field:focus {{
            border-color: #777;
            outline: none;
        }}
        
        .mq-focused {{
            border-color: #777 !important;
        }}
        
        .mq-math-mode .mq-cursor {{
            border-color: white;
        }}
        
        .mq-math-mode {{
            color: white;
        }}
        
        /* Style MathQuill elements to match our theme */
        .mq-math-mode .mq-binary-operator,
        .mq-math-mode .mq-operator-name,
        .mq-math-mode .mq-text-mode {{
            color: white;
        }}
        
        .mq-math-mode .mq-fraction {{
            color: white;
        }}
        
        .mq-math-mode .mq-sqrt-stem {{
            border-color: white;
        }}
        
        .mq-math-mode .mq-sqrt-prefix {{
            border-color: white;
        }}
    </style>
</head>
<body>
    <div id="math-field">{self.placeholder}</div>
    
    <!-- MathQuill JavaScript -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathquill/0.10.1/mathquill.min.js"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    
    <script>
        var MQ = MathQuill.getInterface(2);
        var mathField;
        var bridge;
        
        // Initialize when Qt WebChannel is ready
        new QWebChannel(qt.webChannelTransport, function(channel) {{
            bridge = channel.objects.bridge;
            initializeMathQuill();
        }});
        
        function initializeMathQuill() {{
            var mathFieldSpan = document.getElementById('math-field');
            
            mathField = MQ.MathField(mathFieldSpan, {{
                spaceBehavesLikeTab: true,
                leftRightIntoCmdGoes: 'up',
                restrictMismatchedBrackets: true,
                sumStartsWithNEquals: true,
                supSubsRequireOperand: true,
                charsThatBreakOutOfSupSub: '+-=<>',
                autoSubscriptNumerals: true,
                autoCommands: 'pi theta sqrt sum int infinity',
                autoOperatorNames: 'sin cos tan sec csc cot ln log exp arcsin arccos arctan',
                
                handlers: {{
                    edit: function() {{
                        var latex = mathField.latex();
                        var text = mathField.text();
                        
                        // Send to Python
                        if (bridge && bridge.update_math) {{
                            bridge.update_math(latex, text);
                        }}
                    }},
                    
                    enter: function() {{
                        // Handle enter key if needed
                        return false;
                    }}
                }}
            }});
            
            // Set initial focus
            mathField.focus();
            
            // Add keyboard shortcuts
            $(document).keydown(function(e) {{
                if (e.which === 191 && !e.shiftKey) {{ // '/' key
                    e.preventDefault();
                    mathField.cmd('\\\\frac');
                    return false;
                }}
                
                if (e.which === 54 && e.shiftKey) {{ // '^' key (Shift+6)
                    e.preventDefault();
                    mathField.cmd('^');
                    return false;
                }}
                
                if (e.which === 56 && e.shiftKey) {{ // '*' key (Shift+8)
                    e.preventDefault();
                    mathField.cmd('\\\\cdot');
                    return false;
                }}
            }});
        }}
        
        // Function to set content from Python
        function setLatex(latex) {{
            if (mathField) {{
                mathField.latex(latex);
            }}
        }}
        
        // Function to clear content
        function clear() {{
            if (mathField) {{
                mathField.latex('');
            }}
        }}
        
        // Function to get current content
        function getLatex() {{
            return mathField ? mathField.latex() : '';
        }}
        
        function getText() {{
            return mathField ? mathField.text() : '';
        }}
    </script>
</body>
</html>
        """
        
        self.web_view.setHtml(html_content)
    
    def _on_math_changed(self, latex, plain_text):
        """Handle math content changes from JavaScript"""
        self.current_latex = latex
        self.current_plain_text = plain_text
        self.mathChanged.emit(latex, plain_text)
    
    def get_latex(self):
        """Get the current LaTeX content"""
        return self.current_latex
    
    def get_plain_text(self):
        """Get the current plain text content"""
        return self.current_plain_text
    
    def get_raw_expression(self):
        """Get raw expression for SymPy parsing (converts LaTeX to SymPy-compatible format)"""
        latex = self.current_latex
        if not latex:
            return ""
        
        # Convert LaTeX to SymPy-compatible format
        # Handle fractions
        latex = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', latex)
        
        # Handle superscripts
        latex = re.sub(r'\^?\{([^}]+)\}', r'^(\1)', latex)
        latex = re.sub(r'\^([a-zA-Z0-9])', r'^\1', latex)
        
        # Handle square roots
        latex = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', latex)
        latex = re.sub(r'\\sqrt\[([^]]+)\]\{([^}]+)\}', r'(\2)^(1/\1)', latex)
        
        # Handle trigonometric functions
        latex = re.sub(r'\\sin', 'sin', latex)
        latex = re.sub(r'\\cos', 'cos', latex)
        latex = re.sub(r'\\tan', 'tan', latex)
        latex = re.sub(r'\\sec', 'sec', latex)
        latex = re.sub(r'\\csc', 'csc', latex)
        latex = re.sub(r'\\cot', 'cot', latex)
        
        # Handle logarithms
        latex = re.sub(r'\\ln', 'ln', latex)
        latex = re.sub(r'\\log', 'log', latex)
        
        # Handle other functions
        latex = re.sub(r'\\exp', 'exp', latex)
        
        # Handle constants
        latex = re.sub(r'\\pi', 'pi', latex)
        latex = re.sub(r'\\infty', 'infinity', latex)
        
        # Handle multiplication
        latex = re.sub(r'\\cdot', '*', latex)
        latex = re.sub(r'\\times', '*', latex)
        
        # Remove any remaining backslashes and braces for simple expressions
        latex = re.sub(r'\\([a-zA-Z]+)', r'\1', latex)
        latex = latex.replace('{', '').replace('}', '')
        
        return latex
    
    def set_latex(self, latex):
        """Set the LaTeX content"""
        self.web_view.page().runJavaScript(f"setLatex('{latex}');")
    
    def clear(self):
        """Clear the content"""
        self.web_view.page().runJavaScript("clear();")

class IntegrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integration Solver")
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Store animation references to prevent garbage collection
        self.current_animations = []
        
        self.initUI()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(QColor("#252525"))
        rect = QRectF(0, 0, self.width(), self.height())
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 100, 100)

    def initUI(self):
        # Create scroll area for content
        scroll_area = QScrollArea(self)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #353535;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
        """)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Create content widget
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        scroll_area.setWidget(content_widget)

        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # Position scroll area
        scroll_area.setGeometry(0, 0, self.width(), self.height())

        # Add Home button in the top right
        self.home_button = QPushButton("Home", self)
        self.home_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.home_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #353535;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 6px 18px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.home_button.setFixedSize(90, 38)
        self.home_button.raise_()
        self.home_button.move(self.width() - self.home_button.width() - 20, 20)
        self.home_button.show()
        self.home_button.clicked.connect(self.home_transition)

        # Integration type dropdown
        self.setup_dropdown()

        # Container for integration content
        self.integration_container = QWidget()
        self.integration_container.setStyleSheet("background: transparent;")
        self.integration_layout = QVBoxLayout(self.integration_container)
        self.integration_layout.setAlignment(Qt.AlignTop)
        self.layout.addWidget(self.integration_container)

        # Initially show select message
        self.show_select_message()

        # Add stretch to push content to top
        self.layout.addStretch()

    def setup_dropdown(self):
        # Dropdown layout
        dropdown_layout = QHBoxLayout()
        dropdown_layout.setSpacing(10)
        
        type_label = QLabel("Integration Type:", self)
        type_font = QFont("Arial", 24, QFont.Bold)
        type_label.setFont(type_font)
        type_label.setStyleSheet("color: white; background: transparent;")
        
        self.type_combo = QComboBox(self)
        self.type_combo.setFont(QFont("Arial", 20, QFont.Bold))
        self.type_combo.setStyleSheet("""
            QComboBox {
                color: white;
                background-color: #353535;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 6px 18px;
                min-width: 120px;
                font-weight: bold;
            }
            QComboBox QAbstractItemView {
                background: #353535;
                color: white;
                selection-background-color: #454545;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        self.type_combo.addItems(["", "Indefinite", "Definite"])
        self.type_combo.currentTextChanged.connect(self.handle_type_selection)
        
        dropdown_layout.addWidget(type_label)
        dropdown_layout.addWidget(self.type_combo)
        dropdown_layout.addStretch()
        
        self.layout.addLayout(dropdown_layout)

    def clear_integration_content(self):
        """Clear all widgets from integration container"""
        # First, clear any ongoing animations
        self.current_animations.clear()
        
        # Remove all widgets and their layouts
        while self.integration_layout.count():
            child = self.integration_layout.takeAt(0)
            if child.widget():
                # Clear any graphics effects before deletion
                child.widget().setGraphicsEffect(None)
                child.widget().deleteLater()
            elif child.layout():
                # Handle nested layouts
                self.clear_layout(child.layout())
        
        # Process pending deletions immediately
        QApplication.processEvents()

    def clear_layout(self, layout):
        """Recursively clear a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setGraphicsEffect(None)
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def show_select_message(self):
        """Show 'Select integration type' message"""
        self.clear_integration_content()
        
        message_label = QLabel("Select integration type")
        message_label.setFont(QFont("Arial", 28, QFont.Bold))
        message_label.setStyleSheet("color: white; background: transparent;")
        message_label.setAlignment(Qt.AlignCenter)
        
        self.integration_layout.addWidget(message_label)

    def show_indefinite_integration(self):
        """Show indefinite integration interface"""
        self.clear_integration_content()
        
        # Create integral expression layout
        integral_layout = QHBoxLayout()
        integral_layout.setAlignment(Qt.AlignCenter)
        integral_layout.setSpacing(10)
        
        # Integral symbol
        integral_symbol = QLabel("∫")
        integral_symbol.setFont(QFont("Times New Roman", 48, QFont.Bold))
        integral_symbol.setStyleSheet("color: white; background: transparent;")
        
        # Function input with MathQuill
        self.function_input = MathQuillWidget(self.integration_container, "Enter function (e.g., x^2, sin(x), e^x)")
        self.function_input.setFixedWidth(350)
        
        # Connect to calculation
        self.function_input.mathChanged.connect(self.calculate_indefinite_integral)
        
        # dx label
        dx_label = QLabel("dx")
        dx_label.setFont(QFont("Times New Roman", 24, QFont.Bold))
        dx_label.setStyleSheet("color: white; background: transparent;")
        
        integral_layout.addWidget(integral_symbol)
        integral_layout.addWidget(self.function_input)
        integral_layout.addWidget(dx_label)
        
        self.integration_layout.addLayout(integral_layout)
        
        # Results area with better spacing
        self.results_widget = QWidget()
        self.results_widget.setStyleSheet("background: transparent;")
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.results_layout.setSpacing(20)
        
        # Antiderivative result using math display
        self.antiderivative_display = MathDisplayWidget()
        self.antiderivative_display.setFixedHeight(80)
        self.antiderivative_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Add spacing above the result
        self.results_layout.addSpacing(40)
        self.results_layout.addWidget(self.antiderivative_display)
        
        # Method label
        self.method_label = QLabel("")
        self.method_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.method_label.setStyleSheet("color: #87CEEB; background: transparent; margin: 10px;")
        self.method_label.setAlignment(Qt.AlignCenter)
        self.method_label.setWordWrap(True)
        
        self.results_layout.addWidget(self.method_label)
        
        self.integration_layout.addWidget(self.results_widget)

    def show_definite_integration(self):
        """Show definite integration interface"""
        self.clear_integration_content()
        
        # Create integral expression layout with bounds
        integral_layout = QVBoxLayout()
        integral_layout.setAlignment(Qt.AlignCenter)
        integral_layout.setSpacing(15)
        
        # Upper and lower bounds
        bounds_layout = QHBoxLayout()
        bounds_layout.setAlignment(Qt.AlignCenter)
        bounds_layout.setSpacing(20)
        
        # Lower bound
        lower_layout = QHBoxLayout()
        lower_label = QLabel("Lower bound:")
        lower_label.setFont(QFont("Arial", 16, QFont.Bold))
        lower_label.setStyleSheet("color: white; background: transparent;")
        self.lower_bound_input = QLineEdit()
        self.lower_bound_input.setFont(QFont("Arial", 16))
        self.lower_bound_input.setStyleSheet("""
            QLineEdit {
                color: white;
                background-color: #353535;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                max-width: 80px;
            }
        """)
        self.lower_bound_input.textChanged.connect(self.calculate_definite_integral)
        lower_layout.addWidget(lower_label)
        lower_layout.addWidget(self.lower_bound_input)
        
        # Upper bound
        upper_layout = QHBoxLayout()
        upper_label = QLabel("Upper bound:")
        upper_label.setFont(QFont("Arial", 16, QFont.Bold))
        upper_label.setStyleSheet("color: white; background: transparent;")
        self.upper_bound_input = QLineEdit()
        self.upper_bound_input.setFont(QFont("Arial", 16))
        self.upper_bound_input.setStyleSheet("""
            QLineEdit {
                color: white;
                background-color: #353535;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                max-width: 80px;
            }
        """)
        self.upper_bound_input.textChanged.connect(self.calculate_definite_integral)
        upper_layout.addWidget(upper_label)
        upper_layout.addWidget(self.upper_bound_input)
        
        bounds_layout.addLayout(lower_layout)
        bounds_layout.addLayout(upper_layout)
        integral_layout.addLayout(bounds_layout)
        
        # Main integral expression
        main_integral_layout = QHBoxLayout()
        main_integral_layout.setAlignment(Qt.AlignCenter)
        main_integral_layout.setSpacing(10)
        
        # Integral symbol
        integral_symbol = QLabel("∫")
        integral_symbol.setFont(QFont("Times New Roman", 48, QFont.Bold))
        integral_symbol.setStyleSheet("color: white; background: transparent;")
        
        # Function input with MathQuill
        self.definite_function_input = MathQuillWidget(self.integration_container, "Enter function (e.g., x^2, sin(x), e^x)")
        self.definite_function_input.setFixedWidth(350)
        self.definite_function_input.mathChanged.connect(self.calculate_definite_integral)
        
        # dx label
        dx_label = QLabel("dx")
        dx_label.setFont(QFont("Times New Roman", 24, QFont.Bold))
        dx_label.setStyleSheet("color: white; background: transparent;")
        
        main_integral_layout.addWidget(integral_symbol)
        main_integral_layout.addWidget(self.definite_function_input)
        main_integral_layout.addWidget(dx_label)
        
        integral_layout.addLayout(main_integral_layout)
        self.integration_layout.addLayout(integral_layout)
        
        # Results area for definite integration with better spacing
        self.definite_results_widget = QWidget()
        self.definite_results_widget.setStyleSheet("background: transparent;")
        self.definite_results_layout = QVBoxLayout(self.definite_results_widget)
        self.definite_results_layout.setAlignment(Qt.AlignTop)
        self.definite_results_layout.setSpacing(20)
        
        # Definite integral result using math display
        self.definite_result_display = MathDisplayWidget()
        self.definite_result_display.setFixedHeight(80)
        self.definite_result_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Add spacing above the result
        self.definite_results_layout.addSpacing(40)
        self.definite_results_layout.addWidget(self.definite_result_display)
        
        # Method label for definite
        self.definite_method_label = QLabel("")
        self.definite_method_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.definite_method_label.setStyleSheet("color: #87CEEB; background: transparent; margin: 10px;")
        self.definite_method_label.setAlignment(Qt.AlignCenter)
        self.definite_method_label.setWordWrap(True)
        
        self.definite_results_layout.addWidget(self.definite_method_label)
        
        self.integration_layout.addWidget(self.definite_results_widget)

    def handle_type_selection(self, value):
        """Handle integration type selection with smooth transitions"""
        if value == "":
            self.animate_out_and_show(self.show_select_message)
        elif value == "Indefinite":
            self.animate_out_and_show(self.show_indefinite_integration)
        elif value == "Definite":
            self.animate_out_and_show(self.show_definite_integration)

    def animate_out_and_show(self, show_method):
        """Animate current content out, then show new content"""
        # Clear any existing animations
        self.current_animations.clear()
        
        # Get all current widgets in the integration container
        widgets_to_animate = []
        for i in range(self.integration_layout.count()):
            item = self.integration_layout.itemAt(i)
            if item and item.widget():
                widgets_to_animate.append(item.widget())
        
        if not widgets_to_animate:
            # No current content, show new content immediately
            show_method()
            return
        
        # Create fade out animations for current widgets
        animations = []
        for widget in widgets_to_animate:
            # Remove any existing graphics effect first
            widget.setGraphicsEffect(None)
            
            # Create new opacity effect
            opacity_effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(1.0)
            
            fade_out = QPropertyAnimation(opacity_effect, b"opacity")
            fade_out.setDuration(200)  # Reduced duration for snappier feel
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.InCubic)
            
            animations.append(fade_out)
            fade_out.start()
        
        # Store animations to prevent garbage collection
        self.current_animations = animations
        
        # After fade out completes, clear content and show new content
        def on_fade_out_complete():
            # Force clear all content immediately
            self.clear_integration_content()
            # Show new content
            show_method()
            # Animate in new content
            QTimer.singleShot(50, self.animate_in_new_content)
        
        # Connect the last animation to the completion handler
        if animations:
            animations[-1].finished.connect(on_fade_out_complete)

    def animate_in_new_content(self):
        """Animate new content in with fade effect"""
        # Get all new widgets in the integration container
        widgets_to_animate = []
        for i in range(self.integration_layout.count()):
            item = self.integration_layout.itemAt(i)
            if item and item.widget():
                widgets_to_animate.append(item.widget())
        
        if not widgets_to_animate:
            return
        
        # Create fade in animations for new widgets
        fade_in_animations = []
        for widget in widgets_to_animate:
            # Remove any existing effect
            widget.setGraphicsEffect(None)
            
            # Create opacity effect
            opacity_effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(0.0)
            
            fade_in = QPropertyAnimation(opacity_effect, b"opacity")
            fade_in.setDuration(200)  # Reduced duration
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.OutCubic)
            
            fade_in_animations.append(fade_in)
            fade_in.start()
        
        # Store fade in animations
        self.current_animations.extend(fade_in_animations)
        
        # After fade in completes, remove the opacity effects
        def cleanup_effects():
            for widget in widgets_to_animate:
                if widget and not widget.isHidden():
                    widget.setGraphicsEffect(None)
        
        if fade_in_animations:
            fade_in_animations[-1].finished.connect(cleanup_effects)

    def determine_integration_method(self, expr, result):
        """Determine the integration method used"""
        x = symbols('x')
        expr_str = str(expr)
        
        # Check for common patterns
        if 'sin' in expr_str or 'cos' in expr_str or 'tan' in expr_str:
            return "Trigonometric Integration"
        elif 'exp' in expr_str or 'log' in expr_str or 'E' in expr_str:
            return "Exponential/Logarithmic Integration"
        elif '*' in expr_str and any(func in expr_str for func in ['sin', 'cos', 'exp', 'log']):
            return "Integration by Parts"
        elif expr.is_polynomial():
            return "Power Rule"
        elif expr.has(sp.sqrt):
            return "Square Root Integration"
        elif '/' in expr_str:
            return "Rational Function Integration"
        else:
            # Try to detect substitution by checking if the derivative of inner function is present
            try:
                if expr.has(sp.Function):
                    return "Substitution Method"
                else:
                    return "Direct Integration"
            except Exception:
                return "Standard Integration"

    def parse_function(self, function_text):
        """Parse function text with support for both e^x and exp(x) notation and implicit multiplication"""
        # First handle implicit multiplication using the parsing method
        function_text = self.add_implicit_multiplication_for_parsing(function_text)
        
        # Replace common notation for sympy
        function_text_sympy = function_text.replace('^', '**')
        function_text_sympy = function_text_sympy.replace('ln', 'log')
        
        # Handle e^x notation - convert to exp() for sympy
        function_text_sympy = re.sub(r'\be\*\*\(([^)]+)\)', r'exp(\1)', function_text_sympy)
        function_text_sympy = re.sub(r'\be\*\*([a-zA-Z0-9_]+)', r'exp(\1)', function_text_sympy)
        
        return sympify(function_text_sympy)

    def add_implicit_multiplication_for_parsing(self, text):
        """Add explicit multiplication operators for implicit multiplication (for parsing only)"""
        # Remove spaces first
        text = text.replace(' ', '')
        
        # Handle number followed by variable: 3x -> 3*x
        text = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', text)
        
        # Handle number followed by function: 3sin -> 3*sin, 2ln -> 2*ln
        text = re.sub(r'(\d)(sin|cos|tan|sec|csc|cot|ln|log|exp|sqrt)', r'\1*\2', text)
        
        # Handle number followed by opening parenthesis: 3( -> 3*(
        text = re.sub(r'(\d)\(', r'\1*(', text)
        
        # Handle variable followed by opening parenthesis: x( -> x*(
        text = re.sub(r'([a-zA-Z])\(', r'\1*(', text)
        
        # Handle closing parenthesis followed by variable: )x -> )*x
        text = re.sub(r'\)([a-zA-Z])', r')*\1', text)
        
        # Handle closing parenthesis followed by number: )3 -> )*3
        text = re.sub(r'\)(\d)', r')*\1', text)
        
        # Handle closing parenthesis followed by opening parenthesis: )( -> )*(
        text = re.sub(r'\)\(', r')*(', text)
        
        # Handle closing parenthesis followed by function: )sin -> )*sin
        text = re.sub(r'\)(sin|cos|tan|sec|csc|cot|ln|log|exp|sqrt)', r')*\1', text)
        
        # Handle variable followed by variable: xy -> x*y (but not for multi-letter functions)
        # Be careful not to break function names like 'sin', 'cos', etc.
        text = re.sub(r'([a-zA-Z])([a-zA-Z])(?![a-zA-Z])', r'\1*\2', text)
        
        # Handle function followed by variable: sin(x)y -> sin(x)*y
        text = re.sub(r'(sin|cos|tan|sec|csc|cot|ln|log|exp|sqrt)\(([^)]+)\)([a-zA-Z])', r'\1(\2)*\3', text)
        
        return text

    def calculate_indefinite_integral(self, latex, plain_text):
        """Calculate and display indefinite integral"""
        try:
            function_text = self.function_input.get_raw_expression().strip()
            if not function_text:
                self.antiderivative_display.clear_display()
                self.method_label.setText("")
                return
            
            x = symbols('x')
            
            # Parse the function with enhanced e^x support
            expr = self.parse_function(function_text)
            
            # Calculate the integral
            result = integrate(expr, x)
            
            # Simplify the result
            result = simplify(result)
            
            # Determine integration method
            method = self.determine_integration_method(expr, result)
            
            # Display result using LaTeX with proper multiplication formatting
            result_latex = latex(result)
            # Replace * with \cdot for better mathematical notation
            result_latex = result_latex.replace('*', '\\cdot')
            # Also handle any x symbols that might appear as multiplication
            result_latex = re.sub(r'\\times', r'\\cdot', result_latex)
            
            self.antiderivative_display.display_math(f"{result_latex} + C", color='#90EE90', fontsize=18)
            
            self.method_label.setText(f"Method: {method}")
            
        except Exception as e:
            self.antiderivative_display.display_math("Invalid \\ function \\ or \\ unable \\ to \\ integrate", color='#FF6B6B', fontsize=16)
            self.method_label.setText("")

    def calculate_definite_integral(self, *args):
        """Calculate and display definite integral"""
        try:
            function_text = self.definite_function_input.get_raw_expression().strip()
            lower_text = self.lower_bound_input.text().strip()
            upper_text = self.upper_bound_input.text().strip()
            
            if not function_text:
                self.definite_result_display.clear_display()
                self.definite_method_label.setText("")
                return
            
            if not lower_text or not upper_text:
                self.definite_result_display.clear_display()
                self.definite_method_label.setText("")
                return
            
            x = symbols('x')
            
            # Parse the function with enhanced e^x support
            expr = self.parse_function(function_text)
            lower_bound = sympify(lower_text)
            upper_bound = sympify(upper_text)
            
            # Calculate the definite integral
            result = integrate(expr, (x, lower_bound, upper_bound))
            
            # Simplify the result
            result = simplify(result)
            
            # Determine integration method
            method = self.determine_integration_method(expr, result)
            
            # Display result using LaTeX with proper multiplication formatting
            result_latex = latex(result)
            # Replace * with \cdot for better mathematical notation
            result_latex = result_latex.replace('*', '\\cdot')
            # Also handle any x symbols that might appear as multiplication
            result_latex = re.sub(r'\\times', r'\\cdot', result_latex)
            
            self.definite_result_display.display_math(result_latex, color='#90EE90', fontsize=18)
            
            self.definite_method_label.setText(f"Method: {method}")
            
        except Exception as e:
            self.definite_result_display.display_math("Invalid \\ function, \\ bounds, \\ or \\ unable \\ to \\ integrate", color='#FF6B6B', fontsize=14)
            self.definite_method_label.setText("")

    def home_transition(self):
        """Transition back to home with animation"""
        # Animate all widgets: slide right and fade out
        anims = []
        widgets = []
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            w = item.widget() if item and item.widget() else None
            if w:
                widgets.append(w)
        widgets.append(self.home_button)
        
        for w in widgets:
            # Slide right
            pos_anim = QPropertyAnimation(w, b"pos")
            pos_anim.setDuration(400)
            pos_anim.setEasingCurve(QEasingCurve.InCubic)
            pos_anim.setStartValue(w.pos())
            pos_anim.setEndValue(w.pos() + QPoint(400, 0))
            
            # Fade out
            opacity = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(opacity)
            opacity.setOpacity(1)
            fade_anim = QPropertyAnimation(opacity, b"opacity")
            fade_anim.setDuration(400)
            fade_anim.setStartValue(1)
            fade_anim.setEndValue(0)
            fade_anim.setEasingCurve(QEasingCurve.InCubic)
            
            pos_anim.start()
            fade_anim.start()
            anims.append((pos_anim, fade_anim))
        
        # After animation, launch home and close
        def launch_home():
            subprocess.Popen(
                [sys.executable, os.path.join(os.path.dirname(__file__), "Home.py")],
                    start_new_session=True
            )
            self.close()
        
        QTimer.singleShot(420, launch_home)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntegrationWindow()
    window.show()
    sys.exit(app.exec_())