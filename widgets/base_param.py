import numpy as np
import cv2
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QSlider, QPushButton, QGroupBox)
from PyQt5.QtCore import Qt

class BaseParameterWindow(QWidget):
    def __init__(self, parent=None, title="Parameters"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self.parent = parent
        self.original_image = None
        self.default_params = {}
        self.current_params = {}

        if parent and hasattr(parent, 'current_output'):
            self.original_image = parent.current_output.copy()

        # Removed: self.setup_ui()
        # Removed: self.setup_connections()

        self.setAttribute(Qt.WA_DeleteOnClose)

        if parent:
            parent.register_parameter_window(self)
    
    def setup_ui(self):
        """Setup base UI with standard buttons"""
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Parameter controls area (for subclasses to fill)
        self.controls_layout = QVBoxLayout()
        self.main_layout.addLayout(self.controls_layout)
        
        # Action buttons
        self.button_layout = QHBoxLayout()
        self.revert_btn = QPushButton("Revert")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.revert_btn)
        self.button_layout.addWidget(self.ok_btn)
        self.button_layout.addWidget(self.cancel_btn)
        
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)
    
    def setup_connections(self):
        """Setup base signal connections"""
        self.ok_btn.clicked.connect(self.on_ok)
        self.revert_btn.clicked.connect(self.on_revert)
        self.cancel_btn.clicked.connect(self.on_cancel)
    
    def on_ok(self):
        """Apply changes and close window"""
        self.apply_changes()
        self.close()
    
    def on_revert(self):
        """Revert to original image and reset parameters"""
        if self.parent and self.original_image is not None:
            self.parent.display_image(self.original_image)
            self.reset_parameters()  # Implement this in subclass
    
    def on_cancel(self):
        """Revert changes and close window"""
        self.on_revert()
        self.close()
    
    def reset_parameters(self):
        """To be implemented by subclasses - reset all parameters to defaults"""
        raise NotImplementedError("Subclasses must implement reset_parameters()")
    
    def apply_changes(self):
        """To be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement apply_changes()")
    
    def closeEvent(self, event):
        if self.parent:
            self.parent.unregister_parameter_window(self)
        super().closeEvent(event)