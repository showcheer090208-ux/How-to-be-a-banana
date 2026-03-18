# main_window.py
import re
import os
from urllib.parse import quote, unquote 
from PySide6.QtWidgets import (QMainWindow, QTextBrowser, QWidget, QVBoxLayout, QHBoxLayout,
                               QTextEdit, QLineEdit, QPushButton, QLabel,
                               QSplitter, QGroupBox, QToolBar, QComboBox, 
                               QSpinBox, QInputDialog, QScrollArea)
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QTextCursor

from tts_manager import TTSManager
import config
import memory_manager as mem
import scene_manager as sm
from settings import load_settings, save_settings
from widgets import ArenaBackgroundWidget
from dialogs import WorldEditorDialog
from worker import EngineWorker
from script_renderer import render_script_html
from theme import MAIN_STYLESHEET

# 引入抽离的观测台
from observer_panel import ObserverPanel 

# ==========================================
# 自定义指令输入框：支持 Enter 发送与 Shift+Enter 换行
# ==========================================
class DirectorInput(QTextEdit):
    submit_signal = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event) # 换行
            else:
                self.submit_signal.emit() # 发送指令
                event.accept()
        else:
            super().keyPressEvent(event)

# ==========================================
# 主窗口
# ==========================================
class ScriptStudioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 AI 剧本工作室 (物理引擎 v2.0)")
        self.resize(1280, 850)
        self.setWindowOpacity(0.98)
        
        self.settings = load_settings()
        self.fsize = self.settings.get("fsize", 16)
        
        self.genres = {
            "默认正剧": "语言干练自然，注重逻辑与写实主义。",
            "传统武侠": "文风古意盎然，注重招式拆解、杀气与内力交锋。",
            "赛博朋克": "充斥霓虹、冷雨、机油味与电子合成音。",
            "克苏鲁悬疑": "文风压抑、阴冷，充满不可名状的恐惧感。",
            "二次元轻小说": "文风轻松跳脱，多用夸张的拟声词、颜文字。",
            "黑色幽默": "以荒诞、讽刺的笔触描写悲剧或暴力。"
        }
        
        self.bg_widget = ArenaBackgroundWidget(self)
        self.setCentralWidget(self.bg_widget)
        
        self.char_colors = {}
        self.palette = ["#FFB6C1", "#87CEFA", "#98FB98", "#DDA0DD", "#FFD700", "#FF7F50", "#00FFFF"]
        
        self.init_ui()
        self.setStyleSheet(MAIN_STYLESHEET)
        self.refresh_all()
        self.update_global_font()

    def get_char_color(self, name):
        if name not in self.char_colors:
            self.char_colors[name] = self.palette[len(self.char_colors) % len(self.palette)]
        return self.char_colors[name]

    def init_ui(self):
        main_lay = QVBoxLayout(self.bg_widget)

        # 1. 顶部工具栏
        tb = QToolBar("ToolBar")
        self.addToolBar(Qt.TopToolBarArea, tb)
        b_clear = QPushButton("🧽 清屏"); b_clear.clicked.connect(self.sdis_clear_action); tb.addWidget(b_clear)
        self.tts = TTSManager()
        self.btn_tts = QPushButton("🔇 开启语音"); self.btn_tts.clicked.connect(self.toggle_tts); tb.addWidget(self.btn_tts)
        b1 = QPushButton("🌍 编辑世界法则"); b1.clicked.connect(self.edit_world); tb.addWidget(b1)
        tb.addSeparator()
        b_up = QPushButton("A+ 放大"); b_up.clicked.connect(lambda: self.change_font_size(1)); tb.addWidget(b_up)
        b_dn = QPushButton("A- 缩小"); b_dn.clicked.connect(lambda: self.change_font_size(-1)); tb.addWidget(b_dn)
        
        # 2. 主分割条
        self.main_split = QSplitter(Qt.Horizontal)
        main_lay.addWidget(self.main_split)
        
        # ================== 左侧：数据观测台 ==================
        left_widget = QWidget()
        l_lay = QVBoxLayout(left_widget)
        l_lay.setContentsMargins(0,0,0,0)
        
        # 接入独立的 ObserverPanel
        self.observer_panel = ObserverPanel(self)
        l_lay.addWidget(self.observer_panel, stretch=7)
        
        wgrp = QGroupBox("🌍 核心法则与世界线")
        w_lay = QVBoxLayout(wgrp)
        self.wdis = QTextBrowser()
        self.wdis.setStyleSheet("background-color: rgba(10, 11, 16, 80); border: none;")
        w_lay.addWidget(self.wdis)
        l_lay.addWidget(wgrp, stretch=2)
        
        # ================== 右侧：剧本 + 控制台 ==================
        right_widget = QWidget()
        r_lay = QVBoxLayout(right_widget)
        r_lay.setContentsMargins(0,0,0,0)
        self.right_split = QSplitter(Qt.Vertical)
        self.right_split.setStyleSheet("QSplitter::handle { background: transparent; }")
        
        # 剧本正文
        script_grp = QGroupBox("📜 剧本正文推演区")
        script_lay = QVBoxLayout(script_grp)
        self.sdis = QTextBrowser()
        self.sdis.setOpenExternalLinks(False)
        self.sdis.anchorClicked.connect(self.on_branch_clicked)
        script_lay.addWidget(self.sdis)
        
        # 导演控制台 (包含 Hotbar 和 比例自适应的输入区)
        bot_grp = QGroupBox("🎬 导演指令台")
        bot_main_lay = QVBoxLayout(bot_grp) 
        
        # [动态物件槽 Hotbar]
        self.hotbar_widget = QWidget()
        self.hotbar_layout = QHBoxLayout(self.hotbar_widget)
        self.hotbar_layout.setContentsMargins(0, 0, 0, 0)
        self.hotbar_layout.setAlignment(Qt.AlignLeft)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.hotbar_widget)
        scroll.setMaximumHeight(45)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        bot_main_lay.addWidget(scroll)

        # [输入控制台] 
        controls_lay = QHBoxLayout()
        
        self.chap_spin = QSpinBox()
        self.chap_spin.setPrefix("第 "); self.chap_spin.setSuffix(" 章")
        self.chap_spin.setMinimum(1); self.chap_spin.setMaximum(9999)
        self.chap_spin.setFixedWidth(80)
        controls_lay.addWidget(self.chap_spin, stretch=0)

        self.tin = QLineEdit()
        self.tin.setPlaceholderText("标题/事件")
        self.tin.setFixedWidth(120)
        controls_lay.addWidget(self.tin, stretch=0)
        
        self.len_combo = QComboBox()
        self.len_combo.addItems(["短", "中", "长"]); self.len_combo.setCurrentText("中")
        self.len_combo.setFixedWidth(60)
        controls_lay.addWidget(self.len_combo, stretch=0)
        
        self.genre_combo = QComboBox()
        self.genre_combo.addItems(list(self.genres.keys()))
        self.genre_combo.setFixedWidth(100)
        controls_lay.addWidget(self.genre_combo, stretch=0)
        
        self.din = DirectorInput()
        self.din.setPlaceholderText("⏎ 发送 / ⇧⏎ 换行 | 填入神明旨意或环境变化...")
        self.din.setMinimumHeight(50)
        self.din.submit_signal.connect(self.go) 
        controls_lay.addWidget(self.din, stretch=1) 
        
        self.btn = QPushButton("🚀 Action!")
        self.btn.setObjectName("action_btn")
        self.btn.setFixedWidth(100)
        self.btn.clicked.connect(self.go)
        controls_lay.addWidget(self.btn, stretch=0)
        
        bot_main_lay.addLayout(controls_lay)
        
        # 加入分割条
        self.right_split.addWidget(script_grp)
        self.right_split.addWidget(bot_grp)
        self.right_split.setStretchFactor(0, 4) 
        self.right_split.setStretchFactor(1, 1)
        r_lay.addWidget(self.right_split)
        
        self.main_split.addWidget(left_widget)
        self.main_split.addWidget(right_widget)
        self.main_split.setStretchFactor(0, 2) 
        self.main_split.setStretchFactor(1, 8) 

    # ================= 联动交互 =================
    def update_hotbar(self, objects_dict):
        """当左侧点击场景时，更新顶部的动态物件槽"""
        for i in reversed(range(self.hotbar_layout.count())): 
            widget = self.hotbar_layout.itemAt(i).widget()
            if widget is not None: widget.deleteLater()
            
        if not objects_dict:
            lbl = QLabel("<span style='color:gray; font-size:12px;'>当前场景无特殊物件...</span>")
            self.hotbar_layout.addWidget(lbl)
            return
            
        for obj_name, obj_data in objects_dict.items():
            owner = obj_data.get("owner")
            owner_str = f" ({owner})" if owner else ""
            btn = QPushButton(f"📦 {obj_name}{owner_str}")
            btn.setStyleSheet("background-color: rgba(77, 168, 218, 50); color: #4da8da; border: 1px solid #4da8da; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
            # 点击物件快速填入指令框
            btn.clicked.connect(lambda checked, n=obj_name: self.insert_to_din(f"[{n}]"))
            self.hotbar_layout.addWidget(btn)

    def insert_to_din(self, text):
        cursor = self.din.textCursor()
        cursor.insertText(text + " ")
        self.din.setFocus()

    def refresh_all(self):
        """全局刷新数据"""
        self.observer_panel.refresh()
        
        wd = mem.load_world_state()
        stats_info = wd.get('global_stats', {})
        stats_display = " | ".join([f"<b style='color:#f39c12;'>{k}</b>: {v}" for k, v in stats_info.items()])
        history = "<br>".join(wd.get('chapter_summaries', [])[-3:])
        
        self.wdis.setHtml(f"<b>【📈 动态数值面板】</b><br>{stats_display}<br><br><b>【📖 最近发生的事】</b><br><span style='color:gray;'>{history}</span>")
        self.chap_spin.setValue(len(wd.get('chapter_summaries', [])) + 1)

    @Slot(dict)
    def update_live_data(self, data):
        self.refresh_all() 

    # ================= 业务逻辑 =================
    def new_char(self):
        n, ok = QInputDialog.getText(self, "新建", "角色名字:")
        if ok and n:
            mem.save_character(n, {"name": n, "role_weight": "配角", "profile": "新登场...", "faction": "中立", "last_known_location": "未知", "current_status": "正常", "memories": []})
            self.refresh_all()

    def edit_world(self):
        if WorldEditorDialog(self).exec(): self.refresh_all()

    def go(self):
        t, d = self.tin.text() or "未命名", self.din.toPlainText()
        if not d.strip(): return
        self.btn.setEnabled(False); self.btn.setText("🎥 推演中...")
        current_chap = self.chap_spin.value()
        genre_prompt = self.genres.get(self.genre_combo.currentText(), "常规文风")
        
        self.sdis.clear()
        self.sdis.insertHtml(f"<h2 style='color:#e94560; text-align:center;'>=== 第 {current_chap} 章：{t} ===</h2><br>")
        
        self.worker = EngineWorker(current_chap, t, d, self.len_combo.currentText(), genre_prompt)
        self.worker.text_updated.connect(self.append_txt)
        self.worker.chapter_finished.connect(self.done)
        self.worker.data_changed.connect(self.update_live_data) 
        self.worker.start()
        
        # 发送后清空输入框
        self.din.clear()

    def sdis_clear_action(self):
        self.sdis.clear()
        self.sdis.insertHtml("<div style='color:gray; text-align:center;'>--- 屏幕已清理 ---</div><br>")

    def toggle_tts(self):
        is_muted = not self.tts.muted
        self.tts.set_mute(is_muted)
        self.btn_tts.setText("🔊 语音开启" if not is_muted else "🔇 开启语音")

    @Slot(str)
    def on_branch_clicked(self, url):
        raw_text = url if isinstance(url, str) else url.toString()
        self.insert_to_din(unquote(raw_text))

    def done(self, script, branches):
        cursor = self.sdis.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.sdis.setTextCursor(cursor)
        self.sdis.insertHtml("<br><hr style='border: 1px dashed #3a3a5a; margin: 20px 0;'><br>")

        if branches:
            self.sdis.insertHtml("<div style='color:#f1c40f; font-weight:bold; margin-bottom:10px;'>🌟 神明提示：后续剧情建议（点击填入）：</div>")
            options = [opt.strip() for opt in re.split(r'\n+', branches) if opt.strip()] if isinstance(branches, str) else branches
            for opt in options:
                pure_text = re.sub(r'^[A-Za-z0-9][\.、\s：]+', '', opt).strip()
                self.sdis.insertHtml(f"<div style='margin: 10px 0; padding-left: 10px; border-left: 3px solid #4da8da;'><a href='{quote(pure_text)}' style='color: #4da8da; text-decoration: none; font-size: 14px;'>➤ {opt}</a></div>")

        mem.save_script_chapter(self.chap_spin.value(), self.tin.text().strip() or "未命名章节", self.sdis.toHtml())
        self.btn.setEnabled(True)
        self.btn.setText("🚀 Action!")
        self.sdis.verticalScrollBar().setValue(self.sdis.verticalScrollBar().maximum())
        self.refresh_all()
        if not getattr(self.tts, 'muted', True):
            self.tts.add_task("系统", "推演结束，请指示后续走向。")

    def update_global_font(self):
        font = self.sdis.font(); font.setPointSize(self.fsize); self.sdis.setFont(font)

    def change_font_size(self, delta):
        self.fsize = max(10, min(36, self.fsize + delta))
        self.settings["fsize"] = self.fsize; save_settings(self.settings)
        self.update_global_font()

    def append_txt(self, t):
        s = self.sdis.verticalScrollBar()
        is_at_bottom = s.value() >= (s.maximum() - 50)
        saved_value = s.value()

        html = render_script_html(t, self.fsize, self.get_char_color)
        if html:
            cursor = self.sdis.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.sdis.setTextCursor(cursor)
            self.sdis.insertHtml(html + "<br>")
            clean = re.sub(r'<[^>]+>', '', t).strip()
            if clean and not self.tts.muted: 
                self.tts.add_task(clean.split('】')[0].strip('【') if '】' in clean else "旁白", clean)
        
        if is_at_bottom: s.setValue(s.maximum())
        else: s.setValue(saved_value)