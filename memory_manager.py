import json
import os
import shutil
import re
from datetime import datetime, timezone
import config

# ==========================================
# 📁 正式角色文件管理（持久化）
# ==========================================

def load_json(filepath, default_data):
    if not os.path.exists(filepath):
        save_json(filepath, default_data)
        return default_data
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return default_data

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_character(name, auto_create=False):
    """加载正式角色数据。若 auto_create=False 且文件不存在，则仅返回默认数据不写盘"""
    filepath = os.path.join(config.CHAR_DIR, f"{name}.json")
    default_data = {
        "name": name,
        "role_weight": "龙套炮灰",
        "profile": "临时生成的角色",
        "last_known_location": "未知",
        "current_status": "正常",
        "memories": [],
        "knowledge_base": [],
        "relationships": {}
    }
    
    if not os.path.exists(filepath):
        if auto_create:
            save_json(filepath, default_data)
            return default_data
        else:
            return default_data.copy()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            char = json.load(f)
        except Exception:
            return default_data.copy()
    
    for k, v in default_data.items():
        if k not in char:
            char[k] = v
    return char

def save_character(name, data):
    filepath = os.path.join(config.CHAR_DIR, f"{name}.json")
    save_json(filepath, data)

def archive_character(name):
    filepath = os.path.join(config.CHAR_DIR, f"{name}.json")
    archive_path = os.path.join(config.ARCHIVE_DIR, f"{name}.json")
    if os.path.exists(filepath):
        shutil.move(filepath, archive_path)

def character_exists(name):
    """检查角色是否有正式文件"""
    return os.path.exists(os.path.join(config.CHAR_DIR, f"{name}.json"))

# ==========================================
# 🎭 临时角色缓存池（纯内存，不写文件）
# ==========================================

class TempCharacterCache:
    """临时角色缓存管理器"""
    def __init__(self):
        self._cache = {}
        self.current_chapter = None
    
    def set_chapter(self, chapter_num):
        self.current_chapter = chapter_num
    
    def get(self, name):
        if name not in self._cache:
            self._cache[name] = {
                "name": name,
                "first_seen": self.current_chapter,
                "last_seen": self.current_chapter,
                "appearances": 1,
                "locations": [],
                "memories": [],          
                "interactions": set(),    
                "last_location": None,
                "notable_actions": []      
            }
        else:
            entry = self._cache[name]
            entry["last_seen"] = self.current_chapter
            entry["appearances"] += 1
        return self._cache[name]
    
    def update_location(self, name, location):
        if name in self._cache:
            entry = self._cache[name]
            entry["last_location"] = location
            if location not in entry["locations"]:
                entry["locations"].append(location)
    
    def add_memory(self, name, memory):
        if name in self._cache:
            mem_list = self._cache[name]["memories"]
            mem_list.append(memory)
            if len(mem_list) > 5:
                mem_list.pop(0)
    
    def add_interaction(self, name, other_char):
        if name in self._cache:
            self._cache[name]["interactions"].add(other_char)
    
    def add_notable_action(self, name, action_desc):
        if name in self._cache:
            self._cache[name]["notable_actions"].append(action_desc)
    
    def get_all(self):
        return list(self._cache.keys())
    
    def get_report(self):
        report = []
        for name, data in self._cache.items():
            report.append(
                f"- {name}: 出场{data['appearances']}次，"
                f"首次第{data['first_seen']}章，最近第{data['last_seen']}章，"
                f"互动角色: {len(data['interactions'])}人"
            )
        return "\n".join(report)
    
    def promote(self, name):
        """将临时角色转正为正式角色文件"""
        if name not in self._cache:
            return False
        
        data = self._cache[name]
        char_data = {
            "name": name,
            "role_weight": "龙套炮灰",
            "profile": f"首次登场于第{data['first_seen']}章，共出现{data['appearances']}次。",
            "last_known_location": data["last_location"],
            "current_status": "正常",
            "memories": data["memories"][-3:],
            "knowledge_base": [],
            "relationships": {}
        }
        
        if data["notable_actions"]:
            char_data["profile"] += " 重要行为: " + "；".join(data["notable_actions"][-3:])
        
        save_character(name, char_data)
        del self._cache[name]
        return True

temp_cache = TempCharacterCache()

def get_temp_character(name): return temp_cache.get(name)
def update_temp_location(name, location): temp_cache.update_location(name, location)
def add_temp_memory(name, memory): temp_cache.add_memory(name, memory)
def add_temp_interaction(name, other): temp_cache.add_interaction(name, other)
def add_temp_action(name, action): temp_cache.add_notable_action(name, action)
def get_temp_report(): return temp_cache.get_report()
def promote_temp(name): return temp_cache.promote(name)
def get_all_temp(): return temp_cache.get_all()

# ==========================================
# 🌍 世界状态管理
# ==========================================

def load_world_state():
    filepath = os.path.join(config.WORLD_DIR, "world_state.json")
    default_data = {
        "background": "默认世界",
        "core_rules": "",
        "factions_info": "",
        "global_stats": {"倒计时(天)": "未知", "全服存活人数": "未知"},
        "chapter_summaries": []
    }
    wd = load_json(filepath, default_data)
    if "global_stats" not in wd or not isinstance(wd["global_stats"], dict):
        wd["global_stats"] = default_data["global_stats"]
        save_world_state(wd)
    return wd

def save_world_state(data):
    filepath = os.path.join(config.WORLD_DIR, "world_state.json")
    save_json(filepath, data)

def record_event(chapter_num, event_text):
    filepath = os.path.join(config.WORLD_DIR, "events.json")
    events = load_json(filepath, [])
    tz = timezone(config.TIMEZONE)
    local_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    events.append({"chapter": chapter_num, "time": local_time, "event": event_text})
    save_json(filepath, events)

def save_script_chapter(chapter_num, title, html_content):
    safe_title = re.sub(r'[\\/*?:"<>|]', '', title)[:50]
    filename = f"Chapter_{chapter_num}_{safe_title}.html"
    filepath = os.path.join(config.SCRIPT_DIR, filename)

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>第 {chapter_num} 章：{title}</title>
        <style>
            body {{ background-color: #1a1a2e; color: #e0e0e0; font-family: 'Microsoft YaHei', sans-serif; padding: 40px; }}
        </style>
    </head>
    <body>
        <h1 style='color:#e94560; text-align:center;'>=== 第 {chapter_num} 章：{title} ===</h1>
        {html_content}
    </body>
    </html>
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_html)

def rename_character(old_name, new_name):
    old_path = os.path.join(config.CHAR_DIR, f"{old_name}.json")
    new_path = os.path.join(config.CHAR_DIR, f"{new_name}.json")
    if os.path.exists(old_path) and not os.path.exists(new_path):
        data = load_character(old_name)
        data["name"] = new_name
        save_character(new_name, data)
        os.remove(old_path)
        return True
    return False