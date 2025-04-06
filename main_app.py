import sys
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                            QHBoxLayout, QWidget, QSlider, QPushButton, 
                            QFileDialog, QAction, QToolBar, QMenu, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
from camera.standard_camera import StandardCameraWidget, OakDLiteCameraWidget, StereoCameraWidget
from widgets.brightness_contrast import BrightnessContrastWindow
from widgets.histogram_param import HistogramEnhancementWindow
from widgets.colour_param import HSVParameterWindow
from widgets.denoise_param import DenoiseParameterWindow
from widgets.morph_param import MorphologyParameterWindow
from widgets.canny_param import CannyParameterWindow
from widgets.gauss_blur_param import GaussianBlurParameterWindow
from widgets.sobel_param import SobelParameterWindow
from widgets.threshold_param import ThresholdParameterWindow
from widgets.unsharp_mask_param import UnsharpMaskParameterWindow
from widgets.laplacian_detect_param import LaplacianParameterWindow
from widgets.laplacian_ee_param import LaplacianEnhancementWindow


# Set Qt platform to xcb
os.environ["QT_QPA_PLATFORM"] = "xcb"

# Configure Qt plugin paths
if sys.platform.startswith('linux'):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        ".venv/lib/python3.12/site-packages/PyQt5/Qt5/plugins"
    )

class CVTeachingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Computer Vision Teaching Tool")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize variables
        self.image = None
        self.current_output = None
        self.current_output_path = ""
        #self.threshold1 = 50
        #self.threshold2 = 150
        #self.aperture_size = 3
        #self.l2_gradient = False

        self.camera = None
        self.camera_running = False
        self.parameter_windows = {}
        self.temp_display = None
        self.current_camera = None
        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.update_camera_frame)
        
        self.initUI()
        
    # Fix in the CVTeachingApp class:

    def initUI(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create menu bars
        self.create_menu_bars()
        
        # Create a widget to contain both the image label and camera container
        display_container = QWidget()
        display_layout = QVBoxLayout()
        display_container.setLayout(display_layout)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)
        display_layout.addWidget(self.image_label)
        
        # Camera container - add it to the display layout instead of main layout
        self.camera_container = QWidget()
        self.camera_layout = QVBoxLayout()
        self.camera_container.setLayout(self.camera_layout)
        display_layout.addWidget(self.camera_container)
        
        # Add the display container to the main layout
        main_layout.addWidget(display_container, 1)  # Use stretch factor 1 to give it priority
        
        # Control panel - this will now appear below the display area
        control_panel = QWidget()
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)
        main_layout.addWidget(control_panel)
        
        # Initially hide the camera container
        self.camera_container.hide()

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
        # Get the window title from the class
        title = window_class.__name__.replace("ParameterWindow", "").replace("Window", "")
        
        # Check if window already exists
        if title in self.parameter_windows:
            self.parameter_windows[title].raise_()
            return
            
        # Verify we have an image
        if self.image is None and not self.camera_running:
            QMessageBox.warning(self, "No Image", "Please load an image or start camera first")
            return
            
        # Create and show the window
        window = window_class(self)
        window.show()
        self.register_parameter_window(window)

    def show_floating_parameter_window(self, window_class):
        """Generic method to show any parameter window as floating"""
        # Get the window title from the class name
        title = window_class.__name__.replace("ParameterWindow", "").replace("Window", "")
        
        # Check if window already exists
        if title in self.parameter_windows:
            self.parameter_windows[title].raise_()
            return
            
        # Verify we have an image
        if self.image is None and not self.camera_running:
            QMessageBox.warning(self, "No Image", "Please load an image or start camera first")
            return
            
        # Create and show the window
        param_window = window_class(self)
        param_window.show()

    def show_camera_window(self, camera_class):
        """Show camera stream in main window"""
        if self.current_camera:
            self.stop_camera_stream()
        
        self.current_camera = camera_class()
        if not self.current_camera.start_stream():
            QMessageBox.warning(self, "Error", "Could not start camera")
            return
        
        # Clear previous camera widgets
        while self.camera_layout.count():
            child = self.camera_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add ONLY the video label, NOT the controls layout
        self.camera_layout.addWidget(self.current_camera.video_label)
        
        # Hide the image label when showing camera
        self.image_label.hide()
        self.camera_container.show()
        self.camera_timer.start(30)  # Start frame updates

    def stop_camera_stream(self):
        """Stop the current camera stream and hide the camera container"""
        if self.current_camera:
            self.current_camera.stop_stream()
            self.current_camera = None
            self.camera_timer.stop()
            self.camera_container.hide()
            # Show the image label again when camera is stopped
            self.image_label.show()

    def update_camera_frame(self):
        """Update the camera frame from the current camera"""
        if self.current_camera:
            frame = self.current_camera.get_frame()
            if frame is not None:
                self.current_camera.update_frame()

    def stop_camera_stream(self):
        """Stop the current camera stream and hide the camera container"""
        if self.current_camera:
            self.current_camera.stop_stream()
            self.current_camera = None
            self.camera_timer.stop()
            self.camera_container.hide()

    def create_menu_bars(self):
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

        # brightness and contrast
        brightness_menu = QMenu('Brightness/Contrast', self)
        brightness_action = QAction('Adjust Brightness/Contrast', self)
        brightness_action.triggered.connect(lambda: self.show_parameter_window(BrightnessContrastWindow))
        brightness_menu.addAction(brightness_action)
        tools_menu.addMenu(brightness_menu)

        # Histogram Equalization
        histogram_action = QAction('Histogram', self)
        histogram_action.triggered.connect(lambda: self.show_parameter_window(HistogramEnhancementWindow))
        brightness_menu.addAction(histogram_action)
        tools_menu.addMenu(brightness_menu)
        
        # Edge Detection Submenu
        edge_menu = QMenu('Edge Detection', self)
        
        canny_action = QAction('Canny', self)
        canny_action.triggered.connect(lambda: self.show_parameter_window(CannyParameterWindow))
        edge_menu.addAction(canny_action)
        
        sobel_action = QAction('Sobel', self)
        sobel_action.triggered.connect(lambda: self.show_parameter_window(SobelParameterWindow))
        edge_menu.addAction(sobel_action)

        #laplacian
        laplacian_action = QAction('Laplacian', self)
        laplacian_action.triggered.connect(lambda: self.show_parameter_window(LaplacianParameterWindow))
        edge_menu.addAction(laplacian_action)
        
        tools_menu.addMenu(edge_menu)
        
        # Color Operations
        color_menu = QMenu('Color', self)
        
        grayscale_action = QAction('Convert to Grayscale', self)
        grayscale_action.triggered.connect(self.convert_to_grayscale)
        color_menu.addAction(grayscale_action)
        
        hsv_action = QAction('Adjust HSV', self)
        #hsv_action.triggered.connect(lambda: self.show_floating_parameter_window(HSVParameterWindow))
        hsv_action.triggered.connect(lambda: self.show_parameter_window(HSVParameterWindow))
        color_menu.addAction(hsv_action)
        
        tools_menu.addMenu(color_menu)

        blur_menu = QMenu('Blur', self)
        gaussian_action = QAction('Gaussian Blur', self)
        gaussian_action.triggered.connect(lambda: self.show_parameter_window(GaussianBlurParameterWindow))
        blur_menu.addAction(gaussian_action)

        tools_menu.addMenu(blur_menu)

        # edge enhancement
        edge_enhance_menu = QMenu('Edge Enhancement', self)

        # unsharp mask
        unsharp_action = QAction('Unsharp Mask', self)
        unsharp_action.triggered.connect(lambda: self.show_parameter_window(UnsharpMaskParameterWindow))
        edge_enhance_menu.addAction(unsharp_action)
        tools_menu.addMenu(edge_enhance_menu)

        # Laplacian Enhancement
        laplacian_enhance_action = QAction('Laplacian Enhancement', self)
        laplacian_enhance_action.triggered.connect(lambda: self.show_parameter_window(LaplacianEnhancementWindow))
        edge_enhance_menu.addAction(laplacian_enhance_action)
        tools_menu.addMenu(edge_enhance_menu)

        # Denoise
        denoise_action = QAction('Denoise', self)
        denoise_action.triggered.connect(lambda: self.show_parameter_window(DenoiseParameterWindow))
        tools_menu.addAction(denoise_action)

        # Threshold
        threshold_action = QAction('Threshold', self)
        threshold_action.triggered.connect(lambda: self.show_parameter_window(ThresholdParameterWindow))
        tools_menu.addAction(threshold_action)
        
        # Morphology
        morph_action = QAction('Morphology', self)
        morph_action.triggered.connect(lambda: self.show_parameter_window(MorphologyParameterWindow))
        tools_menu.addAction(morph_action)

        # --- Camera Menu ---
        camera_menu = menubar.addMenu('Camera')
        
        # Camera Selection Submenu
        camera_select_menu = QMenu('Select Camera', self)
        
        standard_action = QAction('Standard Camera', self)
        standard_action.triggered.connect(lambda: self.show_camera_window(StandardCameraWidget))
        camera_select_menu.addAction(standard_action)
        
        oakd_action = QAction('OAK-D Lite', self)
        oakd_action.triggered.connect(lambda: self.show_camera_window(OakDLiteCameraWidget))
        camera_select_menu.addAction(oakd_action)
        
        stereo_action = QAction('Stereo Camera', self)
        stereo_action.triggered.connect(lambda: self.show_camera_window(StereoCameraWidget))
        camera_select_menu.addAction(stereo_action)
        
        camera_menu.addMenu(camera_select_menu)
        
        # Track open camera windows
        self.camera_windows = []

        # --- Help Menu ---
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
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
        """Modified to store current output before changes"""
        # Store previous image if we have a current output
        if hasattr(self, 'current_output') and self.current_output is not None:
            self.previous_output = self.current_output.copy()
        
        # Convert and display the image
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