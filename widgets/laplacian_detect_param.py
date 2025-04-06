import cv2
import numpy as np
from PyQt5.QtWidgets import (QLabel, QSlider, QCheckBox, QGroupBox, 
                            QHBoxLayout, QVBoxLayout, QComboBox)
from PyQt5.QtCore import Qt
from widgets.base_param import BaseParameterWindow
import time

class LaplacianParameterWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        super().__init__(parent, "Laplacian Edge Enhancement")
        
        # Initialize parameters
        self.default_params = {
            'ksize': 3,
            'scale': 1,
            'delta': 0,
            'border_type': cv2.BORDER_DEFAULT,
            'blend_factor': 0.5
        }
        self.current_params = self.default_params.copy()
        
        self.live_preview = True
        self.last_update_time = 0
        
        # Setup UI and connections
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        super().setup_ui()
        self.setFixedSize(500, 300)
        
        # Live preview checkbox
        self.preview_cb = QCheckBox("Live Preview")
        self.preview_cb.setChecked(True)
        self.controls_layout.addWidget(self.preview_cb)
        
        # Kernel parameters
        kernel_group = QGroupBox("Filter Parameters")
        kernel_layout = QVBoxLayout()
        
        self.ksize_slider = self.create_slider("Kernel Size:", 1, 7, self.default_params['ksize'], odd_only=True)
        self.scale_slider = self.create_slider("Scale:", 1, 10, self.default_params['scale'])
        self.delta_slider = self.create_slider("Delta:", 0, 255, self.default_params['delta'])
        self.blend_slider = self.create_slider("Blend Factor:", 0, 10, int(self.default_params['blend_factor'] * 10), float_step=True)
        
        kernel_layout.addLayout(self.ksize_slider)
        kernel_layout.addLayout(self.scale_slider)
        kernel_layout.addLayout(self.delta_slider)
        kernel_layout.addLayout(self.blend_slider)
        kernel_group.setLayout(kernel_layout)
        self.controls_layout.addWidget(kernel_group)
        
        # Border type parameters
        border_group = QGroupBox("Border Type")
        border_layout = QVBoxLayout()
        
        self.border_combo = QComboBox()
        self.border_combo.addItems([
            "Default (Reflect)", 
            "Constant", 
            "Replicate", 
            "Reflect 101", 
            "Wrap"
        ])
        border_layout.addWidget(self.border_combo)
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
        
        # Connect other controls
        self.preview_cb.stateChanged.connect(self.on_preview_changed)
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
        self.ksize_slider.itemAt(1).widget().setValue(self.default_params['ksize'])
        self.scale_slider.itemAt(1).widget().setValue(self.default_params['scale'])
        self.delta_slider.itemAt(1).widget().setValue(self.default_params['delta'])
        self.blend_slider.itemAt(1).widget().setValue(int(self.default_params['blend_factor'] * 10))
        self.border_combo.setCurrentIndex(0)
        
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
            
        # Get current values
        ksize = self.ksize_slider.itemAt(1).widget().value()
        if hasattr(self.ksize_slider.itemAt(1).widget(), 'odd_only'):
            ksize = max(1, ksize | 1)  # Ensure odd and >= 1
        
        scale = self.scale_slider.itemAt(1).widget().value()
        delta = self.delta_slider.itemAt(1).widget().value()
        blend_factor = self.blend_slider.itemAt(1).widget().value() / 10.0
        
        # Map border type selection to OpenCV constant
        border_map = {
            0: cv2.BORDER_DEFAULT,
            1: cv2.BORDER_CONSTANT,
            2: cv2.BORDER_REPLICATE,
            3: cv2.BORDER_REFLECT101,
            4: cv2.BORDER_WRAP
        }
        border_type = border_map.get(self.border_combo.currentIndex(), cv2.BORDER_DEFAULT)
        
        self.current_params = {
            'ksize': ksize,
            'scale': scale,
            'delta': delta,
            'border_type': border_type,
            'blend_factor': blend_factor
        }
        
        # Convert to grayscale if needed
        if len(self.parent.image.shape) == 3:
            gray_img = cv2.cvtColor(self.parent.image, cv2.COLOR_BGR2GRAY)
        else:
            gray_img = self.parent.image
        
        # Apply Laplacian filter
        laplacian = cv2.Laplacian(
            gray_img,
            cv2.CV_64F,
            ksize=ksize,
            scale=scale,
            delta=delta,
            borderType=border_type
        )
        
        # Convert to absolute value and scale to 0-255
        laplacian_abs = cv2.convertScaleAbs(laplacian)
        
        # Enhance edges by blending with original image
        if len(self.parent.image.shape) == 3:
            # For color images, convert laplacian to BGR and blend
            laplacian_bgr = cv2.cvtColor(laplacian_abs, cv2.COLOR_GRAY2BGR)
            result = cv2.addWeighted(self.parent.image, 1 - blend_factor, laplacian_bgr, blend_factor, 0)
        else:
            # For grayscale images, blend directly
            result = cv2.addWeighted(self.parent.image, 1 - blend_factor, laplacian_abs, blend_factor, 0)
        
        if preview_only:
            self.parent.temp_display_image(result)
        else:
            self.parent.display_image(result)