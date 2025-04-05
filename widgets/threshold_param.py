import cv2
import numpy as np
from PyQt5.QtWidgets import (QLabel, QSlider, QCheckBox, QGroupBox, 
                            QHBoxLayout, QVBoxLayout, QComboBox, QRadioButton)
from PyQt5.QtCore import Qt
from widgets.base_param import BaseParameterWindow
import time

class ThresholdParameterWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        super().__init__(parent, "Thresholding")
        
        # Initialize parameters
        self.default_params = {
            'method': cv2.THRESH_BINARY,
            'thresh': 127,
            'maxval': 255,
            'block_size': 11,
            'C': 2,
            'otsu': False,
            'triangle': False
        }
        self.current_params = self.default_params.copy()
        
        self.live_preview = True
        self.last_update_time = 0
        
        # Setup UI and connections
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        super().setup_ui()
        self.setFixedSize(500, 450)
        
        # Live preview checkbox
        self.preview_cb = QCheckBox("Live Preview")
        self.preview_cb.setChecked(True)
        self.controls_layout.addWidget(self.preview_cb)
        
        # Threshold method selection
        method_group = QGroupBox("Threshold Method")
        method_layout = QVBoxLayout()
        
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "Binary",
            "Binary Inverted",
            "Truncate",
            "To Zero",
            "To Zero Inverted",
            "Adaptive Mean",
            "Adaptive Gaussian",
            "Otsu's (Global)",
            "Triangle (Global)"
        ])
        method_layout.addWidget(self.method_combo)
        method_group.setLayout(method_layout)
        self.controls_layout.addWidget(method_group)
        
        # Threshold parameters
        param_group = QGroupBox("Threshold Parameters")
        param_layout = QVBoxLayout()
        
        self.thresh_slider = self.create_slider("Threshold Value:", 0, 255, self.default_params['thresh'])
        self.maxval_slider = self.create_slider("Maximum Value:", 0, 255, self.default_params['maxval'])
        
        param_layout.addLayout(self.thresh_slider)
        param_layout.addLayout(self.maxval_slider)
        
        # Adaptive threshold parameters
        self.adaptive_group = QGroupBox("Adaptive Threshold Parameters")
        adaptive_layout = QVBoxLayout()
        
        self.block_size_slider = self.create_slider("Block Size:", 3, 51, self.default_params['block_size'], odd_only=True)
        self.C_slider = self.create_slider("C Value:", -10, 10, self.default_params['C'])
        
        adaptive_layout.addLayout(self.block_size_slider)
        adaptive_layout.addLayout(self.C_slider)
        self.adaptive_group.setLayout(adaptive_layout)
        self.adaptive_group.setVisible(False)  # Hidden by default
        
        param_layout.addWidget(self.adaptive_group)
        param_group.setLayout(param_layout)
        self.controls_layout.addWidget(param_group)
        
        # Advanced options
        adv_group = QGroupBox("Advanced Options")
        adv_layout = QVBoxLayout()
        
        self.otsu_cb = QCheckBox("Always use Otsu's method (with other methods)")
        self.otsu_cb.setChecked(self.default_params['otsu'])
        
        self.triangle_cb = QCheckBox("Always use Triangle method (with other methods)")
        self.triangle_cb.setChecked(self.default_params['triangle'])
        
        adv_layout.addWidget(self.otsu_cb)
        adv_layout.addWidget(self.triangle_cb)
        adv_group.setLayout(adv_layout)
        self.controls_layout.addWidget(adv_group)

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
        
        # Connect other controls
        self.preview_cb.stateChanged.connect(self.on_preview_changed)
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        self.otsu_cb.stateChanged.connect(self.on_parameter_changed)
        self.triangle_cb.stateChanged.connect(self.on_parameter_changed)
        
        for slider in self.findChildren(QSlider):
            slider.valueChanged.connect(self.on_parameter_changed)
    
    def on_method_changed(self, index):
        # Show/hide adaptive parameters based on selection
        is_adaptive = index in [5, 6]  # Adaptive Mean or Gaussian
        self.adaptive_group.setVisible(is_adaptive)
        
        # Global methods (Otsu, Triangle) disable manual threshold slider
        is_global = index in [7, 8]
        self.thresh_slider.itemAt(1).widget().setEnabled(not is_global)
        
        self.on_parameter_changed()
    
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
        self.method_combo.setCurrentIndex(0)
        self.thresh_slider.itemAt(1).widget().setValue(self.default_params['thresh'])
        self.maxval_slider.itemAt(1).widget().setValue(self.default_params['maxval'])
        self.block_size_slider.itemAt(1).widget().setValue(self.default_params['block_size'])
        self.C_slider.itemAt(1).widget().setValue(self.default_params['C'])
        self.otsu_cb.setChecked(self.default_params['otsu'])
        self.triangle_cb.setChecked(self.default_params['triangle'])
        
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
                if hasattr(sender, 'odd_only') and sender.odd_only:
                    # Ensure value is odd
                    value = sender.value()
                    if value % 2 == 0:
                        value = max(3, value - 1)
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
            
        # Get current values
        method_idx = self.method_combo.currentIndex()
        method_map = {
            0: cv2.THRESH_BINARY,
            1: cv2.THRESH_BINARY_INV,
            2: cv2.THRESH_TRUNC,
            3: cv2.THRESH_TOZERO,
            4: cv2.THRESH_TOZERO_INV,
            5: cv2.ADAPTIVE_THRESH_MEAN_C,
            6: cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            7: cv2.THRESH_OTSU,
            8: cv2.THRESH_TRIANGLE
        }
        method = method_map.get(method_idx, cv2.THRESH_BINARY)
        
        thresh = self.thresh_slider.itemAt(1).widget().value()
        maxval = self.maxval_slider.itemAt(1).widget().value()
        
        block_size = self.block_size_slider.itemAt(1).widget().value()
        if hasattr(self.block_size_slider.itemAt(1).widget(), 'odd_only'):
            block_size = max(3, block_size | 1)  # Ensure odd and >= 3
        
        C = self.C_slider.itemAt(1).widget().value()
        use_otsu = self.otsu_cb.isChecked()
        use_triangle = self.triangle_cb.isChecked()
        
        self.current_params = {
            'method': method,
            'thresh': thresh,
            'maxval': maxval,
            'block_size': block_size,
            'C': C,
            'otsu': use_otsu,
            'triangle': use_triangle
        }
        
        # Convert to grayscale if needed
        if len(self.parent.image.shape) == 3:
            gray_img = cv2.cvtColor(self.parent.image, cv2.COLOR_BGR2GRAY)
        else:
            gray_img = self.parent.image
        
        # Apply thresholding
        if method_idx in [5, 6]:  # Adaptive methods
            result = cv2.adaptiveThreshold(
                gray_img,
                maxval,
                method,
                cv2.THRESH_BINARY,
                block_size,
                C
            )
        else:  # Global methods
            flags = method
            if use_otsu:
                flags |= cv2.THRESH_OTSU
            if use_triangle:
                flags |= cv2.THRESH_TRIANGLE
            
            _, result = cv2.threshold(
                gray_img,
                thresh,
                maxval,
                flags
            )
        
        # Convert to 3-channel image for display if needed
        if len(self.parent.image.shape) == 3:
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        
        if preview_only:
            self.parent.temp_display_image(result)
        else:
            self.parent.display_image(result)