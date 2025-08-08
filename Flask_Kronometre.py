import sys
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QTabWidget, QPushButton, QInputDialog, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPainter, QColor, QPen
from math import fmod
from time import perf_counter

class AnimatedLabel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text = "00:00:00.000"
        self.hue_phase = 0.0
        self.font = QFont("Consolas", 36, QFont.Bold)
        self.setMinimumHeight(100)

    def setText(self, text):
        self.text = text
        self.update()

    def updateHue(self, delta):
        self.hue_phase = fmod(self.hue_phase + delta, 360)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        # Arka plan animasyonu (renk geçişi)
        grad_hue = fmod(self.hue_phase, 360) / 360
        c1 = QColor.fromHslF(grad_hue, 0.5, 0.9)
        c2 = QColor.fromHslF(fmod(grad_hue + 0.15,1.0), 0.6, 0.85)
        c3 = QColor.fromHslF(fmod(grad_hue + 0.3,1.0), 0.7, 0.8)

        # Yatay degrade çizimi
        for x in range(rect.width()):
            t = x / rect.width()
            if t < 0.5:
                r = c1.red() + (c2.red()-c1.red()) * (t/0.5)
                g = c1.green() + (c2.green()-c1.green()) * (t/0.5)
                b = c1.blue() + (c2.blue()-c1.blue()) * (t/0.5)
            else:
                r = c2.red() + (c3.red()-c2.red()) * ((t-0.5)/0.5)
                g = c2.green() + (c3.green()-c2.green()) * ((t-0.5)/0.5)
                b = c2.blue() + (c3.blue()-c2.blue()) * ((t-0.5)/0.5)
            painter.setPen(QColor(int(r), int(g), int(b)))
            painter.drawLine(x, 0, x, rect.height())

        # Yazı rengini hue'yu tamamlayıcı koyu ton yapalım
        text_hue = fmod(self.hue_phase + 180, 360) / 360
        text_color = QColor.fromHslF(text_hue, 0.9, 0.3)

        painter.setFont(self.font)
        painter.setPen(QPen(text_color))
        painter.drawText(rect, Qt.AlignCenter, self.text)


class ModernStopwatch(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Kronometre")
        self.resize(520, 440)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_frame)
        self.last_time = perf_counter()

        # Zamanlama
        self.elapsed_ms = 0.0
        self.target_ms = None
        self.running = False
        self.is_countdown = False

        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # Sekmeler
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Kronometre sekmesi
        stopwatch_tab = QWidget()
        st_layout = QVBoxLayout(stopwatch_tab)

        self.time_label = AnimatedLabel()
        st_layout.addWidget(self.time_label)

        # Butonlar
        btn_layout = QHBoxLayout()
        self.start_btn = self.create_button("Başlat", self.start_pause)
        self.reset_btn = self.create_button("Sıfırla", self.reset)
        self.lap_btn = self.create_button("Tur", self.add_lap)
        self.set_time_btn = self.create_button("Süre Ayarla", self.set_time)

        for w in [self.start_btn, self.reset_btn, self.lap_btn, self.set_time_btn]:
            btn_layout.addWidget(w)

        st_layout.addLayout(btn_layout)
        self.tabs.addTab(stopwatch_tab, "Kronometre")

        # Tur kayıtları sekmesi
        laps_tab = QWidget()
        laps_layout = QVBoxLayout(laps_tab)
        self.laps_list = QListWidget()
        laps_layout.addWidget(self.laps_list)
        self.tabs.addTab(laps_tab, "Tur Kayıtları")

        # Arka planı tamamen beyaz yapalım (istersen değiştir)
        self.setStyleSheet("background: #e0f0ff;")

    def create_button(self, text, slot):
        btn = QPushButton(text)
        btn.setFont(QFont("Segoe UI", 11))
        btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #89f7fe, stop:1 #66a6ff
                );
                color: white;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #66a6ff, stop:1 #89f7fe
                );
            }
        """)
        btn.clicked.connect(slot)
        return btn

    def start_pause(self):
        if not self.running:
            self.last_time = perf_counter()
            self.timer.start(16)
            self.running = True
            self.start_btn.setText("Duraklat")
        else:
            self.timer.stop()
            self.running = False
            self.start_btn.setText("Başlat")

    def reset(self):
        self.timer.stop()
        self.running = False
        self.start_btn.setText("Başlat")
        self.elapsed_ms = 0
        self.target_ms = None
        self.is_countdown = False
        self.time_label.setText("00:00:00.000")
        self.laps_list.clear()

    def add_lap(self):
        self.laps_list.insertItem(0, self.time_label.text)

    def set_time(self):
        text, ok = QInputDialog.getText(self, "Süre Ayarla", "Süre (HH:MM:SS) biçiminde girin:")
        if not ok or not text:
            return

        if not re.match(r'^\d{1,5}:\d{2}:\d{2}$', text):
            QMessageBox.warning(self, "Hatalı Format", "Lütfen HH:MM:SS formatında (örn. 24:59:59) girin.")
            return

        parts = text.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])

        if minutes >= 60 or seconds >= 60:
            QMessageBox.warning(self, "Hatalı Değer", "Dakika ve saniye 0-59 arasında olmalı.")
            return

        self.target_ms = (hours * 3600 + minutes * 60 + seconds) * 1000
        self.elapsed_ms = self.target_ms
        self.is_countdown = True
        self.update_display()
        self.laps_list.clear()

    def _on_frame(self):
        now = perf_counter()
        delta = (now - self.last_time) * 1000
        self.last_time = now

        if self.is_countdown:
            self.elapsed_ms -= delta
            if self.elapsed_ms <= 0:
                self.elapsed_ms = 0
                self.timer.stop()
                self.running = False
                self.start_btn.setText("Başlat")
        else:
            self.elapsed_ms += delta

        self.update_display()
        self.time_label.updateHue(0.7)

    def update_display(self):
        ms = int(self.elapsed_ms % 1000)
        total_seconds = int(self.elapsed_ms // 1000)
        s = total_seconds % 60
        m = (total_seconds // 60) % 60
        h = total_seconds // 3600

        self.time_label.setText(f"{h:02}:{m:02}:{s:02}.{ms:03}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernStopwatch()
    window.show()
    sys.exit(app.exec_())
