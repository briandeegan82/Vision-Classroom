import numpy as np
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                            QHBoxLayout, QWidget, QSlider, QPushButton, QCheckBox, 
                            QGroupBox, QFileDialog, QAction, QToolBar, QMenu, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from .base_param import BaseParameterWindow

class DenoiseParameterWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        super().__init__("Denoising Parameters", parent)
        self.live_preview = True
    
    def setup_ui(self):
        self.setFixedSize(300, 250)
        
        layout = QVBoxLayout()
        
        # Live preview checkbox
        self.preview_cb = QCheckBox("Live Preview")
        self.preview_cb.setChecked(True)
        layout.addWidget(self.preview_cb)
        
        # Denoising parameters
        params_group = QGroupBox("Denoising Parameters")
        params_layout = QVBoxLayout()
        
        self.h_slider = self.create_slider("Filter Strength:", 1, 50, 10)
        self.h_color_slider = self.create_slider("Color Strength:", 1, 50, 10)
        self.template_slider = self.create_slider("Template Window:", 3, 11, 7, odd_only=True)
        self.search_slider = self.create_slider("Search Window:", 3, 21, 21, odd_only=True)
        
        params_layout.addLayout(self.h_slider)
        params_layout.addLayout(self.h_color_slider)
        params_layout.addLayout(self.template_slider)
        params_layout.addLayout(self.search_slider)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def create_slider(self, label, min_val, max_val, default, odd_only=False):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        
        if odd_only:
            slider.setSingleStep(2)
            slider.setPageStep(2)
        
        layout.addWidget(slider)
        value_label = QLabel(str(default))
        layout.addWidget(value_label)
        
        slider.value_label = value_label
        if odd_only:
            slider.valueChanged.connect(lambda v: value_label.setText(str(v if v % 2 else v + 1)))
        else:
            slider.valueChanged.connect(lambda v: value_label.setText(str(v)))
        
        return layout
    
    def setup_connections(self):
        for slider in self.findChildren(QSlider):
            if not hasattr(slider, 'value_label'):  # Skip if already connected
                slider.valueChanged.connect(lambda v, s=slider: s.value_label.setText(str(v)))
        
        self.preview_cb.stateChanged.connect(lambda: setattr(self, 'live_preview', self.preview_cb.isChecked()))
        self.apply_btn.clicked.connect(self.apply_changes)
        self.cancel_btn.clicked.connect(self.close)
    
    def on_parameter_changed(self):
        if self.live_preview and self.parent and self.parent.image is not None:
            self.apply_changes(preview_only=True)
    
    def apply_changes(self, preview_only=False):
        if not self.parent or self.parent.image is None:
            return
            
        h = self.h_slider.itemAt(1).widget().value()
        h_color = self.h_color_slider.itemAt(1).widget().value()
        template_window = self.template_slider.itemAt(1).widget().value()
        search_window = self.search_slider.itemAt(1).widget().value()
        
        # Ensure odd window sizes
        template_window = template_window + 1 if template_window % 2 == 0 else template_window
        search_window = search_window + 1 if search_window % 2 == 0 else search_window
        
        denoised = cv2.fastNlMeansDenoisingColored(
            self.parent.image,
            None,
            h,
            h_color,
            template_window,
            search_window
        )
        
        if preview_only:
            self.parent.temp_display_image(denoised)
        else:
            self.parent.display_image(denoised)