import cv2
import numpy as np
from PyQt5.QtWidgets import (QLabel, QSlider, QCheckBox, QGroupBox, 
                            QHBoxLayout, QVBoxLayout, QComboBox)
from PyQt5.QtCore import Qt
from widgets.base_param import BaseParameterWindow
import time

class CannyParameterWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        # Call parent constructor first
        super().__init__(parent, "Canny Edge Detection")
        
        # Initialize parameters
        self.default_params = {
            'threshold1': 50,
            'threshold2': 150,
            'aperture_size': 3,
            'l2_gradient': False
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
        
        # Threshold parameters
        threshold_group = QGroupBox("Threshold Parameters")
        threshold_layout = QVBoxLayout()
        
        self.threshold1_slider = self.create_slider("Threshold 1:", 0, 500, self.default_params['threshold1'])
        self.threshold2_slider = self.create_slider("Threshold 2:", 0, 500, self.default_params['threshold2'])
        
        threshold_layout.addLayout(self.threshold1_slider)
        threshold_layout.addLayout(self.threshold2_slider)
        threshold_group.setLayout(threshold_layout)
        self.controls_layout.addWidget(threshold_group)
        
        # Advanced parameters
        advanced_group = QGroupBox("Advanced Parameters")
        advanced_layout = QVBoxLayout()
        
        # Aperture size combo box (only 3, 5, or 7)
        aperture_layout = QHBoxLayout()
        aperture_layout.addWidget(QLabel("Aperture Size:"))
        self.aperture_combo = QComboBox()
        self.aperture_combo.addItems(["3", "5", "7"])
        self.aperture_combo.setCurrentText(str(self.default_params['aperture_size']))
        aperture_layout.addWidget(self.aperture_combo)
        advanced_layout.addLayout(aperture_layout)
        
        self.l2_gradient_cb = QCheckBox("Use L2 Gradient (more accurate)")
        self.l2_gradient_cb.setChecked(self.default_params['l2_gradient'])
        
        advanced_layout.addWidget(self.l2_gradient_cb)
        advanced_group.setLayout(advanced_layout)
        self.controls_layout.addWidget(advanced_group)

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
        self.l2_gradient_cb.stateChanged.connect(self.on_parameter_changed)
        self.aperture_combo.currentTextChanged.connect(self.on_parameter_changed)
        
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
        self.threshold1_slider.itemAt(1).widget().setValue(self.default_params['threshold1'])
        self.threshold2_slider.itemAt(1).widget().setValue(self.default_params['threshold2'])
        self.aperture_combo.setCurrentText(str(self.default_params['aperture_size']))
        self.l2_gradient_cb.setChecked(self.default_params['l2_gradient'])
        
        self.current_params = self.default_params.copy()
        self.apply_changes(preview_only=True)
    
    def on_preview_changed(self, state):
        self.live_preview = state == Qt.Checked
    
    def on_parameter_changed(self):
        sender = self.sender()
        if isinstance(sender, QSlider) and hasattr(sender, 'value_label'):
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
        self.current_params = {
            'threshold1': self.threshold1_slider.itemAt(1).widget().value(),
            'threshold2': self.threshold2_slider.itemAt(1).widget().value(),
            'aperture_size': int(self.aperture_combo.currentText()),
            'l2_gradient': self.l2_gradient_cb.isChecked()
        }
        
        # Process image
        gray_img = cv2.cvtColor(self.parent.image, cv2.COLOR_BGR2GRAY)
        
        # Apply Canny edge detection
        edges = cv2.Canny(
            gray_img,
            self.current_params['threshold1'],
            self.current_params['threshold2'],
            apertureSize=self.current_params['aperture_size'],
            L2gradient=self.current_params['l2_gradient']
        )
        
        # Convert to 3-channel image for display
        result = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        if preview_only:
            self.parent.temp_display_image(result)
        else:
            self.parent.display_image(result)