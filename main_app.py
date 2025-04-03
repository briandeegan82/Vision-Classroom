import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                            QHBoxLayout, QWidget, QSlider, QPushButton, 
                            QFileDialog, QAction, QToolBar, QMenu, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from camera.oakd_lite_camera import OakDLiteCamera
from widgets.base_param import BaseParameterWindow
from widgets.colour_param import HSVParameterWindow
from widgets.denoise_param import DenoiseParameterWindow
from widgets.morph_param import MorphologyParameterWindow

class CVTeachingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Computer Vision Teaching Tool")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize variables
        self.image = None
        self.current_output = None
        self.current_output_path = ""
        self.threshold1 = 50
        self.threshold2 = 150
        self.aperture_size = 3
        self.l2_gradient = False

        self.camera = None
        self.camera_running = False
        self.parameter_windows = {}
        self.temp_display = None
        
        self.initUI()
        
    def initUI(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create menu bars
        self.createMenuBars()
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)
        main_layout.addWidget(self.image_label)
        
        # Control panel
        control_panel = QWidget()
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)
        
        # Threshold controls
        threshold1_layout = QHBoxLayout()
        threshold1_layout.addWidget(QLabel("Threshold 1:"))
        self.threshold1_slider = QSlider(Qt.Horizontal)
        self.threshold1_slider.setRange(0, 255)
        self.threshold1_slider.setValue(self.threshold1)
        self.threshold1_slider.valueChanged.connect(self.update_threshold1)
        threshold1_layout.addWidget(self.threshold1_slider)
        threshold1_layout.addWidget(QLabel(str(self.threshold1)))
        self.threshold1_label = threshold1_layout.itemAt(2).widget()
        control_layout.addLayout(threshold1_layout)
        
        threshold2_layout = QHBoxLayout()
        threshold2_layout.addWidget(QLabel("Threshold 2:"))
        self.threshold2_slider = QSlider(Qt.Horizontal)
        self.threshold2_slider.setRange(0, 255)
        self.threshold2_slider.setValue(self.threshold2)
        self.threshold2_slider.valueChanged.connect(self.update_threshold2)
        threshold2_layout.addWidget(self.threshold2_slider)
        threshold2_layout.addWidget(QLabel(str(self.threshold2)))
        self.threshold2_label = threshold2_layout.itemAt(2).widget()
        control_layout.addLayout(threshold2_layout)
        
        # Apply button
        self.apply_button = QPushButton("Apply Canny Edge Detection")
        self.apply_button.clicked.connect(self.apply_canny)
        control_layout.addWidget(self.apply_button)
        
        main_layout.addWidget(control_panel)
    
    def register_parameter_window(self, window):
        """Track open parameter windows"""
        key = window.windowTitle()
        self.parameter_windows[key] = window
    
    def unregister_parameter_window(self, window):
        """Remove closed windows from tracking"""
        key = window.windowTitle()
        if key in self.parameter_windows:
            del self.parameter_windows[key]
    
    def temp_display_image(self, img):
        """Display temporary preview images"""
        if not hasattr(self, 'temp_display'):
            self.temp_display = img.copy()
        # Convert and display similar to display_image()
        if len(img.shape) == 2:  # Grayscale
            q_img = QImage(img.data, img.shape[1], img.shape[0], 
                          img.strides[0], QImage.Format_Grayscale8)
        else:  # BGR
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_img.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.width(), self.image_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    def show_parameter_window(self, window_class):
        """Show or activate a parameter window"""
        title = window_class.__name__.replace("ParameterWindow", "").replace("Window", "")
        
        if title in self.parameter_windows:
            self.parameter_windows[title].raise_()
            return
            
        if self.image is None:
            QMessageBox.warning(self, "No Image", "Please load an image first")
            return
            
        window = window_class(self)
        window.show()

    def createMenuBars(self):
        # Create main menu bar
        menubar = self.menuBar()
        
        # --- File Menu ---
        file_menu = menubar.addMenu('File')
        
        # Open Action
        open_action = QAction('Open...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        
        # Save Actions
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_image)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As...', self)
        save_as_action.triggered.connect(self.save_as_image)
        file_menu.addAction(save_as_action)
        
        # Exit Action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # --- Tools Menu ---
        tools_menu = menubar.addMenu('Tools')
        
        # Edge Detection Submenu
        edge_menu = QMenu('Edge Detection', self)
        
        canny_action = QAction('Canny', self)
        canny_action.triggered.connect(lambda: self.show_parameter_window(MorphologyParameterWindow))
        edge_menu.addAction(canny_action)
        
        sobel_action = QAction('Sobel', self)
        sobel_action.triggered.connect(lambda: self.apply_edge_detection('sobel'))
        edge_menu.addAction(sobel_action)
        
        tools_menu.addMenu(edge_menu)
        
        # Color Operations
        color_menu = QMenu('Color', self)
        
        grayscale_action = QAction('Convert to Grayscale', self)
        grayscale_action.triggered.connect(self.convert_to_grayscale)
        color_menu.addAction(grayscale_action)
        
        hsv_action = QAction('Adjust HSV', self)  # Changed from 'Convert to HSV'
        hsv_action.triggered.connect(lambda: self.show_parameter_window(HSVParameterWindow))
        color_menu.addAction(hsv_action)
        
        tools_menu.addMenu(color_menu)
        
        # Denoise
        denoise_action = QAction('Denoise', self)
        denoise_action.triggered.connect(lambda: self.show_parameter_window(DenoiseParameterWindow))
        tools_menu.addAction(denoise_action)
        
        # Morphology
        morph_action = QAction('Morphology', self)
        morph_action.triggered.connect(lambda: self.show_parameter_window(MorphologyParameterWindow))
        tools_menu.addAction(morph_action)

        # --- Camera Menu ---
        camera_menu = menubar.addMenu('Camera')

        # Start/Stop Camera
        self.camera_start_action = QAction('Start Camera', self)
        self.camera_start_action.triggered.connect(self.start_camera_stream)
        camera_menu.addAction(self.camera_start_action)
        
        self.camera_stop_action = QAction('Stop Camera', self)
        self.camera_stop_action.triggered.connect(self.stop_camera_stream)
        self.camera_stop_action.setEnabled(False)
        camera_menu.addAction(self.camera_stop_action)
        
        # Camera Settings Submenu
        settings_menu = QMenu('Settings', self)
        
        res_640 = QAction('640x480', self)
        res_640.triggered.connect(lambda: self.set_camera_resolution((640, 480)))
        settings_menu.addAction(res_640)
        
        res_720 = QAction('1280x720', self)
        res_720.triggered.connect(lambda: self.set_camera_resolution((1280, 720)))
        settings_menu.addAction(res_720)
        
        camera_menu.addMenu(settings_menu)

        # --- Help Menu ---
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def start_camera_stream(self):
        """Initialize and start the camera stream."""
        try:
            if self.camera is None:
                self.camera = OakDLiteCamera(preview_size=(640, 480), fps=30)
            
            self.camera.start_stream()
            self.camera_running = True
            self.camera_start_action.setEnabled(False)
            self.camera_stop_action.setEnabled(True)
            
            # Start a timer to update the display
            self.camera_timer = self.startTimer(30)  # ~30ms = ~30fps
            
            QMessageBox.information(self, "Camera", "Camera stream started successfully")
        except Exception as e:
            QMessageBox.critical(self, "Camera Error", f"Failed to start camera: {str(e)}")
    
    def stop_camera_stream(self):
        """Stop the camera stream."""
        if self.camera is not None:
            self.camera.stop_stream()
            self.camera_running = False
            self.camera_start_action.setEnabled(True)
            self.camera_stop_action.setEnabled(False)
            self.killTimer(self.camera_timer)
            
            # Clear camera display if needed
            if hasattr(self, 'camera_image'):
                self.display_image(np.zeros((480, 640, 3), dtype=np.uint8))
    
    def timerEvent(self, event):
        """Handle timer events for camera frame updates."""
        if self.camera_running and self.camera is not None:
            frame = self.camera.get_frame()
            if frame is not None:
                self.current_output = frame.copy()
                self.display_image(frame)
                
                # If any processing is active, apply it
                if hasattr(self, 'active_processing'):
                    self.apply_active_processing(frame)

    def set_camera_resolution(self, resolution):
        """Change camera resolution."""
        if self.camera_running:
            self.stop_camera_stream()
        
        self.camera = OakDLiteCamera(preview_size=resolution, fps=30)
        
        if self.camera_running:  # If was running, restart with new resolution
            self.start_camera_stream()

    def apply_active_processing(self, frame):
        """Apply the currently selected processing to camera frames."""
        # Example implementation - extend with your actual processing methods
        if self.active_processing == 'canny':
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            processed = cv2.Canny(gray, self.threshold1, self.threshold2)
            self.display_image(processed)

    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        
        if file_path:
            self.image = cv2.imread(file_path, cv2.IMREAD_COLOR)
            self.current_output = self.image.copy()
            self.current_output_path = file_path
            self.display_image(self.image)
            
    def display_image(self, img):
        # Convert the image to QImage
        if len(img.shape) == 2:  # Grayscale
            q_img = QImage(img.data, img.shape[1], img.shape[0], 
                          img.strides[0], QImage.Format_Grayscale8)
        else:  # BGR
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_img.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale the image to fit the label while maintaining aspect ratio
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.width(), self.image_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.current_output = img
            
    def update_threshold1(self, value):
        self.threshold1 = value
        self.threshold1_label.setText(str(value))
        
    def update_threshold2(self, value):
        self.threshold2 = value
        self.threshold2_label.setText(str(value))
        
    def apply_canny(self):
        if self.image is not None:
            gray_img = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(
                gray_img, 
                self.threshold1, 
                self.threshold2, 
                apertureSize=self.aperture_size, 
                L2gradient=self.l2_gradient
            )
            self.display_image(edges)
            
    def reset_parameters(self):
        self.threshold1 = 50
        self.threshold2 = 150
        self.threshold1_slider.setValue(self.threshold1)
        self.threshold2_slider.setValue(self.threshold2)
        if self.image is not None:
            self.display_image(self.image)
    
    def apply_edge_detection(self, method):
        if self.image is None:
            return
            
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        if method == 'canny':
            edges = cv2.Canny(gray, self.threshold1, self.threshold2)
            self.display_image(edges)
        elif method == 'sobel':
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
            edges = cv2.magnitude(sobelx, sobely)
            self.display_image(edges)
    
    def convert_to_grayscale(self):
        if self.image is not None:
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            self.display_image(gray)
    
    def convert_to_hsv(self):
        if self.image is not None:
            hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
            self.display_image(hsv)
    
    def apply_denoising(self):
        if self.image is not None:
            denoised = cv2.fastNlMeansDenoisingColored(
                self.image, None, 10, 10, 7, 21)
            self.display_image(denoised)
    
    def apply_morphology(self):
        if self.image is not None:
            kernel = np.ones((5,5), np.uint8)
            morphed = cv2.morphologyEx(
                self.image, cv2.MORPH_GRADIENT, kernel)
            self.display_image(morphed)
    
    def save_image(self):
        if hasattr(self, 'current_output') and self.current_output is not None:
            if self.current_output_path:
                cv2.imwrite(self.current_output_path, self.current_output)
            else:
                self.save_as_image()
    
    def save_as_image(self):
        if hasattr(self, 'current_output') and self.current_output is not None:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Image", "", 
                "PNG (*.png);;JPEG (*.jpg *.jpeg);;All Files (*)")
            if path:
                cv2.imwrite(path, self.current_output)
                self.current_output_path = path
    
    def show_about(self):
        QMessageBox.about(self, "About CV Teaching Tool",
                         "Computer Vision Teaching Tool\n"
                         "Version 1.0\n\n"
                         "A PyQt5/OpenCV application for\n"
                         "teaching computer vision concepts.")

def main():
    app = QApplication(sys.argv)
    window = CVTeachingApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()