import numpy as np
import cv2
import time
from PyQt5.QtWidgets import (QLabel, QSlider, QCheckBox, QGroupBox, QHBoxLayout, QVBoxLayout)
from PyQt5.QtCore import Qt
from widgets.base_param import BaseParameterWindow

class HSVParameterWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        # Call parent constructor first
        super().__init__(parent, "HSV Parameters")
        
        # Initialize parameters after parent constructor
        self.default_params = {
            'hue_shift': 0,
            'hue_scale': 100,
            'sat_shift': 0,
            'sat_scale': 100,
            'val_shift': 0,
            'val_scale': 100
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
        
        # Hue adjustment
        hue_group = QGroupBox("Hue Adjustment")
        hue_layout = QVBoxLayout()
        
        self.hue_slider = self.create_slider("Hue Shift:", -180, 180, self.default_params['hue_shift'])
        self.hue_scale = self.create_slider("Hue Scale:", 50, 200, self.default_params['hue_scale'])
        
        hue_layout.addLayout(self.hue_slider)
        hue_layout.addLayout(self.hue_scale)
        hue_group.setLayout(hue_layout)
        self.controls_layout.addWidget(hue_group)
        
        # Saturation/Value adjustments
        sv_group = QGroupBox("Saturation/Value Adjustments")
        sv_layout = QVBoxLayout()
        
        self.sat_slider = self.create_slider("Saturation Shift:", -100, 100, self.default_params['sat_shift'])
        self.sat_scale = self.create_slider("Saturation Scale:", 50, 200, self.default_params['sat_scale'])
        self.val_slider = self.create_slider("Value Shift:", -100, 100, self.default_params['val_shift'])
        self.val_scale = self.create_slider("Value Scale:", 50, 200, self.default_params['val_scale'])
        
        sv_layout.addLayout(self.sat_slider)
        sv_layout.addLayout(self.sat_scale)
        sv_layout.addLayout(self.val_slider)
        sv_layout.addLayout(self.val_scale)
        sv_group.setLayout(sv_layout)
        self.controls_layout.addWidget(sv_group)

    # ... rest of the methods remain the same ...

    def create_slider(self, label, min_val, max_val, default):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        layout.addWidget(slider)
        value_label = QLabel(str(default))
        layout.addWidget(value_label)
        
        slider.value_label = value_label
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
        self.hue_slider.itemAt(1).widget().setValue(self.default_params['hue_shift'])
        self.hue_scale.itemAt(1).widget().setValue(self.default_params['hue_scale'])
        self.sat_slider.itemAt(1).widget().setValue(self.default_params['sat_shift'])
        self.sat_scale.itemAt(1).widget().setValue(self.default_params['sat_scale'])
        self.val_slider.itemAt(1).widget().setValue(self.default_params['val_shift'])
        self.val_scale.itemAt(1).widget().setValue(self.default_params['val_scale'])
        
        self.current_params = self.default_params.copy()
        self.apply_changes(preview_only=True)
    
    def on_preview_changed(self, state):
        self.live_preview = state == Qt.Checked
    
    def on_parameter_changed(self):
        slider = self.sender()
        if hasattr(slider, 'value_label'):
            slider.value_label.setText(str(slider.value()))
        
        if self.live_preview and self.parent and self.parent.image is not None:
            current_time = time.time()
            if current_time - self.last_update_time > 0.066:
                self.apply_changes(preview_only=True)
                self.last_update_time = current_time
    
    def apply_changes(self, preview_only=False):
        if not self.parent or self.parent.image is None:
            return
            
        # Get current values
        self.current_params = {
            'hue_shift': self.hue_slider.itemAt(1).widget().value(),
            'hue_scale': self.hue_scale.itemAt(1).widget().value() / 100.0,
            'sat_shift': self.sat_slider.itemAt(1).widget().value(),
            'sat_scale': self.sat_scale.itemAt(1).widget().value() / 100.0,
            'val_shift': self.val_slider.itemAt(1).widget().value(),
            'val_scale': self.val_scale.itemAt(1).widget().value() / 100.0
        }
        
        # Process image
        hsv_img = cv2.cvtColor(self.parent.image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Apply adjustments
        hsv_img[:,:,0] = (hsv_img[:,:,0] * self.current_params['hue_scale'] + 
                         self.current_params['hue_shift']) % 180
        hsv_img[:,:,1] = np.clip(hsv_img[:,:,1] * self.current_params['sat_scale'] + 
                         self.current_params['sat_shift'], 0, 255)
        hsv_img[:,:,2] = np.clip(hsv_img[:,:,2] * self.current_params['val_scale'] + 
                         self.current_params['val_shift'], 0, 255)
        
        result = cv2.cvtColor(hsv_img.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        if preview_only:
            self.parent.temp_display_image(result)
        else:
            self.parent.display_image(result)