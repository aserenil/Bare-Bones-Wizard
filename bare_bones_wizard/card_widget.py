# card_widget.py
from PySide6.QtCore import Qt, QUrl, Signal, Slot
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

# --- NEW: Create a single, global network manager for the whole app ---
# This is the standard, recommended practice.
NETWORK_MANAGER = QNetworkAccessManager()


class CardWidget(QFrame):
    """
    An interactive widget that uses Qt's network classes to download its own thumbnail.
    """

    selected = Signal(object)
    chosen = Signal(dict)

    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        # --- NEW: This will hold our network reply object ---
        self.network_reply = None

        # --- UI Setup (no changes here) ---
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setMinimumHeight(150)
        self.setMaximumHeight(150)
        main_layout = QVBoxLayout(self)
        self.thumbnail_label = QLabel("Loading...")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setFixedSize(128, 96)
        self.thumbnail_label.setStyleSheet("border: 1px solid gray;")
        self.name_label = QLabel(self.item_data.get("name", "No Name"))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_container_layout = QHBoxLayout()
        thumb_container_layout.addStretch()
        thumb_container_layout.addWidget(self.thumbnail_label)
        thumb_container_layout.addStretch()
        main_layout.addStretch()
        main_layout.addLayout(thumb_container_layout)
        main_layout.addWidget(self.name_label)
        main_layout.addStretch()

    def select_card(self):
        self.setStyleSheet("QFrame { border: 2px solid #0078d4; }")

    def unselect_card(self):
        self.setStyleSheet("")

    def mousePressEvent(self, event: QMouseEvent):
        self.selected.emit(self)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.chosen.emit(self.item_data)
        super().mouseDoubleClickEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        # --- CHANGE: Check for network_reply instead of download_runner ---
        if not self.network_reply:
            self.start_download()

    def start_download(self):
        """Creates and executes a network request."""
        item_id = self.item_data.get("id", 0)
        url = QUrl(f"https://placehold.co/128x96/222/FFF.png?text=Item+{item_id}")
        request = QNetworkRequest(url)

        # --- NEW: Use the global network manager to get the URL ---
        self.network_reply = NETWORK_MANAGER.get(request)
        # --- NEW: Connect the finished signal to our new slot ---
        self.network_reply.finished.connect(self.on_network_reply_finished)

    @Slot()
    def on_network_reply_finished(self):
        """Slot to handle the completed network request."""
        # --- NEW: Read data directly from the reply object ---
        image_data = self.network_reply.readAll()

        # Check for errors
        if self.network_reply.error() != self.network_reply.NetworkError.NoError:
            print(f"Network Error: {self.network_reply.errorString()}")
            self.thumbnail_label.setText("Error")
        else:
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)

            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.thumbnail_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.thumbnail_label.clear()
                self.thumbnail_label.setPixmap(scaled_pixmap)
                self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Clean up the reply object
        self.network_reply.deleteLater()
        self.network_reply = None

    def closeEvent(self, event):
        """Ensure any running download is aborted when the widget is closed."""
        # --- NEW: Abort the network reply if it's running ---
        if self.network_reply and self.network_reply.isRunning():
            self.network_reply.abort()
        super().closeEvent(event)
