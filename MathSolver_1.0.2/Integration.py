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
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QPoint, QTimer, QEasingCurve, QUrl, pyqtSignal, QRect, QParallelAnimationGroup
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

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
        
        self.setStyleSheet("""
            background: transparent;
            border-radius: 8px;
        """)
        
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
        
        # Enable console message logging
        page = self.web_view.page()
        page.javaScriptConsoleMessage = self.js_console_message
        
        # Intercept JavaScript calls
        page.urlChanged.connect(self._handle_url_change)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.web_view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Load the HTML content
        self._load_mathquill_html()
        
        # Wait for page to load
        self.web_view.loadFinished.connect(self._on_page_loaded)
        
        # Set up timer for polling
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._poll_for_updates)
        self.update_timer.setInterval(200)  # Check every 200ms
        
    def _on_page_loaded(self, ok):
        """Called when the web page has finished loading"""
        if ok:
            print("MathQuill page loaded successfully")
            # Start polling for updates
            self.update_timer.start()
        else:
            print("ERROR: MathQuill page failed to load")
    
    def _handle_url_change(self, url):
        """Handle URL changes (not used in this approach)"""
        pass
    
    def _poll_for_updates(self):
        """Poll JavaScript for content updates"""
        self.web_view.page().runJavaScript("getLatex();", self._handle_latex_result)
        self.web_view.page().runJavaScript("getText();", self._handle_text_result)
    
    def _handle_latex_result(self, latex):
        """Handle LaTeX result from JavaScript"""
        if latex != self.current_latex:
            print(f"LaTeX changed: '{latex}'")
            self.current_latex = latex
            # Get text as well
            self.web_view.page().runJavaScript("getText();", lambda text: self._handle_content_change(latex, text))
    
    def _handle_text_result(self, text):
        """Handle text result from JavaScript"""
        self.current_plain_text = text
    
    def _handle_content_change(self, latex, text):
        """Handle both latex and text change"""
        print(f"Content changed - latex: '{latex}', text: '{text}'")
        self.current_latex = latex
        self.current_plain_text = text
        self.mathChanged.emit(latex, text)
        
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
        
        /* Placeholder styling */
        .mq-placeholder {{
            color: #888 !important;
            opacity: 1 !important;
        }}
        
        .mq-empty.mq-hasCursor {{
            background: transparent;
        }}
    </style>
</head>
<body>
    <span id="math-field"></span>
    
    <!-- MathQuill JavaScript -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathquill/0.10.1/mathquill.min.js"></script>
    
    <script>
        var MQ = MathQuill.getInterface(2);
        var mathField;
        var lastLatex = '';
        var lastText = '';
        
        // Initialize MathQuill immediately
        $(document).ready(function() {{
            console.log('Document ready, initializing MathQuill...');
            initializeMathQuill();
        }});
        
        function initializeMathQuill() {{
            console.log('Initializing MathQuill...');
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
                placeholder: '{self.placeholder}',
                
                handlers: {{
                    edit: function() {{
                        var latex = mathField.latex();
                        var text = mathField.text();
                        
                        // Only update if content actually changed
                        if (latex !== lastLatex || text !== lastText) {{
                            lastLatex = latex;
                            lastText = text;
                            console.log('MathQuill edit event - latex:', latex, 'text:', text);
                            
                            // Use window method to communicate with Python
                            window.updateMath(latex, text);
                        }}
                    }},
                    
                    enter: function() {{
                        return false;
                    }}
                }}
            }});
            
            console.log('MathQuill initialized successfully');
            
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
        
        // Global function for Python communication
        window.updateMath = function(latex, text) {{
            console.log('Calling window.updateMath with:', latex, text);
            // This will be intercepted by Python
        }};
        
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
    
    def js_console_message(self, level, message, line, source):
        """Handle JavaScript console messages"""
        print(f"JS Console [{level}]: {message} (line {line})")
    
    def _on_math_changed(self, latex, plain_text):
        """Handle math content changes from JavaScript"""
        print(f"Python received: latex='{latex}', plain_text='{plain_text}'")  # Debug
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
        latex_expr = self.current_latex
        if not latex_expr:
            return ""
        
        print(f"Converting LaTeX to raw expression: '{latex_expr}'")  # Debug
        
        # Handle empty braces first (common issue)
        latex_expr = re.sub(r'\^?\{\s*\}', '', latex_expr)  # Remove empty braces like ^{ }
        latex_expr = re.sub(r'\^?\{\}', '', latex_expr)     # Remove empty braces like ^{}
        
        # Handle \left and \right parentheses
        latex_expr = re.sub(r'\\left\(', '(', latex_expr)
        latex_expr = re.sub(r'\\right\)', ')', latex_expr)
        latex_expr = re.sub(r'\\left\[', '[', latex_expr)
        latex_expr = re.sub(r'\\right\]', ']', latex_expr)
        latex_expr = re.sub(r'\\left\{', '{', latex_expr)
        latex_expr = re.sub(r'\\right\}', '}', latex_expr)
        
        # Handle trigonometric functions BEFORE processing fractions
        latex_expr = re.sub(r'\\sin', 'sin', latex_expr)
        latex_expr = re.sub(r'\\cos', 'cos', latex_expr)
        latex_expr = re.sub(r'\\tan', 'tan', latex_expr)
        latex_expr = re.sub(r'\\sec', 'sec', latex_expr)
        latex_expr = re.sub(r'\\csc', 'csc', latex_expr)
        latex_expr = re.sub(r'\\cot', 'cot', latex_expr)
        
        # Handle logarithms
        latex_expr = re.sub(r'\\ln', 'ln', latex_expr)
        latex_expr = re.sub(r'\\log', 'log', latex_expr)
        
        # Handle other functions
        latex_expr = re.sub(r'\\exp', 'exp', latex_expr)
        
        # Handle constants
        latex_expr = re.sub(r'\\pi', 'pi', latex_expr)
        latex_expr = re.sub(r'\\infty', 'infinity', latex_expr)
        
        # Convert LaTeX to SymPy-compatible format
        # Handle fractions
        latex_expr = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', latex_expr)
        
        # Handle superscripts with braces
        latex_expr = re.sub(r'\^?\{([^}]+)\}', r'^(\1)', latex_expr)
        # Handle simple superscripts
        latex_expr = re.sub(r'\^([a-zA-Z0-9])', r'^\1', latex_expr)
        
        # Handle square roots
        latex_expr = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', latex_expr)
        latex_expr = re.sub(r'\\sqrt\[([^]]+)\]\{([^}]+)\}', r'(\2)^(1/\1)', latex_expr)
        
        # Handle multiplication
        latex_expr = re.sub(r'\\cdot', '*', latex_expr)
        latex_expr = re.sub(r'\\times', '*', latex_expr)
        
        # Remove any remaining backslashes and braces for simple expressions
        latex_expr = re.sub(r'\\([a-zA-Z]+)', r'\1', latex_expr)
        latex_expr = latex_expr.replace('{', '').replace('}', '')
        
        print(f"Converted to raw expression: '{latex_expr}'")  # Debug
        return latex_expr
    
    def set_latex(self, latex):
        """Set the LaTeX content"""
        self.web_view.page().runJavaScript(f"setLatex('{latex}');")
    
    def clear(self):
        """Clear the content"""
        self.web_view.page().runJavaScript("clear();")
    
    def stop_timer(self):
        """Stop the update timer when widget is destroyed"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

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
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        brush = QBrush(QColor("#252525"))
        rect = QRectF(0, 0, self.width(), self.height())
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)

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
        button_font = QFont("Arial", 16, QFont.Bold)
        button_font.setStyleHint(QFont.SansSerif, QFont.PreferAntialias)
        self.home_button.setFont(button_font)
        self.home_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #353535;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 8px 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.home_button.adjustSize()
        self.home_button.setMinimumWidth(80)
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

        # Animate initial elements
        QTimer.singleShot(100, self.animate_initial_elements)

    def animate_initial_elements(self):
        """Animate initial UI elements on startup"""
        elements = [self.home_button]
        
        # Find dropdown elements
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and item.layout():
                for j in range(item.layout().count()):
                    sub_item = item.layout().itemAt(j)
                    if sub_item and sub_item.widget():
                        elements.append(sub_item.widget())
        
        # Add integration container
        elements.append(self.integration_container)
        
        animations = []
        for i, element in enumerate(elements):
            # Set up starting position
            original_pos = element.pos()
            start_pos = QPoint(original_pos.x() - 200, original_pos.y())
            element.move(start_pos)
            
            # Set up opacity effect
            opacity_effect = QGraphicsOpacityEffect()
            element.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(0)
            
            # Create position animation
            pos_anim = QPropertyAnimation(element, b"pos")
            pos_anim.setDuration(700)
            pos_anim.setStartValue(start_pos)
            pos_anim.setEndValue(original_pos)
            pos_anim.setEasingCurve(QEasingCurve.OutQuart)
            
            # Create opacity animation
            opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
            opacity_anim.setDuration(700)
            opacity_anim.setStartValue(0)
            opacity_anim.setEndValue(1)
            opacity_anim.setEasingCurve(QEasingCurve.OutQuart)
            
            # Group animations
            group = QParallelAnimationGroup()
            group.addAnimation(pos_anim)
            group.addAnimation(opacity_anim)
            
            # Start with delay
            QTimer.singleShot(i * 120, group.start)
            animations.append(group)
        
        self.current_animations.extend(animations)

    def setup_dropdown(self):
        # Dropdown layout
        dropdown_layout = QHBoxLayout()
        dropdown_layout.setSpacing(10)
        
        type_label = QLabel("Integration Type:", self)
        type_font = QFont("Arial", 24, QFont.Bold)
        type_font.setStyleHint(QFont.SansSerif, QFont.PreferAntialias)
        type_label.setFont(type_font)
        type_label.setStyleSheet("color: white; background: transparent;")
        
        self.type_combo = QComboBox(self)
        combo_font = QFont("Arial", 20, QFont.Bold)
        combo_font.setStyleHint(QFont.SansSerif, QFont.PreferAntialias)
        self.type_combo.setFont(combo_font)
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
                border-radius: 8px;
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
        self.current_animations.clear()
        
        while self.integration_layout.count():
            child = self.integration_layout.takeAt(0)
            if child.widget():
                child.widget().setGraphicsEffect(None)
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())
        
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
        message_font = QFont("Arial", 28, QFont.Bold)
        message_font.setStyleHint(QFont.SansSerif, QFont.PreferAntialias)
        message_label.setFont(message_font)
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
        integral_font = QFont("Times New Roman", 48, QFont.Bold)
        integral_font.setStyleHint(QFont.Times, QFont.PreferAntialias)
        integral_symbol.setFont(integral_font)
        integral_symbol.setStyleSheet("color: white; background: transparent;")
        
        # Function input with MathQuill
        self.function_input = MathQuillWidget(self.integration_container, "Enter function (e.g., x^2, sin(x), e^x)")
        self.function_input.setFixedWidth(350)
        self.function_input.mathChanged.connect(self.calculate_indefinite_integral)
        
        # dx label
        dx_label = QLabel("dx")
        dx_font = QFont("Times New Roman", 24, QFont.Bold)
        dx_font.setStyleHint(QFont.Times, QFont.PreferAntialias)
        dx_label.setFont(dx_font)
        dx_label.setStyleSheet("color: white; background: transparent;")
        
        integral_layout.addWidget(integral_symbol)
        integral_layout.addWidget(self.function_input)
        integral_layout.addWidget(dx_label)
        
        self.integration_layout.addLayout(integral_layout)
        
        # Results area
        self.results_widget = QWidget()
        self.results_widget.setStyleSheet("background: transparent;")
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.results_layout.setSpacing(20)
        
        # Antiderivative result using math display
        self.antiderivative_display = MathDisplayWidget()
        self.antiderivative_display.setFixedHeight(80)
        self.antiderivative_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.results_layout.addSpacing(40)
        self.results_layout.addWidget(self.antiderivative_display)
        
        # Method label
        self.method_label = QLabel("")
        method_font = QFont("Arial", 16, QFont.Bold)
        method_font.setStyleHint(QFont.SansSerif, QFont.PreferAntialias)
        self.method_label.setFont(method_font)
        self.method_label.setStyleSheet("""
            color: #87CEEB; 
            background: transparent; 
            margin: 10px;
            border-radius: 8px;
            padding: 8px;
        """)
        self.method_label.setAlignment(Qt.AlignCenter)
        self.method_label.setWordWrap(True)
        
        self.results_layout.addWidget(self.method_label)
        self.integration_layout.addWidget(self.results_widget)
        
        # Animate elements individually
        QTimer.singleShot(50, lambda: self.animate_integral_elements([integral_symbol, self.function_input, dx_label, self.results_widget]))

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
        lower_font = QFont("Arial", 16, QFont.Bold)
        lower_font.setStyleHint(QFont.SansSerif, QFont.PreferAntialias)
        lower_label.setFont(lower_font)
        lower_label.setStyleSheet("color: white; background: transparent;")
        self.lower_bound_input = QLineEdit()
        bounds_font = QFont("Arial", 16)
        bounds_font.setStyleHint(QFont.SansSerif, QFont.PreferAntialias)
        self.lower_bound_input.setFont(bounds_font)
        self.lower_bound_input.setStyleSheet("""
            QLineEdit {
                color: white;
                background-color: #353535;
                border: 1px solid #555;
                border-radius: 8px;
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
        upper_font = QFont("Arial", 16, QFont.Bold)
        upper_font.setStyleHint(QFont.SansSerif, QFont.PreferAntialias)
        upper_label.setFont(upper_font)
        upper_label.setStyleSheet("color: white; background: transparent;")
        self.upper_bound_input = QLineEdit()
        self.upper_bound_input.setFont(bounds_font)
        self.upper_bound_input.setStyleSheet("""
            QLineEdit {
                color: white;
                background-color: #353535;
                border: 1px solid #555;
                border-radius: 8px;
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
        integral_font = QFont("Times New Roman", 48, QFont.Bold)
        integral_font.setStyleHint(QFont.Times, QFont.PreferAntialias)
        integral_symbol.setFont(integral_font)
        integral_symbol.setStyleSheet("color: white; background: transparent;")
        
        # Function input with MathQuill
        self.definite_function_input = MathQuillWidget(self.integration_container, "Enter function (e.g., x^2, sin(x), e^x)")
        self.definite_function_input.setFixedWidth(350)
        self.definite_function_input.mathChanged.connect(self.calculate_definite_integral)
        
        # dx label
        dx_label = QLabel("dx")
        dx_font = QFont("Times New Roman", 24, QFont.Bold)
        dx_font.setStyleHint(QFont.Times, QFont.PreferAntialias)
        dx_label.setFont(dx_font)
        dx_label.setStyleSheet("color: white; background: transparent;")
        
        main_integral_layout.addWidget(integral_symbol)
        main_integral_layout.addWidget(self.definite_function_input)
        main_integral_layout.addWidget(dx_label)
        
        integral_layout.addLayout(main_integral_layout)
        self.integration_layout.addLayout(integral_layout)
        
        # Results area for definite integration
        self.definite_results_widget = QWidget()
        self.definite_results_widget.setStyleSheet("background: transparent;")
        self.definite_results_layout = QVBoxLayout(self.definite_results_widget)
        self.definite_results_layout.setAlignment(Qt.AlignTop)
        self.definite_results_layout.setSpacing(20)
        
        # Definite integral result using math display
        self.definite_result_display = MathDisplayWidget()
        self.definite_result_display.setFixedHeight(80)
        self.definite_result_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.definite_results_layout.addSpacing(40)
        self.definite_results_layout.addWidget(self.definite_result_display)
        
        # Method label for definite
        self.definite_method_label = QLabel("")
        method_font = QFont("Arial", 16, QFont.Bold)
        method_font.setStyleHint(QFont.SansSerif, QFont.PreferAntialias)
        self.definite_method_label.setFont(method_font)
        self.definite_method_label.setStyleSheet("""
            color: #87CEEB; 
            background: transparent; 
            margin: 10px;
            border-radius: 8px;
            padding: 8px;
        """)
        self.definite_method_label.setAlignment(Qt.AlignCenter)
        self.definite_method_label.setWordWrap(True)
        
        self.definite_results_layout.addWidget(self.definite_method_label)
        self.integration_layout.addWidget(self.definite_results_widget)
        
        # Animate bounds first, then integral elements
        bounds_elements = [lower_label, self.lower_bound_input, upper_label, self.upper_bound_input]
        QTimer.singleShot(50, lambda: self.animate_integral_elements(bounds_elements))
        QTimer.singleShot(300, lambda: self.animate_integral_elements([integral_symbol, self.definite_function_input, dx_label, self.definite_results_widget]))

    def animate_integral_elements(self, elements):
        """Animate integral elements individually"""
        animations = []
        
        for i, element in enumerate(elements):
            # Set up starting position
            original_pos = element.pos()
            start_pos = QPoint(original_pos.x() - 200, original_pos.y())
            element.move(start_pos)
            
            # Set up opacity effect
            opacity_effect = QGraphicsOpacityEffect()
            element.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(0)
            
            # Create position animation
            pos_anim = QPropertyAnimation(element, b"pos")
            pos_anim.setDuration(700)
            pos_anim.setStartValue(start_pos)
            pos_anim.setEndValue(original_pos)
            pos_anim.setEasingCurve(QEasingCurve.OutQuart)
            
            # Create opacity animation
            opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
            opacity_anim.setDuration(700)
            opacity_anim.setStartValue(0)
            opacity_anim.setEndValue(1)
            opacity_anim.setEasingCurve(QEasingCurve.OutQuart)
            
            # Group animations
            group = QParallelAnimationGroup()
            group.addAnimation(pos_anim)
            group.addAnimation(opacity_anim)
            
            # Start with delay
            QTimer.singleShot(i * 120, group.start)
            animations.append(group)
        
        self.current_animations.extend(animations)

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
        self.current_animations.clear()
        
        widgets_to_animate = []
        for i in range(self.integration_layout.count()):
            item = self.integration_layout.itemAt(i)
            if item and item.widget():
                widgets_to_animate.append(item.widget())
        
        if not widgets_to_animate:
            show_method()
            return
        
        animations = []
        for widget in widgets_to_animate:
            widget.setGraphicsEffect(None)
            
            opacity_effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(1.0)
            
            fade_out = QPropertyAnimation(opacity_effect, b"opacity")
            fade_out.setDuration(200)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.InCubic)
            
            animations.append(fade_out)
            fade_out.start()
        
        self.current_animations = animations
        
        def on_fade_out_complete():
            self.clear_integration_content()
            show_method()
        
        if animations:
            animations[-1].finished.connect(on_fade_out_complete)

    def determine_integration_method(self, expr, result):
        """Determine the integration method used"""
        x = symbols('x')
        expr_str = str(expr)
        
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
            try:
                if expr.has(sp.Function):
                    return "Substitution Method"
                else:
                    return "Direct Integration"
            except Exception:
                return "Standard Integration"

    def parse_function(self, function_text):
        """Parse function text with support for both e^x and exp(x) notation and implicit multiplication"""
        if not function_text or not function_text.strip():
            raise ValueError("Empty function expression")
            
        function_text = self.add_implicit_multiplication_for_parsing(function_text)
        
        function_text_sympy = function_text.replace('^', '**')
        function_text_sympy = function_text_sympy.replace('ln', 'log')
        
        function_text_sympy = re.sub(r'\be\*\*\(([^)]+)\)', r'exp(\1)', function_text_sympy)
        function_text_sympy = re.sub(r'\be\*\*([a-zA-Z0-9_]+)', r'exp(\1)', function_text_sympy)
        
        if '(' in function_text_sympy and ')' not in function_text_sympy:
            raise ValueError("Unmatched parentheses")
        if ')' in function_text_sympy and '(' not in function_text_sympy:
            raise ValueError("Unmatched parentheses")
            
        return sympify(function_text_sympy)

    def add_implicit_multiplication_for_parsing(self, text):
        """Add explicit multiplication operators for implicit multiplication (for parsing only)"""
        text = text.replace(' ', '')
        
        text = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', text)
        text = re.sub(r'(\d)(sin|cos|tan|sec|csc|cot|ln|log|exp|sqrt)', r'\1*\2', text)
        text = re.sub(r'(\d)\(', r'\1*(', text)
        text = re.sub(r'([a-zA-Z])\(', r'\1*(', text)
        text = re.sub(r'\)([a-zA-Z])', r')*\1', text)
        text = re.sub(r'\)(\d)', r')*\1', text)
        text = re.sub(r'\)\(', r')*(', text)
        text = re.sub(r'\)(sin|cos|tan|sec|csc|cot|ln|log|exp|sqrt)', r')*\1', text)
        text = re.sub(r'([a-zA-Z])([a-zA-Z])(?![a-zA-Z])', r'\1*\2', text)
        text = re.sub(r'(sin|cos|tan|sec|csc|cot|ln|log|exp|sqrt)\(([^)]+)\)([a-zA-Z])', r'\1(\2)*\3', text)
        
        return text

    def calculate_indefinite_integral(self, latex_expr, plain_text):
        """Calculate and display indefinite integral"""
        try:
            function_text = self.function_input.get_raw_expression().strip()
            if not function_text or function_text.isspace():
                self.antiderivative_display.clear_display()
                self.method_label.setText("")
                return
            
            if '(' in function_text and ')' not in function_text:
                return
            if function_text.endswith('(') or function_text.endswith('^'):
                return
                
            x = symbols('x')
            expr = self.parse_function(function_text)
            result = integrate(expr, x)
            result = simplify(result)
            
            method = self.determine_integration_method(expr, result)
            
            result_latex = latex(result)
            result_latex = result_latex.replace('*', '\\cdot')
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
            
            if not function_text or function_text.isspace():
                self.definite_result_display.clear_display()
                self.definite_method_label.setText("")
                return
            
            if not lower_text or not upper_text:
                self.definite_result_display.clear_display()
                self.definite_method_label.setText("")
                return
            
            if '(' in function_text and ')' not in function_text:
                return
            if function_text.endswith('(') or function_text.endswith('^'):
                return
                
            x = symbols('x')
            expr = self.parse_function(function_text)
            lower_bound = sympify(lower_text)
            upper_bound = sympify(upper_text)
            
            result = integrate(expr, (x, lower_bound, upper_bound))
            result = simplify(result)
            
            method = self.determine_integration_method(expr, result)
            
            result_latex = latex(result)
            result_latex = result_latex.replace('*', '\\cdot')
            result_latex = re.sub(r'\\times', r'\\cdot', result_latex)
            
            self.definite_result_display.display_math(result_latex, color='#90EE90', fontsize=18)
            self.definite_method_label.setText(f"Method: {method}")
            
        except Exception as e:
            self.definite_result_display.display_math("Invalid \\ function, \\ bounds, \\ or \\ unable \\ to \\ integrate", color='#FF6B6B', fontsize=14)
            self.definite_method_label.setText("")

    def home_transition(self):
        """Transition back to home with animation"""
        anims = []
        widgets = []
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            w = item.widget() if item and item.widget() else None
            if w:
                widgets.append(w)
        widgets.append(self.home_button)
        
        for w in widgets:
            pos_anim = QPropertyAnimation(w, b"pos")
            pos_anim.setDuration(400)
            pos_anim.setEasingCurve(QEasingCurve.InCubic)
            pos_anim.setStartValue(w.pos())
            pos_anim.setEndValue(w.pos() + QPoint(400, 0))
            
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