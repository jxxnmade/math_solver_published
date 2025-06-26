import sys
import os
import math
import cmath
import numpy as np
from fractions import Fraction
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QComboBox, 
                             QListView, QLineEdit, QGraphicsOpacityEffect, QHBoxLayout, 
                             QScrollArea, QPushButton)
from PyQt5.QtGui import QPainter, QBrush, QColor, QFont, QIntValidator
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, QPoint, QTimer, QEasingCurve
import subprocess
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')

class GraphWidget(QWidget):
    """Widget to display polynomial graphs"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(facecolor='#000000')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.setStyleSheet("background: transparent;")
        
    def plot_linear(self, a, c):
        """Plot linear function y = ax + c"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#000000')
        
        # Set domain [-5, 5]
        x_vals = np.array([-5, 5])
        y_vals = a * x_vals + c
        
        # Set range based on y-values at endpoints
        if a > 0:
            y_min, y_max = y_vals[0], y_vals[1]  # y(-5), y(5)
        else:
            y_min, y_max = y_vals[1], y_vals[0]  # y(5), y(-5)
        
        # Plot the line
        ax.plot(x_vals, y_vals, color='white', linewidth=2)
        
        # Set limits to fill the square
        ax.set_xlim(-5, 5)
        ax.set_ylim(y_min, y_max)
        
        # Add axes
        ax.axhline(y=0, color='white', linewidth=0.5, alpha=0.7)
        ax.axvline(x=0, color='white', linewidth=0.5, alpha=0.7)
        
        # Style the plot
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white') 
        ax.spines['right'].set_color('white')
        ax.spines['left'].set_color('white')
        
        self.canvas.draw()
    
    def plot_polynomial(self, coefficients, degree):
        """Plot polynomial of degree 3 or higher"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#000000')
        
        # Create polynomial function
        def poly_func(x):
            result = 0
            for i, coeff in enumerate(coefficients):
                result += coeff * (x ** (degree - i))
            return result
        
        # Find critical points (local maxima and minima)
        # Take derivative
        derivative_coeffs = []
        for i in range(len(coefficients) - 1):
            power = degree - i
            derivative_coeffs.append(coefficients[i] * power)
        
        # Find roots of derivative (critical points)
        critical_points = []
        if len(derivative_coeffs) > 1:
            try:
                roots = np.roots(derivative_coeffs)
                for root in roots:
                    if np.isreal(root):
                        critical_points.append(float(root.real))
            except:
                pass
        
        # Evaluate function at critical points to find local min/max
        critical_values = []
        for cp in critical_points:
            critical_values.append(poly_func(cp))
        
        # Find global min and max from critical points
        if critical_values:
            local_min = min(critical_values)
            local_max = max(critical_values)
        else:
            # If no critical points, use a default range
            local_min, local_max = -10, 10
        
        # Add some padding to the y-range
        y_range = local_max - local_min
        if y_range < 1:
            y_range = 1
        padding = y_range * 0.1
        y_min = local_min - padding
        y_max = local_max + padding
        
        # Find x-bounds where function exceeds the local min/max range
        def find_x_bound(direction):
            """Find x where |f(x)| exceeds the local min/max range"""
            search_start = 0
            search_range = 1
            
            while search_range < 100:  # Prevent infinite loop
                if direction > 0:  # searching to the right
                    x_test = search_start + search_range
                else:  # searching to the left
                    x_test = search_start - search_range
                
                y_test = poly_func(x_test)
                
                # Check if y_test is outside the local min/max range
                if y_test < local_min or y_test > local_max:
                    return x_test
                
                search_range *= 1.5
            
            # Fallback
            return search_start + direction * 10
        
        # Find x bounds
        x_min = find_x_bound(-1)  # search left
        x_max = find_x_bound(1)   # search right
        
        # Ensure reasonable bounds
        x_min = max(x_min, -50)
        x_max = min(x_max, 50)
        
        # Generate x values for plotting
        x_vals = np.linspace(x_min, x_max, 1000)
        y_vals = [poly_func(x) for x in x_vals]
        
        # Plot the polynomial
        ax.plot(x_vals, y_vals, color='white', linewidth=2)
        
        # Set limits (2:1 ratio, bottom:top)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        
        # Add axes
        ax.axhline(y=0, color='white', linewidth=0.5, alpha=0.7)
        ax.axvline(x=0, color='white', linewidth=0.5, alpha=0.7)
        
        # Style the plot
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white') 
        ax.spines['right'].set_color('white')
        ax.spines['left'].set_color('white')
        
        self.canvas.draw()
    
    def show_development_message(self):
        """Show 'Still in development' message for quadratic functions"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#000000')
        
        ax.text(0.5, 0.5, 'Still in development', 
               horizontalalignment='center',
               verticalalignment='center',
               fontsize=24,
               color='red',
               weight='bold',
               transform=ax.transAxes)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        self.canvas.draw()
    
    def clear_graph(self):
        """Clear the graph"""
        self.figure.clear()
        self.canvas.draw()

class RoundedWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Polynomial Solver")
        self.setFixedSize(600, 900)  # Increased height for graph
        self.setAttribute(Qt.WA_TranslucentBackground)
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
        self.layout.setSpacing(10)

        # Position scroll area
        scroll_area.setGeometry(0, 0, self.width(), self.height())

        # Equation parts with adjusted exponent positioning
        self.equation_str = [
            ("a<sub style='font-size:22px; position:relative; left:2px;'>n</sub>", False),
            ("x<sup style='font-size:18px; position:relative; left:2px; bottom:18px;'>n</sup>", False),
            (" + ", False),
            ("a<sub style='font-size:22px; position:relative; left:2px;'>n-1</sub>", False),
            ("x<sup style='font-size:18px; position:relative; left:2px; bottom:18px;'>n-1</sup>", False),
            (" + ...", False)
        ]
        self.labels = []
        font = QFont("Times New Roman", 32)
        font.setStyleStrategy(QFont.PreferAntialias)

        # Equation container
        self.equation_container = QWidget(content_widget)
        self.equation_container.setAttribute(Qt.WA_TranslucentBackground)
        self.equation_container.setStyleSheet("background: transparent;")
        self.equation_container.setFixedHeight(60)

        # Custom label widths: 30px for a_n, x^n, and first +, 40px for a_{n-1}, x^{n-1}, and + ...
        label_widths = [30, 30, 30, 40, 40, 40]
        spacing = 0  # No additional spacing between labels
        total_width = sum(label_widths)  # 30 + 30 + 30 + 40 + 40 + 40 = 210

        for i, (part, _) in enumerate(self.equation_str):
            label = QLabel(self.equation_container)
            label.setText(f"<span style='color:white; font-family:\"Times New Roman\";'>{part}</span>")
            label.setFont(font)
            label.setTextFormat(Qt.RichText)
            label.setAttribute(Qt.WA_TranslucentBackground)
            label.setStyleSheet("background: transparent;")
            label.setFixedHeight(60)
            label.setFixedWidth(label_widths[i])
            label.setAlignment(Qt.AlignCenter)
            label.move(0, -50)
            label.show()
            self.labels.append(label)

        container_x = (600 - total_width) // 2  # Use window width
        container_y = 30
        self.equation_container.setFixedWidth(total_width)
        self.equation_container.move(container_x, container_y)

        x = 0
        for i, label in enumerate(self.labels):
            label.move(x, -50)
            x += label_widths[i] + spacing

        self.label_animations = []
        x = 0
        for i, label in enumerate(self.labels):
            start_pos = QPoint(x, -50)
            end_pos = QPoint(x, 0)
            anim = QPropertyAnimation(label, b"pos")
            anim.setDuration(400)
            anim.setStartValue(start_pos)
            anim.setEndValue(end_pos)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            self.label_animations.append(anim)
            x += label_widths[i] + spacing

        def start_label_anim(i):
            self.label_animations[i].start()
            # After last label animates in, show N= dropdown
            if i == len(self.label_animations) - 1:
                QTimer.singleShot(400, self.show_n_dropdown)

        for i in range(len(self.label_animations)):
            QTimer.singleShot(200 + i * 100, lambda i=i: start_label_anim(i))

        # Add equation container to layout
        self.layout.addWidget(self.equation_container, alignment=Qt.AlignCenter)

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

        def home_transition():
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

        self.home_button.clicked.connect(home_transition)

    def gcd(self, a, b):
        """Calculate greatest common divisor"""
        while b:
            a, b = b, a % b
        return a

    def format_fraction(self, numerator, denominator):
        """Format a fraction in simplest form"""
        if denominator == 0:
            return "undefined"
        if denominator == 1:
            return str(numerator)
        if denominator == -1:
            return str(-numerator)
        
        # Handle negative fractions
        if denominator < 0:
            numerator = -numerator
            denominator = -denominator
        
        # Simplify fraction
        gcd_val = self.gcd(abs(numerator), abs(denominator))
        numerator //= gcd_val
        denominator //= gcd_val
        
        if denominator == 1:
            return str(numerator)
        else:
            return f"{numerator}/{denominator}"

    def format_complex(self, root):
        """Format complex number with exact fractions"""
        if isinstance(root, (int, float, Fraction)):
            # Real number
            if isinstance(root, Fraction):
                return str(root)
            elif isinstance(root, (int, float)):
                if abs(root) < 1e-10:  # Effectively zero
                    return "0"
                elif isinstance(root, float):
                    # Force to fraction for all floating point numbers
                    frac = self.force_to_fraction(root)
                    return str(frac)
                else:
                    return str(root)
        
        elif isinstance(root, complex):
            real = root.real
            imag = root.imag
            
            # Handle real part - force to fraction if it's a float
            if isinstance(real, Fraction):
                real_str = str(real)
            elif abs(real) < 1e-10:  # Effectively zero
                real_str = "0"
            else:
                real_frac = self.force_to_fraction(real)
                real_str = str(real_frac)
            
            # Handle imaginary part - force to fraction if it's a float
            if abs(imag) < 1e-10:  # Effectively zero
                return real_str
            
            if isinstance(imag, Fraction):
                imag_frac = imag
            else:
                imag_frac = self.force_to_fraction(abs(imag))
            
            imag_str = str(imag_frac)
            
            # Format the complex number
            if abs(real) < 1e-10:  # Real part is effectively zero
                if abs(imag - 1) < 1e-10:
                    return "i"
                elif abs(imag + 1) < 1e-10:
                    return "-i"
                elif imag > 0:
                    return f"{imag_str}i" if imag_str != "1" else "i"
                else:
                    return f"-{imag_str}i" if imag_str != "1" else "-i"
            else:
                if abs(imag - 1) < 1e-10:
                    return f"{real_str} + i"
                elif abs(imag + 1) < 1e-10:
                    return f"{real_str} - i"
                elif imag > 0:
                    return f"{real_str} + {imag_str}i" if imag_str != "1" else f"{real_str} + i"
                else:
                    return f"{real_str} - {imag_str}i" if imag_str != "1" else f"{real_str} - i"
        
        return str(root)

    def sqrt_exact(self, n):
        """Return exact square root as (coefficient, radicand) or (value, 0) if perfect square"""
        if n < 0:
            return self.sqrt_exact(-n)[0], self.sqrt_exact(-n)[1], True  # Return (coeff, rad, is_imaginary)
        if n == 0:
            return 0, 0, False
        
        # Check if perfect square
        sqrt_n = int(n ** 0.5)
        if sqrt_n * sqrt_n == n:
            return sqrt_n, 0, False
        
        # Find largest perfect square factor
        coeff = 1
        radicand = n
        for i in range(2, int(n**0.5) + 1):
            while radicand % (i*i) == 0:
                coeff *= i
                radicand //= (i*i)
        
        return coeff, radicand, False

    def force_to_fraction(self, value, max_denominator=1000000):
        """Force a floating point value to a fraction, trying multiple strategies"""
        if isinstance(value, (Fraction, int)):
            return value
            
        # Strategy 1: Direct conversion with high precision
        frac1 = Fraction(value).limit_denominator(max_denominator)
        if abs(float(frac1) - value) < 1e-12:
            return frac1
            
        # Strategy 2: Round to remove floating point errors, then convert
        # Try different decimal places
        for decimals in range(15, 5, -1):
            rounded_val = round(value, decimals)
            frac2 = Fraction(rounded_val).limit_denominator(max_denominator)
            if abs(float(frac2) - value) < 1e-10:
                return frac2
        
        # Strategy 3: Try to detect if it's close to a rational number
        # Check if it's close to simple fractions like 1/3, 2/3, etc.
        for denom in range(1, 1000):
            for num in range(-denom*10, denom*10 + 1):
                test_frac = Fraction(num, denom)
                if abs(float(test_frac) - value) < 1e-10:
                    return test_frac
        
        # Strategy 4: If all else fails, force it to a fraction anyway
        return Fraction(value).limit_denominator(max_denominator)

    def solve_cubic(self, a, b, c, d):
        """Solve cubic equation ax³ + bx² + cx + d = 0"""
        if a == 0:
            return []
        
        # Use numpy for reliable root finding
        coeffs = [a, b, c, d]
        roots = np.roots(coeffs)
        
        # Process roots to handle floating point precision issues
        processed_roots = []
        for root in roots:
            if np.isreal(root):
                real_val = float(root.real)
                # Force to fraction using aggressive strategy
                frac = self.force_to_fraction(real_val)
                processed_roots.append(frac)
            else:
                # Handle complex roots
                real_part = float(root.real)
                imag_part = float(root.imag)
                
                # Force both parts to fractions
                real_frac = self.force_to_fraction(real_part)
                imag_frac = self.force_to_fraction(imag_part)
                
                processed_roots.append(complex(real_frac, imag_frac))
        
        return processed_roots

    def solve_quartic(self, a, b, c, d, e):
        """Solve quartic equation ax⁴ + bx³ + cx² + dx + e = 0"""
        if a == 0:
            return []
        
        # Use numpy for reliable root finding
        coeffs = [a, b, c, d, e]
        roots = np.roots(coeffs)
        
        # Process roots to handle floating point precision issues
        processed_roots = []
        for root in roots:
            if np.isreal(root):
                real_val = float(root.real)
                # Force to fraction using aggressive strategy
                frac = self.force_to_fraction(real_val)
                processed_roots.append(frac)
            else:
                # Handle complex roots
                real_part = float(root.real)
                imag_part = float(root.imag)
                
                # Force both parts to fractions
                real_frac = self.force_to_fraction(real_part)
                imag_frac = self.force_to_fraction(imag_part)
                
                processed_roots.append(complex(real_frac, imag_frac))
        
        return processed_roots
    def show_n_dropdown(self):
       # N= label and dropdown in a horizontal layout
       n_layout = QHBoxLayout()
       n_layout.setSpacing(10)
       
       n_label = QLabel("N =", self)
       n_font = QFont("Arial", 24, QFont.Bold)
       n_label.setFont(n_font)
       n_label.setStyleSheet("color: white; background: transparent;")
       n_label.adjustSize()

       self.combo = QComboBox(self)
       combo_font = QFont("Arial", 20, QFont.Bold)
       self.combo.setFont(combo_font)
       self.combo.setStyleSheet("""
           QComboBox {
               color: white;
               background-color: #353535;
               border: 1px solid #555;
               border-radius: 8px;
               padding: 2px 18px 2px 8px;
               min-width: 6em;
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
       self.combo.addItems(["", "1", "2", "3", "4"])
       self.combo.setFixedWidth(60)

       n_layout.addWidget(n_label)
       n_layout.addWidget(self.combo)
       n_layout.addStretch()

       # Add N= layout to main layout
       self.layout.addLayout(n_layout)

       # Fade in for N= label
       n_opacity = QGraphicsOpacityEffect(n_label)
       n_label.setGraphicsEffect(n_opacity)
       n_opacity.setOpacity(0)
       self.n_anim = QPropertyAnimation(n_opacity, b"opacity")
       self.n_anim.setDuration(200)
       self.n_anim.setStartValue(0)
       self.n_anim.setEndValue(1)
       self.n_anim.start()

       # Fade in for dropdown
       combo_opacity = QGraphicsOpacityEffect(self.combo)
       self.combo.setGraphicsEffect(combo_opacity)
       combo_opacity.setOpacity(0)
       self.combo_anim = QPropertyAnimation(combo_opacity, b"opacity")
       self.combo_anim.setDuration(200)
       self.combo_anim.setStartValue(0)
       self.combo_anim.setEndValue(1)
       self.combo_anim.start()

       # Initialize input field variables
       self.input_fields = {}
       self.results_label = None
       self.graph_widget = None
       self.combo.currentTextChanged.connect(self.handle_n_selection)

       # Add stretch to push content to top
       self.layout.addStretch()

    def clear_input_fields(self):
       """Clear all existing input fields"""
       for field in self.input_fields.values():
           if field['label']:
               field['label'].deleteLater()
           if field['input']:
               field['input'].deleteLater()
       self.input_fields.clear()
       
       if self.results_label:
           self.results_label.deleteLater()
           self.results_label = None
           
       if self.graph_widget:
           self.graph_widget.deleteLater()
           self.graph_widget = None

    def create_input_field(self, label_text, field_name):
       """Create a label and input field pair"""
       layout = QHBoxLayout()
       layout.setSpacing(10)
       
       label = QLabel(label_text, self)
       font = QFont("Arial", 24, QFont.Bold)
       label.setFont(font)
       label.setStyleSheet("color: white; background: transparent;")
       label.setTextFormat(Qt.RichText)
       label.adjustSize()

       input_field = QLineEdit(self)
       input_field.setFont(QFont("Arial", 20, QFont.Bold))
       input_field.setStyleSheet("""
           QLineEdit {
               color: white;
               background-color: #353535;
               border: 1px solid #555;
               border-radius: 8px;
               padding: 2px 8px;
               min-width: 6em;
           }
       """)
       input_field.setFixedWidth(80)
       input_field.setMaxLength(6)
       validator = QIntValidator(input_field)
       validator.setRange(-9999, 9999)
       input_field.setValidator(validator)

       layout.addWidget(label)
       layout.addWidget(input_field)
       layout.addStretch()

       self.layout.addLayout(layout)
       
       self.input_fields[field_name] = {
           'label': label,
           'input': input_field,
           'layout': layout
       }
       
       return input_field

    def create_results_label(self):
       """Create the results display label"""
       self.results_label = QLabel("", self)
       self.results_label.setFont(QFont("Arial", 16, QFont.Bold))
       self.results_label.setStyleSheet("color: white; background: transparent;")
       self.results_label.setAlignment(Qt.AlignLeft)
       self.results_label.setTextFormat(Qt.RichText)
       self.results_label.setWordWrap(True)
       self.layout.addWidget(self.results_label)
       
       # Create and add graph widget after results
       self.graph_widget = GraphWidget()
       self.graph_widget.setFixedHeight(200)  # 2:1 ratio, so width will be 400
       self.graph_widget.setFixedWidth(400)
       self.layout.addWidget(self.graph_widget, alignment=Qt.AlignCenter)

    def handle_n_selection(self, value):
       # Clear previous input fields and results
       self.clear_input_fields()

       if value == "1":
           # Linear: ax + c = 0
           a_input = self.create_input_field("a =", "a")
           c_input = self.create_input_field("c =", "c")
           self.create_results_label()

           # Connect to calculation function
           a_input.textChanged.connect(self.calculate_results_n1)
           c_input.textChanged.connect(self.calculate_results_n1)

       elif value == "2":
           # Quadratic: a₂x² + a₁x + c = 0
           a2_input = self.create_input_field("a<sub>2</sub> =", "a2")
           a1_input = self.create_input_field("a<sub>1</sub> =", "a1")
           c_input = self.create_input_field("c =", "c")
           self.create_results_label()

           # Connect to calculation function
           a2_input.textChanged.connect(self.calculate_results_n2)
           a1_input.textChanged.connect(self.calculate_results_n2)
           c_input.textChanged.connect(self.calculate_results_n2)

       elif value == "3":
           # Cubic: a₃x³ + a₂x² + a₁x + c = 0
           a3_input = self.create_input_field("a<sub>3</sub> =", "a3")
           a2_input = self.create_input_field("a<sub>2</sub> =", "a2")
           a1_input = self.create_input_field("a<sub>1</sub> =", "a1")
           c_input = self.create_input_field("c =", "c")
           self.create_results_label()

           # Connect to calculation function
           a3_input.textChanged.connect(self.calculate_results_n3)
           a2_input.textChanged.connect(self.calculate_results_n3)
           a1_input.textChanged.connect(self.calculate_results_n3)
           c_input.textChanged.connect(self.calculate_results_n3)

       elif value == "4":
           # Quartic: a₄x⁴ + a₃x³ + a₂x² + a₁x + c = 0
           a4_input = self.create_input_field("a<sub>4</sub> =", "a4")
           a3_input = self.create_input_field("a<sub>3</sub> =", "a3")
           a2_input = self.create_input_field("a<sub>2</sub> =", "a2")
           a1_input = self.create_input_field("a<sub>1</sub> =", "a1")
           c_input = self.create_input_field("c =", "c")
           self.create_results_label()

           # Connect to calculation function
           a4_input.textChanged.connect(self.calculate_results_n4)
           a3_input.textChanged.connect(self.calculate_results_n4)
           a2_input.textChanged.connect(self.calculate_results_n4)
           a1_input.textChanged.connect(self.calculate_results_n4)
           c_input.textChanged.connect(self.calculate_results_n4)

    def get_input_value(self, field_name):
       """Get integer value from input field, return None if empty or invalid"""
       if field_name in self.input_fields and self.input_fields[field_name]['input']:
           text = self.input_fields[field_name]['input'].text()
           if text:
               try:
                   return int(text)
               except ValueError:
                   return None
       return None

    def all_fields_filled(self, field_names):
       """Check if all specified fields have valid input"""
       for field_name in field_names:
           if self.get_input_value(field_name) is None:
               return False
       return True

    def calculate_results_n1(self):
       # Linear equation: ax + c = 0
       if self.all_fields_filled(['a', 'c']):
           a = self.get_input_value('a')
           c = self.get_input_value('c')
           
           results = []
           
           if a == 0:
               results.append("<b>Error:</b> Leading coefficient cannot be zero")
               if self.graph_widget:
                   self.graph_widget.clear_graph()
           else:
               # Function format
               results.append(f"<b>Function:</b> f(x) = {a}x + {c}")
               
               # X-intercept (root) - using enhanced fraction formatting
               root_value = Fraction(-c, a)
               x_intercept_formatted = self.format_complex(root_value)
               results.append(f"<b>X-intercept:</b> ({x_intercept_formatted}, 0)")
               
               # Y-intercept
               results.append(f"<b>Y-intercept:</b> (0, {c})")
               
               # End behavior
               results.append("<b>End Behavior:</b>")
               if a > 0:
                   results.append("&nbsp;&nbsp;lim<sub>x→+∞</sub> f(x) = +∞")
                   results.append("&nbsp;&nbsp;lim<sub>x→-∞</sub> f(x) = -∞")
               else:
                   results.append("&nbsp;&nbsp;lim<sub>x→+∞</sub> f(x) = -∞")
                   results.append("&nbsp;&nbsp;lim<sub>x→-∞</sub> f(x) = +∞")
               
               # Plot the linear function
               if self.graph_widget:
                   self.graph_widget.plot_linear(a, c)

       else:
           results = []
           if self.graph_widget:
               self.graph_widget.clear_graph()

       # Update results label
       if self.results_label:
           self.results_label.setText("<br>".join(results))
           self.results_label.setVisible(True)
           self.results_label.update()

       self.update()

    def calculate_results_n2(self):
       # Quadratic equation: a₂x² + a₁x + c = 0
       if self.all_fields_filled(['a2', 'a1', 'c']):
           a2 = self.get_input_value('a2')
           a1 = self.get_input_value('a1')
           c = self.get_input_value('c')
           
           results = []
           
           if a2 == 0:
               results.append("<b>Error:</b> Leading coefficient cannot be zero")
               if self.graph_widget:
                   self.graph_widget.clear_graph()
           else:
               # Function format
               a1_str = f" + {a1}x" if a1 > 0 else f" - {abs(a1)}x" if a1 < 0 else ""
               c_str = f" + {c}" if c > 0 else f" - {abs(c)}" if c < 0 else ""
               results.append(f"<b>Function:</b> f(x) = {a2}x²{a1_str}{c_str}")
               
               # Calculate discriminant for quadratic formula
               discriminant = a1**2 - 4*a2*c
               
               results.append("<b>X-intercepts (Roots):</b>")
               if discriminant > 0:
                   # Two real solutions - use enhanced formatting
                   coeff, rad, is_imag = self.sqrt_exact(discriminant)
                   if rad == 0:  # Perfect square discriminant
                       x1_frac = Fraction(-a1 + coeff, 2 * a2)
                       x2_frac = Fraction(-a1 - coeff, 2 * a2)
                       
                       x1_formatted = self.format_complex(x1_frac)
                       x2_formatted = self.format_complex(x2_frac)
                       results.append(f"&nbsp;&nbsp;x₁ = {x1_formatted}")
                       results.append(f"&nbsp;&nbsp;x₂ = {x2_formatted}")
                   else:  # Irrational roots with exact radical form
                       den = 2 * a2
                       numerator_part = Fraction(-a1, den)
                       
                       if coeff == 1:
                           sqrt_part = f"√{rad}"
                       else:
                           sqrt_part = f"{coeff}√{rad}"
                       
                       # Format the radical expressions
                       if den == 1:
                           if numerator_part == 0:
                               results.append(f"&nbsp;&nbsp;x₁ = {sqrt_part}")
                               results.append(f"&nbsp;&nbsp;x₂ = -{sqrt_part}")
                           else:
                               results.append(f"&nbsp;&nbsp;x₁ = {numerator_part} + {sqrt_part}")
                               results.append(f"&nbsp;&nbsp;x₂ = {numerator_part} - {sqrt_part}")
                       else:
                           if numerator_part == 0:
                               results.append(f"&nbsp;&nbsp;x₁ = {sqrt_part}/{den}")
                               results.append(f"&nbsp;&nbsp;x₂ = -{sqrt_part}/{den}")
                           else:
                               results.append(f"&nbsp;&nbsp;x₁ = ({numerator_part} + {sqrt_part})/{den if den != 1 else ''}")
                               results.append(f"&nbsp;&nbsp;x₂ = ({numerator_part} - {sqrt_part})/{den if den != 1 else ''}")
               
               elif discriminant == 0:
                   # One solution (repeated root)
                   x_frac = Fraction(-a1, 2 * a2)
                   x_formatted = self.format_complex(x_frac)
                   results.append(f"&nbsp;&nbsp;x = {x_formatted} (repeated root)")
               
               else:  # discriminant < 0
                   # Complex solutions - use enhanced formatting
                   coeff, rad, is_imag = self.sqrt_exact(-discriminant)
                   den = 2 * a2
                   real_part = Fraction(-a1, den)
                   
                   # Create complex numbers with fractions
                   if coeff == 1:
                       imag_coefficient = Fraction(1, den) if den != 1 else 1
                   else:
                       imag_coefficient = Fraction(coeff, den) if den != 1 else coeff
                   
                   if rad == 1:
                       # Pure imaginary with coefficient
                       root1 = complex(real_part, imag_coefficient)
                       root2 = complex(real_part, -imag_coefficient)
                   else:
                       # Need to display as a√b form
                       if den == 1:
                           if real_part == 0:
                               if coeff == 1:
                                   results.append(f"&nbsp;&nbsp;x₁ = i√{rad}")
                                   results.append(f"&nbsp;&nbsp;x₂ = -i√{rad}")
                               else:
                                   results.append(f"&nbsp;&nbsp;x₁ = {coeff}i√{rad}")
                                   results.append(f"&nbsp;&nbsp;x₂ = -{coeff}i√{rad}")
                           else:
                               if coeff == 1:
                                   results.append(f"&nbsp;&nbsp;x₁ = {real_part} + i√{rad}")
                                   results.append(f"&nbsp;&nbsp;x₂ = {real_part} - i√{rad}")
                               else:
                                   results.append(f"&nbsp;&nbsp;x₁ = {real_part} + {coeff}i√{rad}")
                                   results.append(f"&nbsp;&nbsp;x₂ = {real_part} - {coeff}i√{rad}")
                       else:
                           if real_part == 0:
                               if coeff == 1:
                                   results.append(f"&nbsp;&nbsp;x₁ = i√{rad}/{den}")
                                   results.append(f"&nbsp;&nbsp;x₂ = -i√{rad}/{den}")
                               else:
                                   results.append(f"&nbsp;&nbsp;x₁ = {coeff}i√{rad}/{den}")
                                   results.append(f"&nbsp;&nbsp;x₂ = -{coeff}i√{rad}/{den}")
                           else:
                               if coeff == 1:
                                   results.append(f"&nbsp;&nbsp;x₁ = ({real_part} + i√{rad})/{den}")
                                   results.append(f"&nbsp;&nbsp;x₂ = ({real_part} - i√{rad})/{den}")
                               else:
                                   results.append(f"&nbsp;&nbsp;x₁ = ({real_part} + {coeff}i√{rad})/{den}")
                                   results.append(f"&nbsp;&nbsp;x₂ = ({real_part} - {coeff}i√{rad})/{den}")

               # Y-intercept
               results.append(f"<b>Y-intercept:</b> (0, {c})")

               # End behavior
               results.append("<b>End Behavior:</b>")
               if a2 > 0:
                   results.append("&nbsp;&nbsp;lim<sub>x→±∞</sub> f(x) = +∞")
               else:
                   results.append("&nbsp;&nbsp;lim<sub>x→±∞</sub> f(x) = -∞")

               # Show "Still in development" message for quadratic graph
               if self.graph_widget:
                   self.graph_widget.show_development_message()

       else:
           results = []
           if self.graph_widget:
               self.graph_widget.clear_graph()

       # Update results label
       if self.results_label:
           self.results_label.setText("<br>".join(results))
           self.results_label.setVisible(True)
           self.results_label.update()

       self.update()

    def calculate_results_n3(self):
       # Cubic equation: a₃x³ + a₂x² + a₁x + c = 0
       if self.all_fields_filled(['a3', 'a2', 'a1', 'c']):
           a3 = self.get_input_value('a3')
           a2 = self.get_input_value('a2')
           a1 = self.get_input_value('a1')
           c = self.get_input_value('c')
           
           results = []
           
           if a3 == 0:
               results.append("<b>Error:</b> Leading coefficient cannot be zero")
               if self.graph_widget:
                   self.graph_widget.clear_graph()
           else:
               # Function format
               a2_str = f" + {a2}x²" if a2 > 0 else f" - {abs(a2)}x²" if a2 < 0 else ""
               a1_str = f" + {a1}x" if a1 > 0 else f" - {abs(a1)}x" if a1 < 0 else ""
               c_str = f" + {c}" if c > 0 else f" - {abs(c)}" if c < 0 else ""
               results.append(f"<b>Function:</b> f(x) = {a3}x³{a2_str}{a1_str}{c_str}")
               
               # Solve cubic equation
               try:
                   roots = self.solve_cubic(a3, a2, a1, c)
                   
                   results.append("<b>X-intercepts (Roots):</b>")
                   for i, root in enumerate(roots):
                       formatted_root = self.format_complex(root)
                       results.append(f"&nbsp;&nbsp;x{i+1} = {formatted_root}")
               
               except Exception as e:
                   results.append("<b>Roots:</b> Unable to calculate (numerical method failed)")

               # Y-intercept
               results.append(f"<b>Y-intercept:</b> (0, {c})")

               # End behavior with limit notation
               results.append("<b>End Behavior:</b>")
               if a3 > 0:
                   results.append("&nbsp;&nbsp;lim<sub>x→+∞</sub> f(x) = +∞")
                   results.append("&nbsp;&nbsp;lim<sub>x→-∞</sub> f(x) = -∞")
               else:
                   results.append("&nbsp;&nbsp;lim<sub>x→+∞</sub> f(x) = -∞")
                   results.append("&nbsp;&nbsp;lim<sub>x→-∞</sub> f(x) = +∞")

               # Plot the cubic function
               if self.graph_widget:
                   coefficients = [a3, a2, a1, c]
                   self.graph_widget.plot_polynomial(coefficients, 3)

       else:
           results = []
           if self.graph_widget:
               self.graph_widget.clear_graph()

       # Update results label
       if self.results_label:
           self.results_label.setText("<br>".join(results))
           self.results_label.setVisible(True)
           self.results_label.update()

       self.update()

    def calculate_results_n4(self):
       # Quartic equation: a₄x⁴ + a₃x³ + a₂x² + a₁x + c = 0
       if self.all_fields_filled(['a4', 'a3', 'a2', 'a1', 'c']):
           a4 = self.get_input_value('a4')
           a3 = self.get_input_value('a3')
           a2 = self.get_input_value('a2')
           a1 = self.get_input_value('a1')
           c = self.get_input_value('c')
           
           results = []
           
           if a4 == 0:
               results.append("<b>Error:</b> Leading coefficient cannot be zero")
               if self.graph_widget:
                   self.graph_widget.clear_graph()
           else:
               # Function format
               a3_str = f" + {a3}x³" if a3 > 0 else f" - {abs(a3)}x³" if a3 < 0 else ""
               a2_str = f" + {a2}x²" if a2 > 0 else f" - {abs(a2)}x²" if a2 < 0 else ""
               a1_str = f" + {a1}x" if a1 > 0 else f" - {abs(a1)}x" if a1 < 0 else ""
               c_str = f" + {c}" if c > 0 else f" - {abs(c)}" if c < 0 else ""
               results.append(f"<b>Function:</b> f(x) = {a4}x⁴{a3_str}{a2_str}{a1_str}{c_str}")
               
               # Solve quartic equation
               try:
                   roots = self.solve_quartic(a4, a3, a2, a1, c)
                   
                   results.append("<b>X-intercepts (Roots):</b>")
                   for i, root in enumerate(roots):
                       formatted_root = self.format_complex(root)
                       results.append(f"&nbsp;&nbsp;x{i+1} = {formatted_root}")
               
               except Exception as e:
                   results.append("<b>Roots:</b> Unable to calculate (numerical method failed)")

               # Y-intercept
               results.append(f"<b>Y-intercept:</b> (0, {c})")

               # End behavior with limit notation
               results.append("<b>End Behavior:</b>")
               if a4 > 0:
                   results.append("&nbsp;&nbsp;lim<sub>x→±∞</sub> f(x) = +∞")
               else:
                   results.append("&nbsp;&nbsp;lim<sub>x→±∞</sub> f(x) = -∞")

               # Plot the quartic function
               if self.graph_widget:
                   coefficients = [a4, a3, a2, a1, c]
                   self.graph_widget.plot_polynomial(coefficients, 4)

       else:
           results = []
           if self.graph_widget:
               self.graph_widget.clear_graph()

       # Update results label
       if self.results_label:
           self.results_label.setText("<br>".join(results))
           self.results_label.setVisible(True)
           self.results_label.update()

       self.update()

if __name__ == "__main__":
   app = QApplication(sys.argv)
   window = RoundedWindow()
   window.show()
   sys.exit(app.exec_())