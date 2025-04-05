import cv2
import numpy as np
from PyQt5.QtWidgets import (QLabel, QSlider, QCheckBox, QGroupBox, 
                            QHBoxLayout, QVBoxLayout, QComboBox)
from PyQt5.QtCore import Qt
from widgets.base_param import BaseParameterWindow
import time

class UnsharpMaskParameterWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        super().__init__(parent, "Unsharp Mask")
        
        # Initialize parameters
        self.default_params = {
            'amount': 1.0,
            'radius': 1.0,
            'threshold': 0,
            'blur_type': 'gaussian',
            'preserve_color': False
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
        
        # Sharpening parameters
        sharpen_group = QGroupBox("Sharpening Parameters")
        sharpen_layout = QVBoxLayout()
        
        self.amount_slider = self.create_slider("Amount:", 0.0, 3.0, self.default_params['amount'], float_step=0.1)
        self.radius_slider = self.create_slider("Radius:", 0.1, 5.0, self.default_params['radius'], float_step=0.1)
        self.threshold_slider = self.create_slider("Threshold:", 0, 255, self.default_params['threshold'])
        
        sharpen_layout.addLayout(self.amount_slider)
        sharpen_layout.addLayout(self.radius_slider)
        sharpen_layout.addLayout(self.threshold_slider)
        sharpen_group.setLayout(sharpen_layout)
        self.controls_layout.addWidget(sharpen_group)
        
        # Blur type selection
        blur_group = QGroupBox("Blur Type")
        blur_layout = QVBoxLayout()
        
        self.blur_combo = QComboBox()
        self.blur_combo.addItems(["Gaussian", "Median", "Bilateral"])
        blur_layout.addWidget(self.blur_combo)
        blur_group.setLayout(blur_layout)
        self.controls_layout.addWidget(blur_group)
        
        # Color handling
        color_group = QGroupBox("Color Handling")
        color_layout = QVBoxLayout()
        
        self.color_cb = QCheckBox("Preserve Color (Lab space)")
        self.color_cb.setChecked(self.default_params['preserve_color'])
        color_layout.addWidget(self.color_cb)
        color_group.setLayout(color_layout)
        self.controls_layout.addWidget(color_group)

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
        self.blur_combo.currentIndexChanged.connect(self.on_parameter_changed)
        self.color_cb.stateChanged.connect(self.on_parameter_changed)
        
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
        self.amount_slider.itemAt(1).widget().setValue(int(self.default_params['amount'] * 10))
        self.radius_slider.itemAt(1).widget().setValue(int(self.default_params['radius'] * 10))
        self.threshold_slider.itemAt(1).widget().setValue(self.default_params['threshold'])
        self.blur_combo.setCurrentIndex(0)
        self.color_cb.setChecked(self.default_params['preserve_color'])
        
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
        amount = self.amount_slider.itemAt(1).widget().value() / 10.0
        radius = self.radius_slider.itemAt(1).widget().value() / 10.0
        threshold = self.threshold_slider.itemAt(1).widget().value()
        blur_type = self.blur_combo.currentText().lower()
        preserve_color = self.color_cb.isChecked()
        
        self.current_params = {
            'amount': amount,
            'radius': radius,
            'threshold': threshold,
            'blur_type': blur_type,
            'preserve_color': preserve_color
        }
        
        # Apply unsharp mask
        result = self.apply_unsharp_mask(
            self.parent.image,
            amount=amount,
            radius=radius,
            threshold=threshold,
            blur_type=blur_type,
            preserve_color=preserve_color
        )
        
        if preview_only:
            self.parent.temp_display_image(result)
        else:
            self.parent.display_image(result)
    
    def apply_unsharp_mask(self, image, amount=1.0, radius=1.0, threshold=0, blur_type='gaussian', preserve_color=False):
        """Apply unsharp mask to the image"""
        if preserve_color and len(image.shape) == 3:
            # Convert to Lab color space to sharpen only L channel
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a, b = cv2.split(lab)
            
            # Apply unsharp mask to L channel
            sharpened_l = self._unsharp_mask_single_channel(l_channel, amount, radius, threshold, blur_type)
            
            # Merge back and convert to BGR
            lab = cv2.merge([sharpened_l, a, b])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            if len(image.shape) == 3:
                # Convert to grayscale if color preservation is off
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                sharpened = self._unsharp_mask_single_channel(gray, amount, radius, threshold, blur_type)
                return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
            else:
                return self._unsharp_mask_single_channel(image, amount, radius, threshold, blur_type)
    
    def _unsharp_mask_single_channel(self, image, amount, radius, threshold, blur_type):
        """Apply unsharp mask to a single channel image"""
        # Apply appropriate blur
        if blur_type == 'gaussian':
            blurred = cv2.GaussianBlur(image, (0, 0), radius)
        elif blur_type == 'median':
            ksize = int(2 * radius + 1)
            blurred = cv2.medianBlur(image, ksize)
        elif blur_type == 'bilateral':
            blurred = cv2.bilateralFilter(image, -1, radius, radius)
        
        # Calculate sharpened image
        sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
        
        # Apply threshold (only sharpen areas with significant difference)
        if threshold > 0:
            low_contrast = cv2.absdiff(image, blurred) < threshold
            sharpened = np.where(low_contrast, image, sharpened)
        
        # Clip values to valid range
        return np.clip(sharpened, 0, 255).astype(np.uint8)