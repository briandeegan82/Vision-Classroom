import cv2
import depthai as dai
import numpy as np


class DepthAIStereoDepth:
    def __init__(self, resolution=400, extended_disparity=True, median_filter=True):
        """
        Initialize DepthAI stereo depth pipeline.
        
        Args:
            resolution (int): Camera resolution (400 or 800 pixels)
            extended_disparity (bool): Enable extended disparity for longer range
            median_filter (bool): Enable median filtering for noise reduction
        """
        self.resolution = self._get_resolution(resolution)
        self.extended_disparity = extended_disparity
        self.median_filter = median_filter
        self.pipeline = None
        self.device = None
        self.depth_queue = None
        self.depth_frame = None
        self.running = False

    def _get_resolution(self, resolution):
        """Convert numeric resolution to DepthAI enum."""
        resolutions = {
            400: dai.MonoCameraProperties.SensorResolution.THE_400_P,
            800: dai.MonoCameraProperties.SensorResolution.THE_800_P
        }
        return resolutions.get(resolution, dai.MonoCameraProperties.SensorResolution.THE_400_P)

    def create_pipeline(self):
        """Create and configure the DepthAI pipeline."""
        self.pipeline = dai.Pipeline()

        # Create stereo depth node
        stereo = self.pipeline.create(dai.node.StereoDepth)

        # Configure cameras
        left = self.pipeline.create(dai.node.MonoCamera)
        right = self.pipeline.create(dai.node.MonoCamera)
        
        left.setBoardSocket(dai.CameraBoardSocket.LEFT)
        left.setResolution(self.resolution)
        right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
        right.setResolution(self.resolution)

        # Link cameras to stereo depth
        left.out.link(stereo.left)
        right.out.link(stereo.right)

        # Configure depth processing
        if self.extended_disparity:
            stereo.setExtendedDisparity(True)
        if self.median_filter:
            stereo.setMedianFilter(dai.StereoDepthProperties.MedianFilter.KERNEL_7x7)

        # Create output stream
        xout_depth = self.pipeline.create(dai.node.XLinkOut)
        xout_depth.setStreamName("depth")
        stereo.depth.link(xout_depth.input)

    def _mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks to display depth values."""
        if event == cv2.EVENT_LBUTTONDOWN and self.depth_frame is not None:
            distance = self.depth_frame[y, x] / 1000.0  # Convert mm to meters
            print(f"Depth at ({x}, {y}): {distance:.2f} meters")

    def start(self):
        """Start the depth stream with interactive visualization."""
        try:
            self.create_pipeline()
            self.device = dai.Device(self.pipeline)
            self.depth_queue = self.device.getOutputQueue(name="depth", maxSize=1, blocking=False)
            self.running = True

            cv2.namedWindow("Depth Image")
            cv2.setMouseCallback("Depth Image", self._mouse_callback)

            while self.running:
                depth_data = self.depth_queue.get()
                self.depth_frame = depth_data.getFrame()

                # Normalize and colorize for visualization
                depth_vis = cv2.normalize(self.depth_frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                depth_colored = cv2.applyColorMap(depth_vis, cv2.COLORMAP_TURBO)

                cv2.imshow("Depth Image", depth_colored)
                if cv2.waitKey(1) == ord('q'):
                    break

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop the pipeline and clean up resources."""
        self.running = False
        if hasattr(self, 'device') and self.device:
            self.device.close()
        cv2.destroyAllWindows()

    def __enter__(self):
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.stop()


if __name__ == "__main__":
    # Example usage
    with DepthAIStereoDepth(resolution=400) as depth_sensor:
        depth_sensor.start()