# scene_editor.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QTextEdit, QLineEdit, QPushButton, QLabel,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QGroupBox, QMessageBox)
from PySide6.QtCore import Qt
import scene_manager as sm

class SceneEditorDialog(QDialog):
    def __init__(self, scene_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"编辑场景: {scene_name}")
        self.resize(600, 700)
        self.scene_name = scene_name
        self.scene_data = sm.load_scene(scene_name)  # 获取场景数据

        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 场景名称（只读）
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("场景名称:"))
        self.name_label = QLabel(scene_name)
        self.name_label.setStyleSheet("font-weight: bold; color: #e94560;")
        name_layout.addWidget(self.name_label)
        name_layout.addStretch()
        layout.addLayout(name_layout)

        # 布局文本
        group_layout = QGroupBox("📐 空间布局 (字符画)")
        form = QFormLayout(group_layout)
        self.layout_text = QTextEdit()
        self.layout_text.setPlainText(self.scene_data.get("layout_text", ""))
        self.layout_text.setMaximumHeight(100)
        form.addRow("layout_text:", self.layout_text)
        layout.addWidget(group_layout)

        # 物件表格
        group_objects = QGroupBox("📦 物件列表")
        obj_layout = QVBoxLayout(group_objects)
        self.obj_table = QTableWidget()
        self.obj_table.setColumnCount(3)
        self.obj_table.setHorizontalHeaderLabels(["物件名", "所有者", "可访问者"])
        self.obj_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        obj_layout.addWidget(self.obj_table)

        # 物件按钮
        obj_btn_layout = QHBoxLayout()
        self.btn_add_obj = QPushButton("➕ 添加物件")
        self.btn_add_obj.clicked.connect(self.add_object_row)
        self.btn_remove_obj = QPushButton("➖ 移除选中物件")
        self.btn_remove_obj.clicked.connect(self.remove_selected_object)
        obj_btn_layout.addWidget(self.btn_add_obj)
        obj_btn_layout.addWidget(self.btn_remove_obj)
        obj_layout.addLayout(obj_btn_layout)
        layout.addWidget(group_objects)

        # 角色位置表格
        group_positions = QGroupBox("📍 角色位置")
        pos_layout = QVBoxLayout(group_positions)
        self.pos_table = QTableWidget()
        self.pos_table.setColumnCount(2)
        self.pos_table.setHorizontalHeaderLabels(["角色名", "位置"])
        self.pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        pos_layout.addWidget(self.pos_table)

        # 位置按钮
        pos_btn_layout = QHBoxLayout()
        self.btn_add_pos = QPushButton("➕ 添加角色位置")
        self.btn_add_pos.clicked.connect(self.add_position_row)
        self.btn_remove_pos = QPushButton("➖ 移除选中角色")
        self.btn_remove_pos.clicked.connect(self.remove_selected_position)
        pos_btn_layout.addWidget(self.btn_add_pos)
        pos_btn_layout.addWidget(self.btn_remove_pos)
        pos_layout.addLayout(pos_btn_layout)
        layout.addWidget(group_positions)

        # 保存按钮
        self.btn_save = QPushButton("💾 保存场景修改")
        self.btn_save.setStyleSheet("background-color: #e94560; padding: 8px;")
        self.btn_save.clicked.connect(self.save_scene)
        layout.addWidget(self.btn_save)

        # 初始化表格数据
        self.load_objects()
        self.load_positions()

    def load_objects(self):
        """加载物件数据到表格"""
        objects = self.scene_data.get("objects", {})
        self.obj_table.setRowCount(len(objects))
        for row, (obj_name, obj_info) in enumerate(objects.items()):
            self.obj_table.setItem(row, 0, QTableWidgetItem(obj_name))
            owner = obj_info.get("owner", "")
            self.obj_table.setItem(row, 1, QTableWidgetItem(owner))
            accessible = ", ".join(obj_info.get("accessible_by", []))
            self.obj_table.setItem(row, 2, QTableWidgetItem(accessible))

    def load_positions(self):
        """加载角色位置到表格"""
        positions = self.scene_data.get("positions", {})
        self.pos_table.setRowCount(len(positions))
        for row, (char, loc) in enumerate(positions.items()):
            self.pos_table.setItem(row, 0, QTableWidgetItem(char))
            self.pos_table.setItem(row, 1, QTableWidgetItem(loc))

    def add_object_row(self):
        """添加一行空物件"""
        row = self.obj_table.rowCount()
        self.obj_table.insertRow(row)
        self.obj_table.setItem(row, 0, QTableWidgetItem("新物件"))
        self.obj_table.setItem(row, 1, QTableWidgetItem(""))
        self.obj_table.setItem(row, 2, QTableWidgetItem(""))

    def remove_selected_object(self):
        """移除选中的物件行"""
        current_row = self.obj_table.currentRow()
        if current_row >= 0:
            self.obj_table.removeRow(current_row)

    def add_position_row(self):
        """添加一行角色位置"""
        row = self.pos_table.rowCount()
        self.pos_table.insertRow(row)
        self.pos_table.setItem(row, 0, QTableWidgetItem("新角色"))
        self.pos_table.setItem(row, 1, QTableWidgetItem("未知"))

    def remove_selected_position(self):
        """移除选中的位置行"""
        current_row = self.pos_table.currentRow()
        if current_row >= 0:
            self.pos_table.removeRow(current_row)

    def save_scene(self):
        """保存场景数据"""
        # 收集布局文本
        self.scene_data["layout_text"] = self.layout_text.toPlainText().strip()

        # 收集物件
        objects = {}
        for row in range(self.obj_table.rowCount()):
            obj_name = self.obj_table.item(row, 0).text().strip()
            if not obj_name:
                continue
            owner = self.obj_table.item(row, 1).text().strip()
            accessible_str = self.obj_table.item(row, 2).text().strip()
            accessible = [a.strip() for a in accessible_str.split(",") if a.strip()]
            obj_info = {}
            if owner:
                obj_info["owner"] = owner
            if accessible:
                obj_info["accessible_by"] = accessible
            objects[obj_name] = obj_info
        self.scene_data["objects"] = objects

        # 收集角色位置
        positions = {}
        for row in range(self.pos_table.rowCount()):
            char = self.pos_table.item(row, 0).text().strip()
            if not char:
                continue
            loc = self.pos_table.item(row, 1).text().strip()
            positions[char] = loc
        self.scene_data["positions"] = positions

        # 保存
        sm.save_scene(self.scene_name, self.scene_data)
        QMessageBox.information(self, "保存成功", f"场景 {self.scene_name} 已更新。")
        self.accept()