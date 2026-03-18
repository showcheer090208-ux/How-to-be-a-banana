# dialogs.py
from PySide6.QtWidgets import (QDialog, QFormLayout, QVBoxLayout, QHBoxLayout,
                               QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox)
import memory_manager as mem
from llm_client import call_llm
from PySide6.QtWidgets import QGroupBox
from theme import EDITOR_STYLESHEET
# ==========================================

class CharacterEditorDialog(QDialog):
    def __init__(self, char_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"编辑: {char_name}")
        self.resize(650, 850) # 稍微加长一点，适应分组后的呼吸感
        self.char_name = char_name
        self.data = mem.load_character(char_name)
        
        self.setStyleSheet(EDITOR_STYLESHEET)
        
        # 外层主布局：垂直排列
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ==========================================
        # 模块 1: 🎭 基础设定
        # ==========================================
        group_basic = QGroupBox("🎭 基础设定")
        form_basic = QFormLayout(group_basic)
        form_basic.setSpacing(10)
        
        self.weight_combo = QComboBox()
        self.weight_combo.addItems(["主角", "重要配角", "龙套炮灰"])
        self.weight_combo.setCurrentText(self.data.get("role_weight", "配角"))
        form_basic.addRow("剧本定位/权重:", self.weight_combo)
        
        self.faction = QLineEdit(self.data.get("faction", ""))
        form_basic.addRow("阵营:", self.faction)

        self.location = QLineEdit(self.data.get("last_known_location", "未知"))
        self.location.setPlaceholderText("例如：反派密室、主角客房...")
        form_basic.addRow("当前舞台/位置:", self.location)
        
        self.status_edit = QLineEdit(self.data.get("current_status", "正常"))
        self.status_edit.setPlaceholderText("例如：重伤昏迷、极度饥饿...")
        form_basic.addRow("当前身心状态:", self.status_edit)
        
        main_layout.addWidget(group_basic)

        # ==========================================
        # 模块 2: 📖 深度刻画
        # ==========================================
        group_profile = QGroupBox("📖 深度刻画")
        form_profile = QFormLayout(group_profile)
        form_profile.setSpacing(10)
        
        self.profile = QTextEdit()
        self.profile.setPlainText(self.data.get("profile", ""))
        self.profile.setMinimumHeight(100)
        form_profile.addRow("综合人设:", self.profile)
        
        self.goal = QTextEdit()
        self.goal.setPlainText(self.data.get("hidden_goal", ""))
        self.goal.setMaximumHeight(50)
        form_profile.addRow("隐藏目标:", self.goal)
        
        main_layout.addWidget(group_profile)

        # ==========================================
        # 模块 3: 🕸️ 羁绊与过往
        # ==========================================
        group_memories = QGroupBox("🕸️ 羁绊与过往")
        form_memories = QFormLayout(group_memories)
        form_memories.setSpacing(10)
        
        self.mems = QTextEdit()
        self.mems.setPlainText("\n".join(self.data.get("memories", [])))
        self.mems.setMinimumHeight(70)
        form_memories.addRow("重大过往(每行一条):", self.mems)
        
        rels = self.data.get("relationships", {})
        rel_lines = [f"{k} | {v.get('关系', '未知')} | {v.get('好感度', 0)}" for k, v in rels.items()]
        self.rels_edit = QTextEdit()
        self.rels_edit.setPlainText("\n".join(rel_lines))
        self.rels_edit.setMinimumHeight(70)
        self.rels_edit.setPlaceholderText("格式示例:\n张三 | 生死之交 | 90")
        form_memories.addRow("人际关系:", self.rels_edit)
        
        main_layout.addWidget(group_memories)

        # ==========================================
        # 底部操作区 (AI功能与保存)
        # ==========================================
        self.original_profile = ""
        btn_layout = QHBoxLayout()
        
        self.btn_ai = QPushButton("✨ AI 压缩提炼人设")
        self.btn_ai.setStyleSheet("background-color: #8e44ad; font-size: 13px;")
        self.btn_ai.clicked.connect(self.ai_compress_memories)
        
        self.btn_undo = QPushButton("↩️ 撤销更改")
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo_summarize)
        
        btn_layout.addWidget(self.btn_ai)
        btn_layout.addWidget(self.btn_undo)
        main_layout.addLayout(btn_layout)
        
        btn_save = QPushButton("💾 保存所有修改")
        btn_save.setStyleSheet("background-color: #e94560; font-size: 14px; padding: 10px; margin-top: 10px;")
        btn_save.clicked.connect(self.save)
        main_layout.addWidget(btn_save)

    def ai_compress_memories(self):
        """手动压缩记忆"""
        current_mems = self.mems.toPlainText()
        if not current_mems:
            return
    
        self.btn_ai.setText("⏳ 压缩中...")
        self.btn_ai.setEnabled(False)
    
        prompt = "将以下记忆列表压缩为简短的最核心的人生转折，保留第一人称，直接输出每行一条："
        compressed = call_llm("记忆压缩", prompt, current_mems)
    
        if compressed:
            self.mems.setPlainText(compressed)
    
        self.btn_ai.setText("✨ AI 压缩记忆")
        self.btn_ai.setEnabled(True)

    def undo_summarize(self):
        self.profile.setPlainText(self.original_profile)
        self.btn_undo.setEnabled(False)

    def save(self):
        rel_text = self.rels_edit.toPlainText().strip()
        new_rels = {}
        for line in rel_text.split('\n'):
            line = line.strip()
            if not line: continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 1:
                target = parts[0]
                relation = parts[1] if len(parts) > 1 else "未知"
                try:
                    favorability = int(parts[2]) if len(parts) > 2 else 0
                except ValueError:
                    favorability = 0
                new_rels[target] = {"关系": relation, "好感度": favorability}

        self.data.update({
            "role_weight": self.weight_combo.currentText(),
            "profile": self.profile.toPlainText().strip(),
            "faction": self.faction.text().strip(),
            "last_known_location": self.location.text().strip(), 
            "current_status": self.status_edit.text().strip(), 
            "hidden_goal": self.goal.toPlainText().strip(),
            "memories": [m.strip() for m in self.mems.toPlainText().split('\n') if m.strip()],
            "relationships": new_rels
        })
        mem.save_character(self.char_name, self.data)
        self.accept()


class WorldEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑世界观与核心数据")
        self.resize(700, 800)
        self.data = mem.load_world_state()
        self.setStyleSheet(EDITOR_STYLESHEET)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 25, 25, 25)
        
        def add_box(title, key):
            te = QTextEdit()
            te.setPlainText(self.data.get(key, ""))
            layout.addWidget(QLabel(title))
            layout.addWidget(te)
            return te
            
        self.bg_edit = add_box("背景:", "background")
        self.rules_edit = add_box("核心法则/禁忌:", "core_rules")
        self.factions_edit = add_box("势力分布:", "factions_info")
        
        self.stats_edit = QTextEdit()
        self.stats_edit.setMaximumHeight(80)
        stats_str = "\n".join([f"{k}: {v}" for k, v in self.data.get("global_stats", {}).items()])
        self.stats_edit.setPlainText(stats_str)
        layout.addWidget(QLabel("📈 核心动态数据 (如 倒计时: 3天，理智值: 80。每行一项，在此定死规则):"))
        layout.addWidget(self.stats_edit)
        
        self.summary_edit = QTextEdit()
        self.summary_edit.setPlainText("\n".join(self.data.get("chapter_summaries", [])))
        layout.addWidget(QLabel("前情提要:"))
        layout.addWidget(self.summary_edit)
        
        save_btn = QPushButton("保存设置并覆盖世界法则")
        save_btn.setStyleSheet("background-color: #2b5c8f; color: white; padding: 12px; font-size: 15px; border-radius: 6px;")
        save_btn.clicked.connect(self.save_data)
        layout.addWidget(save_btn)

    def save_data(self):
        self.data["background"] = self.bg_edit.toPlainText().strip()
        self.data["core_rules"] = self.rules_edit.toPlainText().strip()
        self.data["factions_info"] = self.factions_edit.toPlainText().strip()
        
        stats_dict = {}
        for line in self.stats_edit.toPlainText().split('\n'):
            line = line.strip()
            if not line: continue
            if ":" in line:
                k, v = line.split(":", 1)
                stats_dict[k.strip()] = v.strip()
            elif "：" in line:
                k, v = line.split("：", 1)
                stats_dict[k.strip()] = v.strip()
                
        self.data["global_stats"] = stats_dict 
        self.data["chapter_summaries"] = [s.strip() for s in self.summary_edit.toPlainText().split('\n') if s.strip()]
        
        mem.save_world_state(self.data)
        self.accept()