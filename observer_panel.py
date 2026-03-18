import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QGroupBox, QPushButton, QTextBrowser, QTabWidget, QMenu, QInputDialog, QMessageBox, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import memory_manager as mem
import scene_manager as sm
from dialogs import CharacterEditorDialog
import config

class ObserverPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { height: 32px; width: 110px; font-weight: bold; }")
        
        # 【角色 Tab】
        char_tab = QWidget()
        char_lay = QVBoxLayout(char_tab)
        char_lay.setContentsMargins(5, 10, 5, 5)
        
        self.btn_new_char = QPushButton("➕ 新建角色")
        self.btn_new_char.setStyleSheet("background-color: #3b405a; color: white; padding: 6px; border-radius: 4px;")
        self.btn_new_char.clicked.connect(self.main_window.new_char)
        
        self.char_list = QListWidget()
        self.char_list.setStyleSheet("QListWidget { background-color: rgba(10, 11, 16, 80); border: none; }")
        self.char_list.itemClicked.connect(self.on_char_clicked)
        self.char_list.itemDoubleClicked.connect(self.edit_char)
        self.char_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.char_list.customContextMenuRequested.connect(self.char_context_menu)
        
        char_lay.addWidget(self.btn_new_char)
        char_lay.addWidget(self.char_list)
        self.tabs.addTab(char_tab, "🎭 角色")
        
        # 【场景 Tab】
        scene_tab = QWidget()
        scene_lay = QVBoxLayout(scene_tab)
        scene_lay.setContentsMargins(5, 10, 5, 5)
        
        self.btn_new_scene = QPushButton("🗺️ 新建场景")
        self.btn_new_scene.setStyleSheet("background-color: #3b405a; color: white; padding: 6px; border-radius: 4px;")
        self.btn_new_scene.clicked.connect(self.new_scene)
        
        self.scene_list = QListWidget()
        self.scene_list.setStyleSheet("QListWidget { background-color: rgba(10, 11, 16, 80); border: none; }")
        self.scene_list.itemClicked.connect(self.on_scene_clicked)
        self.scene_list.itemDoubleClicked.connect(self.edit_scene)
        self.scene_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scene_list.customContextMenuRequested.connect(self.scene_context_menu)
        
        scene_lay.addWidget(self.btn_new_scene)
        scene_lay.addWidget(self.scene_list)
        self.tabs.addTab(scene_tab, "🏞️ 场景")
        
        layout.addWidget(self.tabs, stretch=7)

        # 【详情展示区】
        self.detail_grp = QGroupBox("🔍 实时观测详情")
        detail_lay = QVBoxLayout(self.detail_grp)
        
        self.detail_view = QTextBrowser()
        self.detail_view.setStyleSheet("background-color: rgba(10, 11, 16, 110); border: 1px solid rgba(255,255,255,20); border-radius: 6px; padding: 8px;")
        self.detail_view.setHtml("<span style='color:gray;'>请选择上方列表中的角色或场景...</span>")
        detail_lay.addWidget(self.detail_view)
        
        layout.addWidget(self.detail_grp, stretch=3)

    def refresh(self):
        self.refresh_chars()
        self.refresh_scenes()

    def refresh_chars(self):
        self.char_list.clear()
        if os.path.exists(config.CHAR_DIR):
            for f in os.listdir(config.CHAR_DIR):
                if f.endswith(".json"):
                    name = f.replace(".json", "")
                    c_data = mem.load_character(name)
                    item = QListWidgetItem(f"🎭 {name} | 📍 {c_data.get('last_known_location', '未知')}")
                    item.setData(Qt.UserRole, name)
                    item.setForeground(QColor("#FFFFFF"))
                    self.char_list.addItem(item)

        for temp_name in mem.get_all_temp():
            t_data = mem.get_temp_character(temp_name)
            item = QListWidgetItem(f"👻 {temp_name} (临时) | 📍 {t_data.get('last_location', '未知')}")
            item.setData(Qt.UserRole, temp_name)
            item.setForeground(QColor("#00d4ff")) 
            self.char_list.addItem(item)

    def refresh_scenes(self):
        self.scene_list.clear()
        scenes = sm.load_all_scenes()
        for s_name, s_data in scenes.items():
            pos_count = len(s_data.get("positions", {}))
            obj_count = len(s_data.get("objects", {}))
            item = QListWidgetItem(f"🏞️ {s_name} (👤{pos_count} 📦{obj_count})")
            item.setData(Qt.UserRole, s_name)
            self.scene_list.addItem(item)

    def on_char_clicked(self, item):
        name = item.data(Qt.UserRole)
        is_formal = mem.character_exists(name)
        
        if is_formal:
            c_data = mem.load_character(name)
            mems = "<br>".join([f"- {m}" for m in c_data.get("memories", [])[-3:]])
            html = (
                f"<b style='color:#4da8da; font-size:16px;'>🎭 {name}</b><br><br>"
                f"<b style='color:#f39c12;'>[身心状态]</b> {c_data.get('current_status', '正常')}<br>"
                f"<b style='color:#f39c12;'>[阵营定位]</b> {c_data.get('faction', '中立')} | {c_data.get('role_weight', '配角')}<br>"
                f"<b style='color:#f39c12;'>[综合人设]</b> {c_data.get('profile', '')[:60]}...<br><br>"
                f"<b style='color:#f39c12;'>[最近记忆]</b><br><span style='color:#a0a0a0;'>{mems}</span>"
            )
        else:
            t_data = mem.get_temp_character(name)
            acts = "<br>".join([f"- {a}" for a in t_data.get("notable_actions", [])[-3:]])
            html = (
                f"<b style='color:#00d4ff; font-size:16px;'>👻 {name} (临时)</b><br><br>"
                f"<b style='color:#f39c12;'>[出场数据]</b> 出场 {t_data.get('appearances', 0)} 次<br>"
                f"<b style='color:#f39c12;'>[互动角色]</b> {len(t_data.get('interactions', []))} 人<br><br>"
                f"<b style='color:#f39c12;'>[显著行为]</b><br><span style='color:#a0a0a0;'>{acts or '无'}</span>"
            )
            
        self.detail_view.setHtml(html)

    def on_scene_clicked(self, item):
        name = item.data(Qt.UserRole)
        s_data = sm.load_scene(name)
        
        if hasattr(self.main_window, 'update_hotbar'):
            self.main_window.update_hotbar(s_data.get("objects", {}))

        chars = ", ".join(s_data.get("positions", {}).keys()) or "空无一人"
        objs = "<br>".join([f"- {k}: {v.get('status', '')} {v.get('owner', '')}" for k, v in s_data.get("objects", {}).items()]) or "无特殊物件"
        
        html = (
            f"<b style='color:#00FF7F; font-size:16px;'>🏞️ {name}</b><br><br>"
            f"<b style='color:#f39c12;'>[在场人员]</b> {chars}<br><br>"
            f"<b style='color:#f39c12;'>[物理契约 (Layout)]</b><br><span style='color:#a0a0a0;'>{s_data.get('layout_text', '无')}</span><br><br>"
            f"<b style='color:#f39c12;'>[环境参数]</b> {s_data.get('environment', '默认')}<br><br>"
            f"<b style='color:#f39c12;'>[场景资产]</b><br><span style='color:#a0a0a0;'>{objs}</span>"
        )
        self.detail_view.setHtml(html)

    def char_context_menu(self, pos):
        item = self.char_list.itemAt(pos)
        if not item: return
        name = item.data(Qt.UserRole)
        is_formal = mem.character_exists(name)
        
        m = QMenu(self)
        if is_formal:
            char_data = mem.load_character(name)
            a_edit = m.addAction("📝 完整编辑")
            a_move = m.addAction("📍 强制转移")
            a_kill = m.addAction("💀 强制杀青")
            
            action = m.exec(self.char_list.mapToGlobal(pos))
            if action == a_edit: 
                self.edit_char(item)
            elif action == a_move:
                dlg = QInputDialog(self)
                dlg.setWindowTitle("神明干涉"); dlg.setLabelText("转移至:"); dlg.setTextValue(char_data.get("last_known_location", ""))
                if dlg.exec() == QDialog.Accepted:
                    new_loc = dlg.textValue().strip()
                    old_loc = char_data.get("last_known_location", "")
                    
                    # 深度修复：调用底层的统一搬运接口，确保角色的物品被一起转移
                    if new_loc and new_loc != old_loc:
                        sm.move_actor(name, old_loc, new_loc)
                        char_data["last_known_location"] = new_loc
                        mem.save_character(name, char_data)
                        self.main_window.refresh_all()
                        
            elif action == a_kill:
                if QMessageBox.question(self, '确认', f"让【{name}】杀青？") == QMessageBox.Yes:
                    old_loc = char_data.get("last_known_location", "未知")
                    mem.archive_character(name)
                    
                    # 深度修复：同时将角色名从当前站立的场景数据里抹除，防止诈尸
                    scenes = sm.load_all_scenes()
                    if old_loc in scenes and name in scenes[old_loc].get("positions", {}):
                        del scenes[old_loc]["positions"][name]
                        sm.save_scene(old_loc, scenes[old_loc])
                        
                    self.main_window.refresh_all()
        else:
            a_promote = m.addAction("⭐ 提拔为正式角色")
            action = m.exec(self.char_list.mapToGlobal(pos))
            if action == a_promote:
                if mem.promote_temp(name):
                    QMessageBox.information(self, "成功", f"【{name}】已转正，并获得独立档案！")
                    self.main_window.refresh_all()

    def scene_context_menu(self, pos):
        item = self.scene_list.itemAt(pos)
        if not item: return
        m = QMenu(self)
        a_edit = m.addAction("✏️ 编辑场景规则")
        action = m.exec(self.scene_list.mapToGlobal(pos))
        if action == a_edit: self.edit_scene(item)

    def edit_char(self, item):
        name = item.data(Qt.UserRole)
        if mem.character_exists(name):
            if CharacterEditorDialog(name, self).exec(): self.main_window.refresh_all()
        else:
            QMessageBox.warning(self, "提示", "临时角色无法直接编辑，请先右键将其转正。")

    def edit_scene(self, item):
        from scene_editor import SceneEditorDialog
        name = item.data(Qt.UserRole)
        if SceneEditorDialog(name, self).exec(): 
            self.main_window.refresh_all()

    def new_scene(self):
        n, ok = QInputDialog.getText(self, "新建场景", "场景名称:")
        if ok and n:
            sm.save_scene(n, {"layout_text": f"[{n} 的场地]", "objects": {}, "positions": {}})
            self.refresh_scenes()