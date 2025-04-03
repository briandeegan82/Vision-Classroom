import numpy as np
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                            QHBoxLayout, QComboBox, QWidget, QSlider, QPushButton, QCheckBox, 
                            QGroupBox, QRadioButton, QFileDialog, QAction, QToolBar, QMenu, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from .base_param import BaseParameterWindow


class MorphologyParameterWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        super().__init__("Morphology Parameters", parent)
        self.live_preview = True
    
    def setup_ui(self):
        self.setFixedSize(350, 300)
        
        layout = QVBoxLayout()
        
        # Live preview checkbox
        self.preview_cb = QCheckBox("Live Preview")
        self.preview_cb.setChecked(True)
        layout.addWidget(self.preview_cb)
        
        # Operation selection
        op_group = QGroupBox("Operation")
        op_layout = QVBoxLayout()
        
        self.erode_rb = QRadioButton("Erode")
        self.dilate_rb = QRadioButton("Dilate")
        self.open_rb = QRadioButton("Open")
        self.close_rb = QRadioButton("Close")
        self.gradient_rb = QRadioButton("Gradient")
        self.tophat_rb = QRadioButton("Top Hat")
        self.blackhat_rb = QRadioButton("Black Hat")
        
        self.dilate_rb.setChecked(True)
        
        op_layout.addWidget(self.erode_rb)
        op_layout.addWidget(self.dilate_rb)
        op_layout.addWidget(self.open_rb)
        op_layout.addWidget(self.close_rb)
        op_layout.addWidget(self.gradient_rb)
        op_layout.addWidget(self.tophat_rb)
        op_layout.addWidget(self.blackhat_rb)
        op_group.setLayout(op_layout)
        layout.addWidget(op_group)
        
        # Kernel parameters
        kernel_group = QGroupBox("Kernel")
        kernel_layout = QVBoxLayout()
        
        self.kernel_size = self.create_slider("Kernel Size:", 1, 21, 3, odd_only=True)
        self.kernel_shape = QComboBox()
        self.kernel_shape.addItems(["Rectangle", "Cross", "Ellipse"])
        
        kernel_layout.addLayout(self.kernel_size)
        kernel_layout.addWidget(QLabel("Kernel Shape:"))
        kernel_layout.addWidget(self.kernel_shape)
        kernel_group.setLayout(kernel_layout)
        layout.addWidget(kernel_group)
        
        # Iterations
        self.iterations = self.create_slider("Iterations:", 1, 10, 1)
        layout.addLayout(self.iterations)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def setup_connections(self):
        # Connect all radio buttons and sliders
        for rb in self.findChildren(QRadioButton):
            rb.toggled.connect(self.on_parameter_changed)
        
        self.kernel_shape.currentIndexChanged.connect(self.on_parameter_changed)
        self.preview_cb.stateChanged.connect(lambda: setattr(self, 'live_preview', self.preview_cb.isChecked()))
        self.apply_btn.clicked.connect(self.apply_changes)
        self.cancel_btn.clicked.connect(self.close)
    
    def get_current_operation(self):
        if self.erode_rb.isChecked(): return cv2.MORPH_ERODE
        if self.dilate_rb.isChecked(): return cv2.MORPH_DILATE
        if self.open_rb.isChecked(): return cv2.MORPH_OPEN
        if self.close_rb.isChecked(): return cv2.MORPH_CLOSE
        if self.gradient_rb.isChecked(): return cv2.MORPH_GRADIENT
        if self.tophat_rb.isChecked(): return cv2.MORPH_TOPHAT
        if self.blackhat_rb.isChecked(): return cv2.MORPH_BLACKHAT
        return cv2.MORPH_DILATE
    
    def get_kernel_shape(self):
        shapes = {
            0: cv2.MORPH_RECT,
            1: cv2.MORPH_CROSS,
            2: cv2.MORPH_ELLIPSE
        }
        return shapes.get(self.kernel_shape.currentIndex(), cv2.MORPH_RECT)
    
    def apply_changes(self, preview_only=False):
        if not self.parent or self.parent.image is None:
            return
            
        # Get parameters
        op = self.get_current_operation()
        ksize = self.kernel_size.itemAt(1).widget().value()
        ksize = ksize + 1 if ksize % 2 == 0 else ksize  # Ensure odd
        shape = self.get_kernel_shape()
        iterations = self.iterations.itemAt(1).widget().value()
        
        # Create kernel
        kernel = cv2.getStructuringElement(shape, (ksize, ksize))
        
        # Apply operation
        if op in [cv2.MORPH_ERODE, cv2.MORPH_DILATE]:
            result = cv2.morphologyEx(
                self.parent.image, 
                op, 
                kernel, 
                iterations=iterations
            )
        else:
            result = cv2.morphologyEx(
                self.parent.image, 
                op, 
                kernel
            )
        
        if preview_only:
            self.parent.temp_display_image(result)
        else:
            self.parent.display_image(result)