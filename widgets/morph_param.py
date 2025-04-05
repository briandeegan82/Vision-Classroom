import cv2
import numpy as np
from PyQt5.QtWidgets import (QLabel, QSlider, QCheckBox, QGroupBox, 
                            QHBoxLayout, QVBoxLayout, QComboBox, QRadioButton)
from PyQt5.QtCore import Qt
from widgets.base_param import BaseParameterWindow
import time

class MorphologyParameterWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        super().__init__(parent, "Morphological Operations")
        
        # Initialize parameters
        self.default_params = {
            'operation': cv2.MORPH_ERODE,
            'kernel_shape': cv2.MORPH_RECT,
            'kernel_size': 3,
            'iterations': 1,
            'border_type': cv2.BORDER_CONSTANT,
            'border_value': 0
        }
        self.current_params = self.default_params.copy()
        
        self.live_preview = True
        self.last_update_time = 0
        
        # Setup UI and connections
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        super().setup_ui()
        self.setFixedSize(500, 600)
        
        # Live preview checkbox
        self.preview_cb = QCheckBox("Live Preview")
        self.preview_cb.setChecked(True)
        self.controls_layout.addWidget(self.preview_cb)
        
        # Operation selection
        op_group = QGroupBox("Operation")
        op_layout = QVBoxLayout()
        
        self.erode_rb = QRadioButton("Erosion")
        self.dilate_rb = QRadioButton("Dilation")
        self.open_rb = QRadioButton("Opening")
        self.close_rb = QRadioButton("Closing")
        self.gradient_rb = QRadioButton("Morphological Gradient")
        self.tophat_rb = QRadioButton("Top Hat")
        self.blackhat_rb = QRadioButton("Black Hat")
        
        self.erode_rb.setChecked(True)
        
        op_layout.addWidget(self.erode_rb)
        op_layout.addWidget(self.dilate_rb)
        op_layout.addWidget(self.open_rb)
        op_layout.addWidget(self.close_rb)
        op_layout.addWidget(self.gradient_rb)
        op_layout.addWidget(self.tophat_rb)
        op_layout.addWidget(self.blackhat_rb)
        op_group.setLayout(op_layout)
        self.controls_layout.addWidget(op_group)
        
        # Kernel parameters
        kernel_group = QGroupBox("Kernel Parameters")
        kernel_layout = QVBoxLayout()
        
        # Kernel shape
        shape_layout = QHBoxLayout()
        shape_layout.addWidget(QLabel("Kernel Shape:"))
        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["Rectangle", "Cross", "Ellipse"])
        shape_layout.addWidget(self.shape_combo)
        kernel_layout.addLayout(shape_layout)
        
        # Kernel size
        self.kernel_size_slider = self.create_slider("Kernel Size:", 1, 21, self.default_params['kernel_size'], odd_only=True)
        kernel_layout.addLayout(self.kernel_size_slider)
        
        # Iterations
        self.iterations_slider = self.create_slider("Iterations:", 1, 10, self.default_params['iterations'])
        kernel_layout.addLayout(self.iterations_slider)
        
        kernel_group.setLayout(kernel_layout)
        self.controls_layout.addWidget(kernel_group)
        
        # Border parameters
        border_group = QGroupBox("Border Parameters")
        border_layout = QVBoxLayout()
        
        # Border type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Border Type:"))
        self.border_combo = QComboBox()
        self.border_combo.addItems(["Constant", "Replicate", "Reflect", "Wrap", "Reflect101"])
        type_layout.addWidget(self.border_combo)
        border_layout.addLayout(type_layout)
        
        # Border value
        self.border_value_slider = self.create_slider("Border Value:", 0, 255, self.default_params['border_value'])
        border_layout.addLayout(self.border_value_slider)
        
        border_group.setLayout(border_layout)
        self.controls_layout.addWidget(border_group)

    def create_slider(self, label, min_val, max_val, default, float_step=None, odd_only=False):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        slider = QSlider(Qt.Horizontal)
        
        if float_step:
            slider.setRange(int(min_val * 10), int(max_val * 10))
            slider.setValue(int(default * 10))
            value_label = QLabel(f"{default:.1f}")
        else:
            slider.setRange(min_val, max_val)
            slider.setValue(default)
            value_label = QLabel(str(default))
            
        if odd_only:
            slider.setSingleStep(2)
            slider.setPageStep(2)
        
        layout.addWidget(slider)
        layout.addWidget(value_label)
        
        slider.value_label = value_label
        slider.float_step = float_step
        slider.odd_only = odd_only
        return layout
    
    def setup_connections(self):
        super().setup_connections()
        
        # Reconnect buttons to our custom handlers
        self.ok_btn.clicked.disconnect()
        self.ok_btn.clicked.connect(self.on_ok_clicked)
        
        self.revert_btn.clicked.disconnect()
        self.revert_btn.clicked.connect(self.on_revert_clicked)
        
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        
        # Connect operation radio buttons
        self.erode_rb.toggled.connect(self.on_parameter_changed)
        self.dilate_rb.toggled.connect(self.on_parameter_changed)
        self.open_rb.toggled.connect(self.on_parameter_changed)
        self.close_rb.toggled.connect(self.on_parameter_changed)
        self.gradient_rb.toggled.connect(self.on_parameter_changed)
        self.tophat_rb.toggled.connect(self.on_parameter_changed)
        self.blackhat_rb.toggled.connect(self.on_parameter_changed)
        
        # Connect other controls
        self.preview_cb.stateChanged.connect(self.on_preview_changed)
        self.shape_combo.currentIndexChanged.connect(self.on_parameter_changed)
        self.border_combo.currentIndexChanged.connect(self.on_parameter_changed)
        
        for slider in self.findChildren(QSlider):
            slider.valueChanged.connect(self.on_parameter_changed)
    
    def on_ok_clicked(self):
        """Apply changes and close window"""
        self.apply_changes()
        self.close()
    
    def on_revert_clicked(self):
        """Revert to original image and reset parameters"""
        if self.parent and self.original_image is not None:
            self.parent.display_image(self.original_image)
            self.reset_parameters()
    
    def on_cancel_clicked(self):
        """Revert changes and close window"""
        self.on_revert_clicked()
        self.close()
    
    def reset_parameters(self):
        """Reset all parameters to their default values"""
        self.erode_rb.setChecked(True)
        self.shape_combo.setCurrentIndex(0)
        self.kernel_size_slider.itemAt(1).widget().setValue(self.default_params['kernel_size'])
        self.iterations_slider.itemAt(1).widget().setValue(self.default_params['iterations'])
        self.border_combo.setCurrentIndex(0)
        self.border_value_slider.itemAt(1).widget().setValue(self.default_params['border_value'])
        
        self.current_params = self.default_params.copy()
        self.apply_changes(preview_only=True)
    
    def on_preview_changed(self, state):
        self.live_preview = state == Qt.Checked
    
    def on_parameter_changed(self):
        sender = self.sender()
        if isinstance(sender, QSlider) and hasattr(sender, 'value_label'):
            if sender.float_step:
                value = sender.value() / 10.0
                sender.value_label.setText(f"{value:.1f}")
            else:
                if sender.odd_only:
                    # Ensure value is odd
                    value = sender.value()
                    if value % 2 == 0:
                        value = max(1, value - 1)
                        sender.setValue(value)
                sender.value_label.setText(str(sender.value()))
        
        if self.live_preview and self.parent and self.parent.image is not None:
            current_time = time.time()
            if current_time - self.last_update_time > 0.066:  # ~15fps
                self.apply_changes(preview_only=True)
                self.last_update_time = current_time
    
    def apply_changes(self, preview_only=False):
        if not self.parent or self.parent.image is None:
            return
            
        # Get current operation
        if self.erode_rb.isChecked():
            operation = cv2.MORPH_ERODE
        elif self.dilate_rb.isChecked():
            operation = cv2.MORPH_DILATE
        elif self.open_rb.isChecked():
            operation = cv2.MORPH_OPEN
        elif self.close_rb.isChecked():
            operation = cv2.MORPH_CLOSE
        elif self.gradient_rb.isChecked():
            operation = cv2.MORPH_GRADIENT
        elif self.tophat_rb.isChecked():
            operation = cv2.MORPH_TOPHAT
        elif self.blackhat_rb.isChecked():
            operation = cv2.MORPH_BLACKHAT
        else:
            operation = cv2.MORPH_ERODE
        
        # Get kernel shape
        shape_map = {
            0: cv2.MORPH_RECT,
            1: cv2.MORPH_CROSS,
            2: cv2.MORPH_ELLIPSE
        }
        kernel_shape = shape_map.get(self.shape_combo.currentIndex(), cv2.MORPH_RECT)
        
        # Get kernel size (ensure odd)
        kernel_size = self.kernel_size_slider.itemAt(1).widget().value()
        if hasattr(self.kernel_size_slider.itemAt(1).widget(), 'odd_only'):
            kernel_size = max(1, kernel_size | 1)  # Ensure odd and >= 1
        
        # Get iterations
        iterations = self.iterations_slider.itemAt(1).widget().value()
        
        # Get border type
        border_map = {
            0: cv2.BORDER_CONSTANT,
            1: cv2.BORDER_REPLICATE,
            2: cv2.BORDER_REFLECT,
            3: cv2.BORDER_WRAP,
            4: cv2.BORDER_REFLECT101
        }
        border_type = border_map.get(self.border_combo.currentIndex(), cv2.BORDER_CONSTANT)
        
        # Get border value
        border_value = self.border_value_slider.itemAt(1).widget().value()
        
        self.current_params = {
            'operation': operation,
            'kernel_shape': kernel_shape,
            'kernel_size': kernel_size,
            'iterations': iterations,
            'border_type': border_type,
            'border_value': border_value
        }
        
        # Create kernel
        kernel = cv2.getStructuringElement(kernel_shape, (kernel_size, kernel_size))
        
        # Convert to grayscale if needed (for some operations)
        if len(self.parent.image.shape) == 3 and operation not in [cv2.MORPH_TOPHAT, cv2.MORPH_BLACKHAT]:
            img = cv2.cvtColor(self.parent.image, cv2.COLOR_BGR2GRAY)
        else:
            img = self.parent.image.copy()
        
        # Apply morphological operation
        if operation in [cv2.MORPH_TOPHAT, cv2.MORPH_BLACKHAT]:
            # Tophat and blackhat work better with color images
            result = cv2.morphologyEx(img, operation, kernel, 
                                     iterations=iterations,
                                     borderType=border_type,
                                     borderValue=border_value)
        else:
            if operation == cv2.MORPH_ERODE:
                result = cv2.erode(img, kernel, iterations=iterations,
                                  borderType=border_type, borderValue=border_value)
            elif operation == cv2.MORPH_DILATE:
                result = cv2.dilate(img, kernel, iterations=iterations,
                                   borderType=border_type, borderValue=border_value)
            else:
                result = cv2.morphologyEx(img, operation, kernel, 
                                        iterations=iterations,
                                        borderType=border_type,
                                        borderValue=border_value)
            
            # Convert back to 3 channels if original was color
            if len(self.parent.image.shape) == 3 and len(result.shape) == 2:
                result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        
        if preview_only:
            self.parent.temp_display_image(result)
        else:
            self.parent.display_image(result)