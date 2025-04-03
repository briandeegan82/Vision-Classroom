import numpy as np
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                            QHBoxLayout, QWidget, QSlider, QPushButton, 
                            QFileDialog, QAction, QToolBar, QMenu, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class BaseParameterWindow(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)
        self.parent = parent
        self.setup_ui()
        self.setup_connections()
        
        # Window management
        self.setAttribute(Qt.WA_DeleteOnClose)
        if parent:
            parent.register_parameter_window(self)
    
    def setup_ui(self):
        """To be implemented by subclasses"""
        pass
    
    def setup_connections(self):
        """To be implemented by subclasses"""
        pass
    
    def apply_changes(self):
        """To be implemented by subclasses"""
        pass
    
    def closeEvent(self, event):
        if self.parent:
            self.parent.unregister_parameter_window(self)
        super().closeEvent(event)