import cv2
import numpy as np
from PyQt5.QtWidgets import (QLabel, QSlider, QCheckBox, QGroupBox, 
                            QHBoxLayout, QVBoxLayout)
from PyQt5.QtCore import Qt
from widgets.base_param import BaseParameterWindow
import time

class BrightnessContrastWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        super().__init__(parent, "Brightness, Contrast & Gamma")

        self.default_params = {
            'brightness': 0,
            'contrast': 100,  # maps to 1.0
            'gamma': 100      # maps to 1.0
        }
        self.current_params = self.default_params.copy()

        self.live_preview = True
        self.last_update_time = 0

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        super().setup_ui()
        self.setFixedSize(500, 250)

        # Live Preview Checkbox
        self.preview_cb = QCheckBox("Live Preview")
        self.preview_cb.setChecked(True)
        self.controls_layout.addWidget(self.preview_cb)

        # Group Box
        bcg_group = QGroupBox("Brightness / Contrast / Gamma")
        bcg_layout = QVBoxLayout()

        # Sliders
        self.brightness_slider = self.create_slider("Brightness:", -127, 127, self.default_params['brightness'])
        self.contrast_slider = self.create_slider("Contrast:", 0, 300, self.default_params['contrast'],
                                                  value_formatter=lambda v: f"{v/100:.2f}")
        self.gamma_slider = self.create_slider("Gamma:", 10, 300, self.default_params['gamma'],
                                               value_formatter=lambda v: f"{v/100:.2f}")

        bcg_layout.addLayout(self.brightness_slider)
        bcg_layout.addLayout(self.contrast_slider)
        bcg_layout.addLayout(self.gamma_slider)

        bcg_group.setLayout(bcg_layout)
        self.controls_layout.addWidget(bcg_group)

    def create_slider(self, label, min_val, max_val, default, value_formatter=None):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        layout.addWidget(slider)

        if value_formatter is None:
            value_formatter = lambda v: str(v)

        value_label = QLabel(value_formatter(default))
        layout.addWidget(value_label)

        slider.value_label = value_label
        slider.value_formatter = value_formatter
        return layout

    def setup_connections(self):
        super().setup_connections()

        self.ok_btn.clicked.disconnect()
        self.ok_btn.clicked.connect(self.on_ok_clicked)

        self.revert_btn.clicked.disconnect()
        self.revert_btn.clicked.connect(self.on_revert_clicked)

        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)

        self.preview_cb.stateChanged.connect(self.on_preview_changed)

        for slider in self.findChildren(QSlider):
            slider.valueChanged.connect(self.on_parameter_changed)

    def on_ok_clicked(self):
        self.apply_changes()
        self.close()

    def on_revert_clicked(self):
        if self.parent and self.original_image is not None:
            self.parent.display_image(self.original_image)
            self.reset_parameters()

    def on_cancel_clicked(self):
        self.on_revert_clicked()
        self.close()

    def reset_parameters(self):
        self.brightness_slider.itemAt(1).widget().setValue(self.default_params['brightness'])
        self.contrast_slider.itemAt(1).widget().setValue(self.default_params['contrast'])
        self.gamma_slider.itemAt(1).widget().setValue(self.default_params['gamma'])

        self.current_params = self.default_params.copy()
        self.apply_changes(preview_only=True)

    def on_preview_changed(self, state):
        self.live_preview = state == Qt.Checked

    def on_parameter_changed(self):
        sender = self.sender()
        if isinstance(sender, QSlider) and hasattr(sender, 'value_label'):
            val = sender.value()
            sender.value_label.setText(sender.value_formatter(val))

        if self.live_preview and self.parent and self.parent.image is not None:
            current_time = time.time()
            if current_time - self.last_update_time > 0.066:
                self.apply_changes(preview_only=True)
                self.last_update_time = current_time

    def apply_changes(self, preview_only=False):
        if not self.parent or self.parent.image is None:
            return

        brightness = self.brightness_slider.itemAt(1).widget().value()
        contrast_val = self.contrast_slider.itemAt(1).widget().value()
        gamma_val = self.gamma_slider.itemAt(1).widget().value()

        contrast = contrast_val / 100.0
        gamma = gamma_val / 100.0

        self.current_params = {
            'brightness': brightness,
            'contrast': contrast_val,
            'gamma': gamma_val
        }

        img = self.parent.image.copy().astype(np.float32)

        # Brightness and contrast
        img = img * contrast + brightness

        # Gamma correction
        img = np.clip(img, 0, 255) / 255.0
        img = np.power(img, 1.0 / gamma)
        img = np.clip(img * 255.0, 0, 255).astype(np.uint8)

        if preview_only:
            self.parent.temp_display_image(img)
        else:
            self.parent.display_image(img)
