import cv2
import numpy as np
from PyQt5.QtWidgets import (QLabel, QSlider, QCheckBox, QGroupBox, 
                            QHBoxLayout, QVBoxLayout, QComboBox)
from PyQt5.QtCore import Qt
from widgets.base_param import BaseParameterWindow
import time

class LaplacianEnhancementWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        super().__init__(parent, "Laplacian Edge Enhancement")
        
        # Initialize parameters
        self.default_params = {
            'ksize': 3,  # Fixed 3x3 kernel size
            'scale': 1,
            'amount': 0.5,  # Enhancement amount (0-2)
            'blur_kernel': 0,  # Optional pre-blurring
            'border_type': cv2.BORDER_DEFAULT
        }
        self.current_params = self.default_params.copy()
        
        self.live_preview = True
        self.last_update_time = 0
        
        # Setup UI and connections
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        super().setup_ui()
        self.setFixedSize(500, 350)
        
        # Live preview checkbox
        self.preview_cb = QCheckBox("Live Preview")
        self.preview_cb.setChecked(True)
        self.controls_layout.addWidget(self.preview_cb)
        
        # Enhancement parameters
        enh_group = QGroupBox("Enhancement Parameters")
        enh_layout = QVBoxLayout()
        
        self.amount_slider = self.create_slider("Enhance Amount:", 0, 20, 
                                             int(self.default_params['amount'] * 10), 
                                             float_step=True)
        
        self.blur_slider = self.create_slider("Pre-blur (σ):", 0, 10, 
                                           self.default_params['blur_kernel'])
        
        enh_layout.addLayout(self.amount_slider)
        enh_layout.addLayout(self.blur_slider)
        enh_group.setLayout(enh_layout)
        self.controls_layout.addWidget(enh_group)
        
        # Laplacian parameters
        lap_group = QGroupBox("Laplacian Parameters")
        lap_layout = QVBoxLayout()
        
        # Kernel size is fixed to 3x3 for our custom kernel
        self.ksize_label = QLabel("Kernel Size: 3x3 (fixed)")
        lap_layout.addWidget(self.ksize_label)
        
        self.scale_slider = self.create_slider("Scale:", 1, 10, 
                                             self.default_params['scale'])
        
        lap_layout.addLayout(self.scale_slider)
        lap_group.setLayout(lap_layout)
        self.controls_layout.addWidget(lap_group)
        
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
        self.scale_slider.itemAt(1).widget().setValue(self.default_params['scale'])
        self.amount_slider.itemAt(1).widget().setValue(int(self.default_params['amount'] * 10))
        self.blur_slider.itemAt(1).widget().setValue(self.default_params['blur_kernel'])
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
        scale = self.scale_slider.itemAt(1).widget().value()
        amount = self.amount_slider.itemAt(1).widget().value() / 10.0
        blur_kernel = self.blur_slider.itemAt(1).widget().value()
        
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
            'ksize': 3,  # Fixed for our custom kernel
            'scale': scale,
            'amount': amount,
            'blur_kernel': blur_kernel,
            'border_type': border_type
        }
        
        # Work with a copy of the original image
        working_img = self.parent.image.copy()
        
        # Optional Gaussian blur for noise reduction
        if blur_kernel > 0:
            blur_kernel = blur_kernel * 2 + 1  # Ensure odd and positive
            working_img = cv2.GaussianBlur(working_img, (blur_kernel, blur_kernel), 0)
        
        # Define the Laplacian kernel (3x3)
        kernel = np.array([[0, 1, 0],
                         [1, -4, 1],
                         [0, 1, 0]], dtype=np.float32) * scale
        
        # Apply filter to each channel if color image
        if len(working_img.shape) == 3:
            enhanced = np.zeros_like(working_img, dtype=np.float32)
            for i in range(3):  # Process each channel separately
                channel = working_img[:,:,i].astype(np.float32)
                laplacian = cv2.filter2D(channel, -1, kernel, borderType=border_type)
                enhanced[:,:,i] = np.clip(channel + amount * laplacian, 0, 255)
        else:
            # For grayscale images
            working_img = working_img.astype(np.float32)
            laplacian = cv2.filter2D(working_img, -1, kernel, borderType=border_type)
            enhanced = np.clip(working_img + amount * laplacian, 0, 255)
        
        # Convert back to uint8
        enhanced = enhanced.astype(np.uint8)
        
        if preview_only:
            self.parent.temp_display_image(enhanced)
        else:
            self.parent.display_image(enhanced)