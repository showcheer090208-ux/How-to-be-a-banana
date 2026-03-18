# widgets.py
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QLinearGradient

class ArenaBackgroundWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 粒子系统：加大 dy（垂直负向速度），让星光上升得更明显
        self.particles = [[random.uniform(0, 2500), random.uniform(0, 1500), 
                           random.uniform(-0.3, 0.3), random.uniform(-1.2, -0.3), 
                           random.randint(2, 4)] for _ in range(65)]
                           
        self.grid_offset_x = 0.0
        self.grid_offset_y = 0.0
        self.hue = 210.0  
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_bg)
        self.timer.start(16) # 🔥 从 50ms 改为 16ms，实现 60 FPS 满帧刷新

    def animate_bg(self):
        # 因为帧率提高了3倍，为了防止颜色突变太快，色相步长稍微缩小为 0.1
        self.hue = (self.hue + 0.1) % 360
        
        # 网格移动速度
        self.grid_offset_x = (self.grid_offset_x + 0.5) % 60
        self.grid_offset_y = (self.grid_offset_y + 0.5) % 60
        
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            if p[1] < -10:
                p[1] = self.height() + 10
                p[0] = random.uniform(0, max(self.width(), 2000))
            p[0] = p[0] % max(self.width(), 2000)
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # --- 动态渐变背景渲染 (极光/星云效果) ---
        # 提升了HSV中的V(亮度)和降低S(饱和度)，使其成为明亮但不刺眼的护眼背景
        color1 = QColor.fromHsv(int(self.hue), 130, 90)          # 左上角主色调
        color2 = QColor.fromHsv(int((self.hue + 45) % 360), 150, 60)   # 中间过渡色（略深一点产生层次）
        color3 = QColor.fromHsv(int((self.hue + 80) % 360), 120, 110)  # 右下角提亮色
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, color1)
        gradient.setColorAt(0.5, color2)
        gradient.setColorAt(1.0, color3)
        painter.fillRect(self.rect(), gradient)
        
        # --- 高级设计图纸网格渲染 ---
        # 间距从40拉大到60，颜色改为低透明度纯白，去除黑色的脏污感
        painter.setPen(QPen(QColor(255, 255, 255, 12), 1))
        spacing = 60
        for x in range(0, self.width() + spacing, spacing):
            painter.drawLine(int(x - self.grid_offset_x), 0, int(x - self.grid_offset_x), self.height())
        for y in range(0, max(self.height(), 1500) + spacing, spacing):
            painter.drawLine(0, int(y - self.grid_offset_y), self.width(), int(y - self.grid_offset_y))
            
        # --- 带光晕的粒子渲染 ---
        for p in self.particles:
            x, y, size = int(p[0]), int(p[1]), p[4]
            
            # 1. 渲染外层光晕 (更大，更透明)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 10))
            painter.drawEllipse(x - size, y - size, size * 3, size * 3)
            
            # 2. 渲染粒子核心 (偏亮)
            painter.setBrush(QColor(255, 255, 255, 70))
            painter.drawEllipse(x, y, size, size)