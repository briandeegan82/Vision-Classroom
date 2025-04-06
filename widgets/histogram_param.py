import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QCheckBox, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QComboBox
)
from PyQt5.QtCore import Qt
from widgets.base_param import BaseParameterWindow
import time

class HistogramEnhancementWindow(BaseParameterWindow):
    def __init__(self, parent=None):
        super().__init__(parent, "Histogram Enhancement")

        self.default_params = {
            'method': 'None',
            'clip_limit': 20,
            'tile_grid_size': 8,
            'stretch_min': 0,
            'stretch_max': 255
        }
        self.current_params = self.default_params.copy()

        self.live_preview = True
        self.last_update_time = 0

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        super().setup_ui()
        self.setFixedSize(500, 300)

        self.preview_cb = QCheckBox("Live Preview")
        self.preview_cb.setChecked(True)
        self.controls_layout.addWidget(self.preview_cb)

        # Method selection
        method_group = QGroupBox("Histogram Method")
        method_layout = QVBoxLayout()
        method_sel_layout = QHBoxLayout()
        method_sel_layout.addWidget(QLabel("Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["None", "Normalize", "Stretch", "Equalization", "CLAHE"])
        method_sel_layout.addWidget(self.method_combo)
        method_layout.addLayout(method_sel_layout)
        method_group.setLayout(method_layout)
        self.controls_layout.addWidget(method_group)

        # CLAHE settings
        self.clahe_group = QGroupBox("CLAHE Settings")
        clahe_layout = QVBoxLayout()
        self.clip_slider = self.create_slider("Clip Limit:", 1, 40, self.default_params['clip_limit'],
                                              lambda v: f"{v / 10:.1f}")
        self.grid_slider = self.create_slider("Tile Grid Size:", 2, 16, self.default_params['tile_grid_size'])
        clahe_layout.addLayout(self.clip_slider)
        clahe_layout.addLayout(self.grid_slider)
        self.clahe_group.setLayout(clahe_layout)
        self.controls_layout.addWidget(self.clahe_group)
        self.clahe_group.setVisible(False)

        # Stretch settings
        self.stretch_group = QGroupBox("Stretch Settings")
        stretch_layout = QVBoxLayout()
        self.stretch_min_slider = self.create_slider("Lower Clip:", 0, 255, self.default_params['stretch_min'])
        self.stretch_max_slider = self.create_slider("Upper Clip:", 0, 255, self.default_params['stretch_max'])
        stretch_layout.addLayout(self.stretch_min_slider)
        stretch_layout.addLayout(self.stretch_max_slider)
        self.stretch_group.setLayout(stretch_layout)
        self.controls_layout.addWidget(self.stretch_group)
        self.stretch_group.setVisible(False)

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
        self.method_combo.currentTextChanged.connect(self.on_method_changed)

        for slider in self.findChildren(QSlider):
            slider.valueChanged.connect(self.on_parameter_changed)

    def on_method_changed(self, text):
        self.clahe_group.setVisible(text == "CLAHE")
        self.stretch_group.setVisible(text == "Stretch")
        self.on_parameter_changed()

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
        self.method_combo.setCurrentText(self.default_params['method'])
        self.clip_slider.itemAt(1).widget().setValue(self.default_params['clip_limit'])
        self.grid_slider.itemAt(1).widget().setValue(self.default_params['tile_grid_size'])
        self.stretch_min_slider.itemAt(1).widget().setValue(self.default_params['stretch_min'])
        self.stretch_max_slider.itemAt(1).widget().setValue(self.default_params['stretch_max'])
        self.current_params = self.default_params.copy()
        self.apply_changes(preview_only=True)

    def apply_changes(self, preview_only=False):
        if not self.parent or self.parent.image is None:
            return

        method = self.method_combo.currentText()
        clip_limit = self.clip_slider.itemAt(1).widget().value() / 10.0
        tile_size = self.grid_slider.itemAt(1).widget().value()
        stretch_min = self.stretch_min_slider.itemAt(1).widget().value()
        stretch_max = self.stretch_max_slider.itemAt(1).widget().value()

        img = self.parent.image.copy()
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        if method == "Normalize":
            l = cv2.normalize(l, None, 0, 255, cv2.NORM_MINMAX)
        elif method == "Equalization":
            l = cv2.equalizeHist(l)
        elif method == "CLAHE":
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
            l = clahe.apply(l)
        elif method == "Stretch":
            # Manual histogram stretch (clip and rescale)
            l = np.clip(l, stretch_min, stretch_max)
            l = ((l - stretch_min) / max(1, stretch_max - stretch_min)) * 255.0
            l = np.clip(l, 0, 255).astype(np.uint8)

        enhanced = cv2.merge((l, a, b))
        result = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        if preview_only:
            self.parent.temp_display_image(result)
        else:
            self.parent.display_image(result)
