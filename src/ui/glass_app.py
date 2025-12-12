"""Modern PyQt6 UI with liquid glass aesthetic for clipboard sharing application."""
import sys
import time
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QStatusBar, QGraphicsDropShadowEffect,
    QSpacerItem, QSizePolicy, QProgressBar, QTextEdit, QGridLayout
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QThread, pyqtSignal,
    QParallelAnimationGroup, QSequentialAnimationGroup, QPoint, QSize
)
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient, QPen, QBrush,
    QPixmap, QFont, QPainterPath, QMouseEvent, QPalette
)

from core.clipboard_manager import ClipboardManager
from interfaces import ClipboardType, DeviceInfo, ClipboardData
from .animations import SlideInAnimation, FadeInAnimation, PulseEffect

@dataclass
class AnimationSettings:
    """Animation configuration settings."""
    duration: int = 300
    easing_curve: QEasingCurve.Type = QEasingCurve.Type.OutCubic

class LiquidGlassWidget(QFrame):
    """Base widget with liquid glass aesthetic."""

    def __init__(self, parent=None, blur_radius=20, opacity=200):
        super().__init__(parent)
        self.blur_radius = blur_radius
        self.opacity = opacity
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        """Paint liquid glass effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create rounded rect path
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)

        # Create gradient background
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, self.opacity))
        gradient.setColorAt(0.5, QColor(200, 220, 255, self.opacity))
        gradient.setColorAt(1, QColor(180, 200, 240, self.opacity))

        painter.fillPath(path, gradient)

        # Add subtle border
        pen = QPen(QColor(255, 255, 255, 100), 2)
        painter.setPen(pen)
        painter.drawPath(path)

class RippleButton(QPushButton):
    """Button with ripple effect animation."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.ripple_animation = None
        self.ripple_opacity = 0
        self.ripple_radius = 0
        self.ripple_center = QPoint()

        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 150, 255, 200),
                    stop:1 rgba(50, 100, 200, 200));
                border: none;
                border-radius: 15px;
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(120, 170, 255, 220),
                    stop:1 rgba(70, 120, 220, 220));
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(80, 130, 235, 240),
                    stop:1 rgba(40, 90, 190, 240));
            }
        """)

    def mousePressEvent(self, event):
        """Start ripple animation on click."""
        self.ripple_center = event.pos()
        self.ripple_radius = 0
        self.ripple_opacity = 255

        self.ripple_animation = QPropertyAnimation(self, b"ripple_radius")
        self.ripple_animation.setDuration(300)
        self.ripple_animation.setStartValue(0)
        self.ripple_animation.setEndValue(max(self.width(), self.height()))
        self.ripple_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.ripple_animation.valueChanged.connect(self.update)
        self.ripple_animation.start()

        super().mousePressEvent(event)

    def paintEvent(self, event):
        """Paint button with ripple effect."""
        super().paintEvent(event)

        if self.ripple_radius > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            color = QColor(255, 255, 255, int(self.ripple_opacity * (1 - self.ripple_radius / max(self.width(), self.height()))))
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))

            painter.drawEllipse(self.ripple_center, self.ripple_radius, self.ripple_radius)

            if self.ripple_animation and self.ripple_animation.state() == QPropertyAnimation.State.Running:
                self.update()

class ClipboardHistoryItem(LiquidGlassWidget):
    """Individual clipboard history item with glass effect."""

    copy_clicked = pyqtSignal(ClipboardData)

    def __init__(self, data: ClipboardData, parent=None):
        super().__init__(parent, blur_radius=15, opacity=180)
        self.data = data
        self.setup_ui()
        self.add_shadow_effect()
        self.setup_enter_animation()

    def setup_enter_animation(self):
        """Setup enter animation for the item."""
        # Fade in and slide in animation
        FadeInAnimation.fade_in(self, duration=400)
        SlideInAnimation.slide_in_from_left(self, duration=500)

    def enterEvent(self, event):
        """Handle mouse enter event with hover effect."""
        super().enterEvent(event)
        # Add subtle scale effect on hover
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        original_rect = self.geometry()
        hover_rect = QRect(
            original_rect.x() - 5,
            original_rect.y() - 2,
            original_rect.width() + 10,
            original_rect.height() + 4
        )
        self.hover_animation.setDuration(200)
        self.hover_animation.setStartValue(original_rect)
        self.hover_animation.setEndValue(hover_rect)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.hover_animation.start()

    def leaveEvent(self, event):
        """Handle mouse leave event."""
        super().leaveEvent(event)
        # Restore original size
        if hasattr(self, 'hover_animation'):
            original_rect = self.geometry()
            normal_rect = QRect(
                original_rect.x() + 5,
                original_rect.y() + 2,
                original_rect.width() - 10,
                original_rect.height() - 4
            )
            self.hover_animation.setEndValue(normal_rect)
            self.hover_animation.start()

    def setup_ui(self):
        """Setup the UI for this history item."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)

        # Header with device and time
        header_layout = QHBoxLayout()

        device_label = QLabel(f"💻 {self.data.device_name}")
        device_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        time_str = datetime.fromtimestamp(self.data.timestamp).strftime('%H:%M:%S')
        time_label = QLabel(f"🕐 {time_str}")
        time_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 11px;
            }
        """)

        header_layout.addWidget(device_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)

        # Content type and preview
        content_layout = QVBoxLayout()

        if self.data.type == ClipboardType.TEXT:
            type_label = QLabel("📝 文本")
            type_label.setStyleSheet("""
                QLabel {
                    color: #3498db;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)

            preview = self.data.content[:100] + "..." if len(self.data.content) > 100 else self.data.content
            preview_label = QLabel(preview)
            preview_label.setStyleSheet("""
                QLabel {
                    color: #34495e;
                    font-size: 12px;
                    padding: 5px;
                    background: rgba(255, 255, 255, 50);
                    border-radius: 8px;
                }
            """)
            preview_label.setWordWrap(True)

            content_layout.addWidget(type_label)
            content_layout.addWidget(preview_label)

        elif self.data.type == ClipboardType.IMAGE:
            type_label = QLabel("🖼️ 图片")
            type_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
            content_layout.addWidget(type_label)

        layout.addLayout(header_layout)
        layout.addLayout(content_layout)

        # Copy button
        copy_btn = RippleButton("📋 复制")
        copy_btn.setMaximumWidth(100)
        copy_btn.clicked.connect(lambda: self.copy_clicked.emit(self.data))
        layout.addWidget(copy_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def add_shadow_effect(self):
        """Add drop shadow effect."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

class DeviceItem(LiquidGlassWidget):
    """Device display item with online status indicator."""

    def __init__(self, device: DeviceInfo, parent=None):
        super().__init__(parent, blur_radius=12, opacity=160)
        self.device = device
        self.setup_ui()
        self.setup_enter_animation()

    def setup_enter_animation(self):
        """Setup enter animation for the device item."""
        # Fade in and slide in animation from right
        FadeInAnimation.fade_in(self, duration=400)
        SlideInAnimation.slide_in_from_right(self, duration=500)

    def enterEvent(self, event):
        """Handle mouse enter event with hover effect."""
        super().enterEvent(event)
        # Add pulse effect for online devices
        time_diff = time.time() - self.device.last_seen
        if time_diff < 30:  # Online device
            pulse_effect = PulseEffect(self, QColor(46, 204, 113, 100))
            pulse_effect.resize(self.size())
            pulse_effect.move(0, 0)
            pulse_effect.show()
            pulse_effect.start_pulse()
            # Auto-delete after animation
            QTimer.singleShot(2000, pulse_effect.deleteLater)

    def setup_ui(self):
        """Setup device item UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(5)

        # Device name and platform
        header_layout = QHBoxLayout()

        platform_colors = {
            'Windows': '#3498db',
            'Linux': '#27ae60',
            'Darwin': '#9b59b6'  # macOS
        }
        platform_color = platform_colors.get(self.device.platform, '#95a5a6')

        device_name_label = QLabel(f"🖥️ {self.device.name}")
        device_name_label.setStyleSheet(f"""
            QLabel {{
                color: {platform_color};
                font-weight: bold;
                font-size: 13px;
            }}
        """)

        platform_badge = QLabel(f"[{self.device.platform}]")
        platform_badge.setStyleSheet(f"""
            QLabel {{
                color: {platform_color};
                font-size: 10px;
                padding: 2px 6px;
                background: rgba(255, 255, 255, 100);
                border-radius: 10px;
            }}
        """)

        header_layout.addWidget(device_name_label)
        header_layout.addWidget(platform_badge)

        # IP and status
        info_layout = QHBoxLayout()

        ip_label = QLabel(f"🌐 {self.device.ip_address}")
        ip_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 10px;
            }
        """)

        # Online status
        time_diff = time.time() - self.device.last_seen
        is_online = time_diff < 30

        status_color = '#27ae60' if is_online else '#f39c12'
        status_text = '🟢 在线' if is_online else '🟡 离线'

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"""
            QLabel {{
                color: {status_color};
                font-size: 10px;
                font-weight: bold;
            }}
        """)

        info_layout.addWidget(ip_label)
        info_layout.addStretch()
        info_layout.addWidget(status_label)

        layout.addLayout(header_layout)
        layout.addLayout(info_layout)

class ModernClipboardApp(QMainWindow):
    """Modern PyQt6 main application with liquid glass UI."""

    def __init__(self):
        super().__init__()

        # Initialize clipboard manager
        self.manager = ClipboardManager()

        # Device list storage
        self.connected_devices: List[DeviceInfo] = []

        # Setup window
        self.setup_window()
        self.setup_ui()

        # Setup device callback
        self.manager.add_device_callback(self.on_device_event)

        # Start update timers
        self.setup_timers()

    def setup_window(self):
        """Setup main window properties."""
        self.setWindowTitle("🔗 SyncClip - 液态玻璃剪贴板同步")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)

        # Set window styles
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea 0%, stop:1 #764ba2 100%);
            }
        """)

    def setup_ui(self):
        """Setup the main UI."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title bar
        title_widget = self.create_title_bar()
        main_layout.addWidget(title_widget)

        # Content area with history and devices
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Clipboard history (left side)
        history_widget = self.create_history_widget()
        content_layout.addWidget(history_widget, stretch=3)

        # Device list (right side)
        device_widget = self.create_device_widget()
        content_layout.addWidget(device_widget, stretch=1)

        main_layout.addLayout(content_layout)

        # Status bar
        self.statusBar = self.create_status_bar()
        self.setStatusBar(self.statusBar)

    def create_title_bar(self):
        """Create the title bar."""
        title_frame = LiquidGlassWidget(blur_radius=25, opacity=120)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(20, 15, 20, 15)

        # App title
        title_label = QLabel("🔗 SyncClip")
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 24px;
                font-weight: bold;
            }
        """)

        # Clear history button
        clear_btn = RippleButton("🗑️ 清空历史")
        clear_btn.clicked.connect(self.clear_history)
        clear_btn.setFixedWidth(120)

        # Refresh devices button
        refresh_btn = RippleButton("🔄 刷新设备")
        refresh_btn.clicked.connect(self.refresh_devices)
        refresh_btn.setFixedWidth(120)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(refresh_btn)
        title_layout.addWidget(clear_btn)

        return title_frame

    def create_history_widget(self):
        """Create the clipboard history widget."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(15)

        # History title
        title_frame = LiquidGlassWidget(blur_radius=20, opacity=140)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel("📋 剪贴板历史")
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        self.history_count_label = QLabel("(0)")
        self.history_count_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
            }
        """)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.history_count_label)

        # History scroll area
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_scroll.setFrameStyle(QFrame.Shape.NoFrame)

        # History container
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(10, 10, 10, 10)
        self.history_layout.setSpacing(10)
        self.history_layout.addStretch()  # Push items to top

        self.history_scroll.setWidget(self.history_container)

        container_layout.addWidget(title_frame)
        container_layout.addWidget(self.history_scroll)

        return container

    def create_device_widget(self):
        """Create the device list widget."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(15)

        # Device title
        title_frame = LiquidGlassWidget(blur_radius=20, opacity=140)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel("🖥️ 连接的设备")
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        self.device_count_label = QLabel("(0)")
        self.device_count_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
            }
        """)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.device_count_label)

        # Device scroll area
        self.device_scroll = QScrollArea()
        self.device_scroll.setWidgetResizable(True)
        self.device_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.device_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.device_scroll.setFrameStyle(QFrame.Shape.NoFrame)

        # Device container
        self.device_container = QWidget()
        self.device_layout = QVBoxLayout(self.device_container)
        self.device_layout.setContentsMargins(10, 10, 10, 10)
        self.device_layout.setSpacing(10)
        self.device_layout.addStretch()  # Push items to top

        self.device_scroll.setWidget(self.device_container)

        container_layout.addWidget(title_frame)
        container_layout.addWidget(self.device_scroll)

        return container

    def create_status_bar(self):
        """Create the status bar."""
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background: rgba(255, 255, 255, 100);
                border: none;
                border-radius: 10px;
                color: #2c3e50;
                font-size: 12px;
                padding: 5px;
            }
        """)

        self.status_label = QLabel("🚀 运行中...")
        status_bar.addWidget(self.status_label)

        return status_bar

    def setup_timers(self):
        """Setup update timers."""
        # UI update timer
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(1000)  # Update every second

        # Device update timer
        self.device_timer = QTimer()
        self.device_timer.timeout.connect(self.update_devices)
        self.device_timer.start(2000)  # Update every 2 seconds

    def update_ui(self):
        """Update the clipboard history UI."""
        # Clear existing items (keep the stretch at the end)
        while self.history_layout.count() > 1:
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add current history items with staggered animations
        history = self.manager.get_history()
        for i, data in enumerate(reversed(history[-20:])):  # Show last 20 items
            item = ClipboardHistoryItem(data)
            item.copy_clicked.connect(self.copy_to_clipboard)
            self.history_layout.insertWidget(self.history_layout.count() - 1, item)

            # Staggered fade-in for each item
            delay = i * 100  # 100ms delay between each item
            FadeInAnimation.fade_in(item, duration=600, delay=delay)

        # Update counts
        self.history_count_label.setText(f"({len(history)})")
        self.status_label.setText(f"🚀 运行中... {len(history)} 条历史记录")

    def update_devices(self):
        """Update the device list UI."""
        # Clear existing items (keep the stretch at the end)
        while self.device_layout.count() > 1:
            item = self.device_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add current devices with staggered animations
        devices = self.manager.get_connected_devices()
        self.connected_devices = devices

        for i, device in enumerate(devices):
            item = DeviceItem(device)
            self.device_layout.insertWidget(self.device_layout.count() - 1, item)

            # Staggered slide-in for each device from right
            delay = i * 150  # 150ms delay between each device
            SlideInAnimation.slide_in_from_right(item, duration=500, delay=delay)
            FadeInAnimation.fade_in(item, duration=600, delay=delay)

        # Update device count
        self.device_count_label.setText(f"({len(devices)})")

    def on_device_event(self, event_type: str, device: DeviceInfo):
        """Handle device join/leave events."""
        if event_type == 'device_joined':
            self.status_label.setText(f"✅ 设备 {device.name} 已加入")
        elif event_type == 'device_left':
            self.status_label.setText(f"❌ 设备 {device.name} 已离开")

    def refresh_devices(self):
        """Trigger device discovery."""
        self.manager.discover_devices()
        self.status_label.setText("🔍 正在搜索设备...")

    def copy_to_clipboard(self, data: ClipboardData):
        """Copy data to clipboard."""
        try:
            if data.type == ClipboardType.IMAGE and isinstance(data.content, str):
                # Load image from file
                with open(data.content, 'rb') as f:
                    image_data = f.read()
                # Create new data with actual image bytes
                new_data = ClipboardData(
                    content=image_data,
                    type=data.type,
                    timestamp=data.timestamp,
                    device_name=data.device_name
                )
                self.manager.copy_to_clipboard(new_data)
            else:
                self.manager.copy_to_clipboard(data)

            self.status_label.setText(f"✅ 已复制: {data.device_name} 的内容")
        except Exception as e:
            self.status_label.setText(f"❌ 复制失败: {str(e)}")

    def clear_history(self):
        """Clear clipboard history."""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有剪贴板历史记录吗？\n此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.manager.clear_history()
            self.update_ui()

    def closeEvent(self, event):
        """Handle window closing."""
        self.manager.shutdown()
        event.accept()

def main():
    """Main entry point for the modern UI."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = ModernClipboardApp()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()