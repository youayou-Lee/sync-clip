"""Enhanced animations and effects for the liquid glass UI."""
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, QRect, QPoint, QTimer, pyqtSignal
)
from PyQt6.QtGui import QPainter, QColor, QPen

class FloatingWidget(QWidget):
    """Widget with gentle floating animation effect."""

    def __init__(self, parent=None, float_range=5, duration=4000):
        super().__init__(parent)
        self.float_range = float_range
        self.duration = duration
        self.original_y = 0
        self.setup_animation()

    def setup_animation(self):
        """Setup floating animation."""
        self.float_animation = QPropertyAnimation(self, b"pos")
        self.float_animation.setDuration(self.duration)
        self.float_animation.setLoopCount(-1)  # Infinite loop

        # Create floating path
        self.float_animation.setKeyValueAt(0.0, QPoint(self.x(), self.original_y))
        self.float_animation.setKeyValueAt(0.25, QPoint(self.x(), self.original_y - self.float_range))
        self.float_animation.setKeyValueAt(0.5, QPoint(self.x(), self.original_y))
        self.float_animation.setKeyValueAt(0.75, QPoint(self.x(), self.original_y + self.float_range))
        self.float_animation.setKeyValueAt(1.0, QPoint(self.x(), self.original_y))

        self.float_animation.setEasingCurve(QEasingCurve.Type.InOutSine)

    def start_floating(self):
        """Start the floating animation."""
        self.original_y = self.y()
        self.float_animation.start()

class PulseEffect(QWidget):
    """Widget with pulse animation effect."""

    def __init__(self, parent=None, pulse_color=QColor(100, 150, 255, 100)):
        super().__init__(parent)
        self.pulse_color = pulse_color
        self.pulse_radius = 0
        self.pulse_opacity = 0
        self.pulse_animation = None
        self.setAttribute(self.__class__.WA_TransparentForMouseEvents)

    def start_pulse(self):
        """Start pulse animation."""
        self.pulse_radius = 0
        self.pulse_opacity = 200

        self.pulse_animation = QPropertyAnimation(self, b"pulse_radius")
        self.pulse_animation.setDuration(1500)
        self.pulse_animation.setStartValue(0)
        self.pulse_animation.setEndValue(max(self.width(), self.height()))
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.pulse_animation.valueChanged.connect(self.update)
        self.pulse_animation.start()

        # Fade out animation
        opacity_anim = QPropertyAnimation(self, b"pulse_opacity")
        opacity_anim.setDuration(1500)
        opacity_anim.setStartValue(200)
        opacity_anim.setEndValue(0)
        opacity_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        opacity_anim.valueChanged.connect(self.update)
        opacity_anim.start()

    def paintEvent(self, event):
        """Paint pulse effect."""
        if self.pulse_radius > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            color = QColor(self.pulse_color)
            color.setAlpha(int(self.pulse_opacity * (1 - self.pulse_radius / max(self.width(), self.height()))))
            painter.setPen(QPen(color, 3))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(
                self.width() // 2,
                self.height() // 2,
                self.pulse_radius,
                self.pulse_radius
            )

class SlideInAnimation:
    """Helper class for slide-in animations."""

    @staticmethod
    def slide_in_from_left(widget, duration=300, delay=0):
        """Slide widget in from left."""
        if delay > 0:
            QTimer.singleShot(delay, lambda: SlideInAnimation._slide_in_from_left(widget, duration))
        else:
            SlideInAnimation._slide_in_from_left(widget, duration)

    @staticmethod
    def _slide_in_from_left(widget, duration):
        """Internal slide-in implementation."""
        original_x = widget.x()
        widget.move(-widget.width(), widget.y())
        widget.show()

        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(QPoint(-widget.width(), widget.y()))
        animation.setEndValue(QPoint(original_x, widget.y()))
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()

    @staticmethod
    def slide_in_from_right(widget, duration=300, delay=0):
        """Slide widget in from right."""
        if delay > 0:
            QTimer.singleShot(delay, lambda: SlideInAnimation._slide_in_from_right(widget, duration))
        else:
            SlideInAnimation._slide_in_from_right(widget, duration)

    @staticmethod
    def _slide_in_from_right(widget, duration):
        """Internal slide-in implementation."""
        original_x = widget.x()
        parent_width = widget.parent().width() if widget.parent() else 800
        widget.move(parent_width, widget.y())
        widget.show()

        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(QPoint(parent_width, widget.y()))
        animation.setEndValue(QPoint(original_x, widget.y()))
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()

    @staticmethod
    def slide_in_from_top(widget, duration=300, delay=0):
        """Slide widget in from top."""
        if delay > 0:
            QTimer.singleShot(delay, lambda: SlideInAnimation._slide_in_from_top(widget, duration))
        else:
            SlideInAnimation._slide_in_from_top(widget, duration)

    @staticmethod
    def _slide_in_from_top(widget, duration):
        """Internal slide-in implementation."""
        original_y = widget.y()
        widget.move(widget.x(), -widget.height())
        widget.show()

        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(QPoint(widget.x(), -widget.height()))
        animation.setEndValue(QPoint(widget.x(), original_y))
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()

class FadeInAnimation:
    """Helper class for fade-in animations."""

    @staticmethod
    def fade_in(widget, duration=300, delay=0):
        """Fade in widget."""
        if delay > 0:
            QTimer.singleShot(delay, lambda: FadeInAnimation._fade_in(widget, duration))
        else:
            FadeInAnimation._fade_in(widget, duration)

    @staticmethod
    def _fade_in(widget, duration):
        """Internal fade-in implementation."""
        opacity_effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(opacity_effect)
        widget.hide()

        opacity_animation = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_animation.setDuration(duration)
        opacity_animation.setStartValue(0.0)
        opacity_animation.setEndValue(1.0)
        opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        widget.show()
        opacity_animation.start()

class ParticleSystem(QWidget):
    """Simple particle system for background effects."""

    def __init__(self, parent=None, particle_count=20):
        super().__init__(parent)
        self.particle_count = particle_count
        self.particles = []
        self.setup_particles()
        self.setAttribute(self.__class__.WA_TransparentForMouseEvents)

    def setup_particles(self):
        """Setup initial particles."""
        import random
        for _ in range(self.particle_count):
            particle = {
                'x': random.randint(0, self.width() or 800),
                'y': random.randint(0, self.height() or 600),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'size': random.uniform(2, 6),
                'opacity': random.uniform(30, 100)
            }
            self.particles.append(particle)

    def update_particles(self):
        """Update particle positions."""
        import random
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']

            # Bounce off walls
            if particle['x'] <= 0 or particle['x'] >= (self.width() or 800):
                particle['vx'] *= -1
            if particle['y'] <= 0 or particle['y'] >= (self.height() or 600):
                particle['vy'] *= -1

            # Random walk
            particle['vx'] += random.uniform(-0.1, 0.1)
            particle['vy'] += random.uniform(-0.1, 0.1)

            # Limit velocity
            particle['vx'] = max(-2, min(2, particle['vx']))
            particle['vy'] = max(-2, min(2, particle['vy']))

        self.update()

    def paintEvent(self, event):
        """Paint particles."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for particle in self.particles:
            color = QColor(255, 255, 255, int(particle['opacity']))
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(
                int(particle['x']),
                int(particle['y']),
                int(particle['size']),
                int(particle['size'])
            )

class AnimatedBackground(QWidget):
    """Animated gradient background."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gradient_offset = 0
        self.setup_animation()

    def setup_animation(self):
        """Setup gradient animation."""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_gradient)
        self.animation_timer.start(50)  # Update every 50ms

    def update_gradient(self):
        """Update gradient animation."""
        self.gradient_offset = (self.gradient_offset + 1) % 360
        self.update()

    def paintEvent(self, event):
        """Paint animated gradient."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create animated gradient
        from PyQt6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, self.width(), self.height())

        # Animated color stops
        import math
        hue1 = (self.gradient_offset) % 360
        hue2 = (self.gradient_offset + 60) % 360

        from PyQt6.QtGui import QColor
        color1 = QColor.fromHsv(hue1, 70, 90)
        color2 = QColor.fromHsv(hue2, 70, 80)

        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)

        painter.fillRect(self.rect(), gradient)