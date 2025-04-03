import numpy as np
import cv2
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                            QHBoxLayout, QWidget, QSlider, QPushButton, QCheckBox, 
                            QGroupBox, QFileDialog, QAction, QToolBar, QMenu, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from .base_param import BaseParameterWindow

class HSVParameterWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        super().__init__("HSV Parameters", parent)
        self.live_preview = True
        self.last_update_time = 0
    
    def setup_ui(self):
        self.setFixedSize(350, 250)
        
        layout = QVBoxLayout()
        
        # Live preview checkbox
        self.preview_cb = QCheckBox("Live Preview")
        self.preview_cb.setChecked(True)
        layout.addWidget(self.preview_cb)
        
        # Hue adjustment
        hue_group = QGroupBox("Hue Adjustment")
        hue_layout = QVBoxLayout()
        
        self.hue_slider = self.create_slider("Hue Shift:", -180, 180, 0)
        self.hue_scale = self.create_slider("Hue Scale:", 50, 200, 100)
        
        hue_layout.addLayout(self.hue_slider)
        hue_layout.addLayout(self.hue_scale)
        hue_group.setLayout(hue_layout)
        layout.addWidget(hue_group)
        
        # Saturation/Value adjustments
        sv_group = QGroupBox("Saturation/Value Adjustments")
        sv_layout = QVBoxLayout()
        
        self.sat_slider = self.create_slider("Saturation Shift:", -100, 100, 0)
        self.sat_scale = self.create_slider("Saturation Scale:", 50, 200, 100)
        self.val_slider = self.create_slider("Value Shift:", -100, 100, 0)
        self.val_scale = self.create_slider("Value Scale:", 50, 200, 100)
        
        sv_layout.addLayout(self.sat_slider)
        sv_layout.addLayout(self.sat_scale)
        sv_layout.addLayout(self.val_slider)
        sv_layout.addLayout(self.val_scale)
        sv_group.setLayout(sv_layout)
        layout.addWidget(sv_group)
        
        # Apply/Cancel buttons
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def create_slider(self, label, min_val, max_val, default):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        layout.addWidget(slider)
        value_label = QLabel(str(default))
        layout.addWidget(value_label)
        
        # Store reference to value label
        slider.value_label = value_label
        return layout
    
    def setup_connections(self):
        # Connect all sliders
        for slider in self.findChildren(QSlider):
            slider.valueChanged.connect(self.on_parameter_changed)
        
        self.preview_cb.stateChanged.connect(lambda: setattr(self, 'live_preview', self.preview_cb.isChecked()))
        self.apply_btn.clicked.connect(self.apply_changes)
        self.cancel_btn.clicked.connect(self.close)
    
    def on_parameter_changed(self):
        slider = self.sender()
        if hasattr(slider, 'value_label'):
            slider.value_label.setText(str(slider.value()))
        
        if self.live_preview and self.parent and self.parent.image is not None:
            current_time = time.time()
            # Throttle updates to max 15fps
            if current_time - self.last_update_time > 0.066:
                self.apply_changes(preview_only=True)
                self.last_update_time = current_time
    
    def apply_changes(self, preview_only=False):
        if not self.parent or self.parent.image is None:
            return
            
        # Get current values
        h_shift = self.hue_slider.itemAt(1).widget().value()
        h_scale = self.hue_scale.itemAt(1).widget().value() / 100.0
        s_shift = self.sat_slider.itemAt(1).widget().value()
        s_scale = self.sat_scale.itemAt(1).widget().value() / 100.0
        v_shift = self.val_slider.itemAt(1).widget().value()
        v_scale = self.val_scale.itemAt(1).widget().value() / 100.0
        
        # Process image
        hsv_img = cv2.cvtColor(self.parent.image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Apply hue adjustments (circular)
        hsv_img[:,:,0] = (hsv_img[:,:,0] * h_scale + h_shift) % 180
        
        # Apply saturation/value adjustments
        hsv_img[:,:,1] = np.clip(hsv_img[:,:,1] * s_scale + s_shift, 0, 255)
        hsv_img[:,:,2] = np.clip(hsv_img[:,:,2] * v_scale + v_shift, 0, 255)
        
        result = cv2.cvtColor(hsv_img.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        if preview_only:
            self.parent.temp_display_image(result)
        else:
            self.parent.display_image(result)