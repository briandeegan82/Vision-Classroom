import cv2
import depthai as dai

class OakDLiteCamera:
    def __init__(self, preview_size=(640, 480), fps=30):
        """
        Initialize OAK-D Lite camera with specified parameters.
        
        Args:
            preview_size (tuple): Camera preview resolution (width, height)
            fps (int): Frames per second
        """
        self.preview_size = preview_size
        self.fps = fps
        self.pipeline = None
        self.device = None
        self.video_queue = None
        self.running = False

    def initialize_pipeline(self):
        """Set up the DepthAI pipeline."""
        self.pipeline = dai.Pipeline()
        
        # Configure color camera
        cam_rgb = self.pipeline.create(dai.node.ColorCamera)
        cam_rgb.setPreviewSize(*self.preview_size)
        cam_rgb.setInterleaved(False)
        cam_rgb.setFps(self.fps)
        
        # Set up output stream
        xout = self.pipeline.create(dai.node.XLinkOut)
        xout.setStreamName("video")
        cam_rgb.preview.link(xout.input)

    def start_stream(self):
        """Start the camera stream."""
        try:
            self.initialize_pipeline()
            self.device = dai.Device(self.pipeline)
            self.video_queue = self.device.getOutputQueue(
                name="video", 
                maxSize=1, 
                blocking=False
            )
            self.running = True
            print("Camera stream started successfully")
        except Exception as e:
            print(f"Failed to start camera stream: {e}")
            self.running = False

    def get_frame(self):
        """Get the current frame from the camera.
        
        Returns:
            numpy.ndarray: OpenCV frame if available, None otherwise
        """
        if self.running and self.video_queue.has():
            return self.video_queue.get().getCvFrame()
        return None

    def stop_stream(self):
        """Stop the camera stream and clean up resources."""
        self.running = False
        if hasattr(self, 'device') and self.device:
            self.device.close()
        cv2.destroyAllWindows()
        print("Camera stream stopped")

    def stream_video(self, window_name="OAK-D Lite RGB Stream"):
        """
        Display live video stream in a window.
        
        Args:
            window_name (str): Name of the display window
        """
        if not self.running:
            self.start_stream()
            
        try:
            while self.running:
                frame = self.get_frame()
                if frame is not None:
                    cv2.imshow(window_name, frame)
                
                if cv2.waitKey(1) == ord('q'):
                    break
        finally:
            self.stop_stream()

    def __enter__(self):
        """Context manager entry point."""
        self.start_stream()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.stop_stream()


# Example usage
if __name__ == "__main__":
    # Basic usage
    with OakDLiteCamera(preview_size=(640, 480), fps=30) as camera:
        camera.stream_video()
    
    # Alternative usage with more control
    camera = OakDLiteCamera(preview_size=(1280, 720), fps=15)
    camera.start_stream()
    
    try:
        while True:
            frame = camera.get_frame()
            if frame is not None:
                # Do custom processing here
                processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                cv2.imshow("Processed Stream", processed_frame)
            
            if cv2.waitKey(1) == ord('q'):
                break
    finally:
        camera.stop_stream()