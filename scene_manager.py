import json
import os
import re
import logging
import config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SceneManager] - %(message)s')

class Scale:
    UNIT_METER = 1.0     # 比例尺：1字符 = 1米
    TOUCH_RANGE = 1.5    # 触碰/互动阈值
    SOCIAL_RANGE = 5.0   # 正常对话阈值

def get_scene_dir():
    path = os.path.join(config.WORLD_DIR, "scenes")
    os.makedirs(path, exist_ok=True)
    return path

def get_scene_filepath(location_name):
    # 过滤非法字符，确保文件名安全
    safe_name = "".join(c for c in location_name if c not in r'\/:*?"<>|')
    return os.path.join(get_scene_dir(), f"{safe_name}.json")

def _clean_entity_name(text):
    """移除 [角色] 或 (物件) 等修饰符，只保留纯粹名称用于索引计算"""
    return re.sub(r'[\[\]\(\)（）]', '', text).strip()

def calculate_distance(entity_a, entity_b, layout_text):
    """在清洗后的布局文本中计算物理跨度，若无法定位则返回大数"""
    if not layout_text:
        return 99.0
    
    clean_layout = _clean_entity_name(layout_text)
    name_a = _clean_entity_name(entity_a)
    name_b = _clean_entity_name(entity_b)

    if name_a not in clean_layout or name_b not in clean_layout:
        return 99.0

    idx_a = clean_layout.find(name_a)
    idx_b = clean_layout.find(name_b)
    return abs(idx_a - idx_b) * Scale.UNIT_METER

def generate_distance_matrix(scene_data):
    """自动生成当前场景的距离矩阵，供 AI 决策参考"""
    layout = scene_data.get("layout_text", "")
    positions = scene_data.get("positions", {})
    objects = scene_data.get("objects", {})
    
    entities = list(positions.keys()) + list(objects.keys())
    if len(entities) > 30:
        return {"note": "实体过多，请查阅 layout_text 直觉判断距离"}

    matrix = {}
    for e1 in entities:
        matrix[e1] = {}
        for e2 in entities:
            if e1 == e2:
                matrix[e1][e2] = 0.0
            else:
                dist = calculate_distance(e1, e2, layout)
                matrix[e1][e2] = round(dist, 1)
    return matrix

def load_scene(location_name):
    """加载独立场景 JSON，并注入动态物理辅助信息"""
    path = get_scene_filepath(location_name)
    default_scene = {
        "layout_text": f"[{location_name} 的场地]",
        "objects": {},
        "positions": {}
    }
    
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
        except Exception as e:
            logging.error(f"解析场景文件失败 {location_name}: {e}")
            scene_data = default_scene
    else:
        scene_data = default_scene

    # 字段补全
    for k, v in default_scene.items():
        if k not in scene_data:
            scene_data[k] = v

    # 注入内存参考数据（不存盘）
    scene_data["distance_matrix"] = generate_distance_matrix(scene_data)
    scene_data["scale_hint"] = "1字符=1米。触碰需<1.5m。若超距互动，请在 physics_check 说明理由。"
    return scene_data

def save_scene(location_name, scene_data):
    """剥离辅助信息后保存"""
    data_to_save = scene_data.copy()
    data_to_save.pop("distance_matrix", None)
    data_to_save.pop("scale_hint", None)

    path = get_scene_filepath(location_name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

def move_actor(char_name, from_scene, to_scene):
    """跨文件自动化搬运：实现角色及其归属物件的物理迁移"""
    if from_scene == to_scene or from_scene == "未知":
        return
        
    logging.info(f"🚚 物理迁移：【{char_name}】从 [{from_scene}] -> [{to_scene}]")
    
    data_from = load_scene(from_scene)
    data_to = load_scene(to_scene)
    moved_flag = False

    # 1. 搬运角色，重置坐标为待定，防止旧位置穿帮
    if char_name in data_from.get("positions", {}):
        data_from["positions"].pop(char_name)
        data_to.setdefault("positions", {})[char_name] = "[刚进入/位置待定]"
        moved_flag = True

    # 2. 搬运所有权属于该角色的物件
    objs_f = data_from.get("objects", {})
    objs_t = data_to.setdefault("objects", {})
    for obj_n in list(objs_f.keys()):
        if objs_f[obj_n].get("owner") == char_name:
            objs_t[obj_n] = objs_f.pop(obj_n)
            moved_flag = True
            logging.info(f"  - 随身物件同步搬运: {obj_n}")

    if moved_flag:
        save_scene(from_scene, data_from)
        save_scene(to_scene, data_to)

def load_all_scenes():
    """遍历文件夹加载所有场景（分文件读取，供 UI 使用）"""
    scenes = {}
    scene_dir = get_scene_dir()
    if not os.path.exists(scene_dir):
        return scenes
    for filename in os.listdir(scene_dir):
        if filename.endswith(".json"):
            loc_name = filename[:-5]
            # 这里调用 load_scene 会自动附加上辅助信息，方便 UI 观测
            scenes[loc_name] = load_scene(loc_name)
    return scenes