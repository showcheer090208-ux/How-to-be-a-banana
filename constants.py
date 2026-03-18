# constants.py
GLASS_QSS = """
/* 强制所有输入控件使用深色实心背景，确保文字 100% 可见 */
QTextEdit, QLineEdit, QListWidget, QComboBox, QSpinBox, QTextBrowser {
    background-color: rgba(15, 15, 25, 235) !important; 
    color: #FFFFFF !important; 
    border: 1px solid rgba(77, 168, 218, 120);
    selection-background-color: #4da8da;
    border-radius: 6px;
}

/* 列表悬停与选中样式 */
QListWidget::item:hover { background-color: rgba(77, 168, 218, 50); }
QListWidget::item:selected { background-color: rgba(77, 168, 218, 100); border: 1px solid #4da8da; }

/* 剧本展示区细节：增加内边距和行高 */
QTextBrowser {
    background-color: rgba(10, 10, 15, 245) !important;
    color: #F0F0F0;
    line-height: 1.6;
}

/* 按钮强化：高饱和度实心背景 */
QPushButton {
    background-color: rgba(45, 45, 65, 255);
    color: #FFFFFF;
    font-weight: bold;
    border: 1px solid rgba(100, 100, 150, 150);
    padding: 6px;
}
QPushButton:hover {
    background-color: rgba(77, 168, 218, 150);
    border: 1px solid #4da8da;
}
QPushButton#btn_action {
    background-color: #e94560;
}

/* 分割条与面板 */
QGroupBox {
    color: #4da8da;
    font-weight: bold;
    border: 1px solid rgba(77, 168, 218, 60);
    margin-top: 12px;
    background-color: rgba(20, 20, 30, 100);
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }

QMainWindow {
    background-color: transparent; /* 背景由 ArenaBackgroundWidget 绘制渐变 */
}

QScrollBar:vertical { width: 10px; background: transparent; }
QScrollBar::handle:vertical { background: rgba(77, 168, 218, 100); border-radius: 5px; }
"""