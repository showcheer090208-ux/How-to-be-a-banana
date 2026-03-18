# theme.py

# ==========================================
# 1. 小窗口编辑器专属：纯净暗调样式 (实体卡片)
# ==========================================
EDITOR_STYLESHEET = """
* {
    font-family: 'Microsoft YaHei', 'SimHei', sans-serif; /* 全局无锯齿平滑字体 */
}
QDialog {
    background-color: #1e1e24; 
    color: #e0e0e0;
}
QLabel {
    color: #aeb3c0; 
    font-weight: bold;
    padding-top: 4px;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background-color: #14151a; 
    color: #ffffff;
    border: 1px solid #383a4a;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #4da8da;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #4da8da; 
    background-color: #1a1b22;
}
QComboBox::drop-down { border: none; }
QPushButton {
    background-color: #3b405a; 
    color: white;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
}
QPushButton:hover { background-color: #4f5578; }
QPushButton:pressed { background-color: #2d3145; }
QPushButton:disabled { background-color: #252838; color: #666; }

QGroupBox {
    font-size: 14px;
    font-weight: bold;
    color: #4da8da; 
    border: 1px solid #383a4a; 
    border-radius: 6px;
    margin-top: 18px; 
    padding-top: 15px;
    padding-bottom: 5px;
    background-color: #1a1b22; 
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 0 8px;
    background-color: #1e1e24; /* 和背景色一致 */
}

/* 优雅滚动条 */
QScrollBar:vertical {
    border: none; background: transparent; width: 6px; margin: 0px;
}
QScrollBar::handle:vertical {
    background: #4a4d60; min-height: 20px; border-radius: 3px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
"""

# ==========================================
# 2. 主界面专属：半透明亚克力质感 (配合背景图)
# ==========================================
MAIN_STYLESHEET = """
* {
    font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
    color: #e0e0e0;
}
QMainWindow {
    background-color: #0d0d12;
}

/* 顶部工具栏悬浮质感 */
QToolBar {
    background-color: rgba(20, 22, 30, 220); 
    border-bottom: 1px solid rgba(255, 255, 255, 20);
    padding: 4px;
    spacing: 10px;
}
QToolBar QPushButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: bold;
}
QToolBar QPushButton:hover {
    background-color: rgba(255, 255, 255, 20);
    border: 1px solid rgba(255, 255, 255, 40);
}

/* 面板分组 (毛玻璃卡片效果) */
QGroupBox {
    font-size: 14px;
    font-weight: bold;
    color: #4da8da;
    border: 1px solid rgba(255, 255, 255, 30);
    border-radius: 8px;
    margin-top: 20px;
    background-color: rgba(18, 20, 28, 110); /* 82%不透明度，透出底层背景 */
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 4px 10px;
    background-color: #2b2e40;
    border-radius: 4px;
    color: #ffffff;
}

/* 角色列表美化 */
QListWidget {
    background-color: rgba(10, 11, 16, 80);
    border: none;
    border-radius: 6px;
    padding: 5px;
    outline: none; /* 移除点击时的虚线框 */
}
QListWidget::item {
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 4px;
    background-color: rgba(255, 255, 255, 5);
}
QListWidget::item:hover {
    background-color: rgba(77, 168, 218, 50);
}
QListWidget::item:selected {
    background-color: rgba(77, 168, 218, 120);
    border-left: 4px solid #4da8da;
}

/* 文本输入区与剧本展示区 */
QTextBrowser, QTextEdit, QLineEdit, QComboBox, QSpinBox {
    background-color: rgba(10, 11, 16, 110);
    border: 1px solid rgba(255, 255, 255, 20);
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #e94560;
}
QTextBrowser:focus, QTextEdit:focus, QLineEdit:focus {
    border: 1px solid #4da8da;
    background-color: rgba(15, 17, 26, 150);
}

/* 动作按钮 (Action!) 特殊高亮 */
QPushButton#action_btn {
    background-color: #e94560;
    color: white;
    font-size: 15px;
    font-weight: bold;
    border-radius: 6px;
    padding: 10px 20px;
    border: none;
}
QPushButton#action_btn:hover { background-color: #ff5c77; }
QPushButton#action_btn:disabled { background-color: #5a2430; color: #aaa; }

/* 隐形分割条，鼠标放上去才亮起 */
QSplitter::handle {
    background: transparent;
}
QSplitter::handle:hover {
    background: #4da8da;
}
QSplitter::handle:horizontal { width: 4px; }
QSplitter::handle:vertical { height: 4px; }

/* 复用编辑器滚动条 */
QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 0px; }
QScrollBar::handle:vertical { background: rgba(255, 255, 255, 40); border-radius: 3px; }
QScrollBar::handle:vertical:hover { background: rgba(255, 255, 255, 80); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
/* 1. 设置 ComboBox 整体样式 */
QComboBox {
    background-color: #2c2c3e; /* 深色背景 */
    color: #e8eaed;           /* 浅色文字 */
    border: 1px solid #4a4a6a;
    border-radius: 6px;
    padding: 5px 10px;
    min-width: 100px;
}

/* 2. 核心修复：设置下拉列表视图的背景和文字 */
QComboBox QAbstractItemView {
    background-color: #1a1a2e; /* 下拉框展开后的背景色 */
    color: #e8eaed;           /* 下拉框文字颜色 */
    selection-background-color: #4da8da; /* 选中项的背景色 */
    selection-color: #ffffff;           /* 选中项的文字颜色 */
    outline: none;
    border: 1px solid #4a4a6a;
}

/* 3. 设置每一项的高度（解决拥挤问题） */
QComboBox QAbstractItemView::item {
    min-height: 30px;
}
/* 优化导演控制台的下拉框 */
QComboBox#genre_combo, QComboBox#len_combo {
    background-color: #252535;
    color: #00d4ff; /* 亮蓝色文字，增强可读性 */
    border: 1px solid #3d3d5d;
    selection-background-color: #3d3d5d;
}

QComboBox#genre_combo QAbstractItemView {
    background-color: #1a1a2e;
    color: #e0e0e0;
    selection-background-color: #4da8da;
    selection-color: #ffffff;
    border: 1px solid #4da8da;
}
"""