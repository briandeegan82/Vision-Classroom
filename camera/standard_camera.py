import cv2
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QSpinBox, QSizePolicy)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

class BaseCameraWidget(QWidget):
    """Base class for all camera widgets with common interface"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera_running = False
        self.init_ui()
        
    def init_ui(self):
        """Initialize common UI elements"""
        # Create layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # Video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.main_layout.addWidget(self.video_label, 1)
        
        # Create controls layout but don't add it yet
        # This will be added by the derived classes
        self.controls_layout = QHBoxLayout()
        
    def start_stream(self):
        """Start the camera stream"""
        raise NotImplementedError
        
    def stop_stream(self):
        """Stop the camera stream"""
        raise NotImplementedError
        
    def get_frame(self):
        """Get current frame from camera"""
        raise NotImplementedError
        
    def update_frame(self):
        """Update the displayed frame"""
        frame = self.get_frame()
        if frame is not None:
            # Convert to RGB for display
            if len(frame.shape) == 2:  # Grayscale
                q_img = QImage(frame.data, frame.shape[1], frame.shape[0], 
                             frame.strides[0], QImage.Format_Grayscale8)
            else:  # Color (assuming BGR from OpenCV)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(q_img)
            self.video_label.setPixmap(
                pixmap.scaled(
                    self.video_label.width(),
                    self.video_label.height(),
                    Qt.KeepAspectRatio
                )
            )

class StandardCameraWidget(BaseCameraWidget):
        
    def __init__(self, parent=None):
        super().__init__(parent)

        self.capture = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.setWindowTitle("Standard Camera")

        # Set initial window size
        self.setMinimumSize(800, 600)
        self.resize(800, 600)

        # Properly size the video display
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set widget expansion policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add camera controls
        self.setup_camera_controls()

        # Add stretch to push controls to the bottom if needed
        self.main_layout.addStretch()
        
    def setup_camera_controls(self):
        """Add camera-specific controls"""
        # Device selection
        self.device_combo = QComboBox()
        self.device_combo.addItem("Default Camera (0)", 0)
        for i in range(1, 5):
            self.device_combo.addItem(f"Camera {i}", i)
        self.controls_layout.addWidget(QLabel("Camera:"))
        self.controls_layout.addWidget(self.device_combo)
        
        # Resolution selection
        self.width_spin = QSpinBox()
        self.width_spin.setRange(320, 1920)
        self.width_spin.setValue(640)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(240, 1080)
        self.height_spin.setValue(480)
        self.controls_layout.addWidget(QLabel("Width:"))
        self.controls_layout.addWidget(self.width_spin)
        self.controls_layout.addWidget(QLabel("Height:"))
        self.controls_layout.addWidget(self.height_spin)
        
        # Buttons
        self.start_btn = QPushButton("Start Stream")
        self.start_btn.clicked.connect(self.toggle_stream)
        self.controls_layout.addWidget(self.start_btn)
        
        # Set size policies to ensure proper expansion
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_layout.addLayout(self.controls_layout)

    def toggle_stream(self):
        if self.camera_running:
            self.stop_stream()
            self.start_btn.setText("Start Stream")
        else:
            if self.start_stream():
                self.start_btn.setText("Stop Stream")
    
    def start_stream(self):
        try:
            # Get selected parameters
            self.capture_device = self.device_combo.currentData()
            self.resolution = (
                self.width_spin.value(),
                self.height_spin.value()
            )
            
            # Initialize capture
            self.capture = cv2.VideoCapture(self.capture_device)
            
            if not self.capture.isOpened():
                print(f"Error: Could not open video device {self.capture_device}")
                return False
            
            # Set resolution
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
            # Start timer for frame updates
            self.timer.start(30)  # ~30ms = ~33fps
            self.camera_running = True
            return True
        except Exception as e:
            print(f"Error starting camera: {e}")
            return False
    
    def stop_stream(self):
        self.timer.stop()
        if self.capture and self.capture.isOpened():
            self.capture.release()
        self.capture = None
        self.camera_running = False
        self.video_label.clear()
        self.video_label.setStyleSheet("background-color: black;")
    
    def get_frame(self):
        if self.camera_running and self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                return frame
        return None

    def closeEvent(self, event):
        self.stop_stream()
        super().closeEvent(event)


class OakDLiteCameraWidget(BaseCameraWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from camera.oakd_lite_camera import OakDLiteCamera
        self.camera = OakDLiteCamera()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.setWindowTitle("OAK-D Lite Camera")
        
    def start_stream(self):
        self.camera.start_stream()
        self.timer.start(30)
        self.camera_running = True
        return True
        
    def stop_stream(self):
        self.timer.stop()
        self.camera.stop_stream()
        self.camera_running = False
        self.video_label.clear()
        self.video_label.setStyleSheet("background-color: black;")
        
    def get_frame(self):
        return self.camera.get_frame()

class StereoCameraWidget(BaseCameraWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from camera.depth_ai_stereo import DepthAIStereoDepth
        self.camera = DepthAIStereoDepth()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.setWindowTitle("Stereo Camera")
        
    def start_stream(self):
        self.camera.start()
        self.timer.start(30)
        self.camera_running = True
        return True
        
    def stop_stream(self):
        self.timer.stop()
        self.camera.stop()
        self.camera_running = False
        self.video_label.clear()
        self.video_label.setStyleSheet("background-color: black;")
        
    def get_frame(self):
        return self.camera.depth_frame if hasattr(self.camera, 'depth_frame') else None