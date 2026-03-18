import re
import json
from llm_client import call_llm

def direct_next_scene(current_location, director_context, global_stats, current_scene_structure, chapter_script, genre_prompt, length_mode, chapter_num):
    if length_mode == "短":
        len_instruction = "精简旁白 (30-50字)，侧重于快速动作。"
    elif length_mode == "长":
        len_instruction = "电影级细腻描写 (150-300字)，刻画光影、气味、死角。"
    else:
        len_instruction = "适中长度的描写 (50-100字)。"

    stats_str = json.dumps(global_stats, ensure_ascii=False)
    locked_keys = list(global_stats.keys())
    scene_str = json.dumps(current_scene_structure, ensure_ascii=False)

    director_prompt = (
        f"你是本剧的全知导演。当前推演：第 {chapter_num} 章。你必须严格调度镜头，遵守数值法则，并【实时维护物理空间】。\n"
        f"【剧本文风要求】：{genre_prompt}\n"
        f"【世界核心数值面板】：{stats_str}\n"
        f"【神明铁律】：只能修改合法键 {locked_keys} 的值，严禁新增数值键。\n"
        f"【公共黑板（当前舞台布局）】：\n{scene_str}\n"
        "【空间维护铁律】：\n"
        "1. 字段隔离：'positions' 只能记录【角色名: 具体位置】。严禁将物件放入此字段。\n"
        "2. 物件归属：所有静态障碍物、道具、可交互设备必须放入 'objects' 字段。\n"
        "   示例: \"positions\": {\"李诺\": \"金属墙前\", \"苏茜\": \"门边\"}, \"objects\": {\"黑色金属墙\": {\"type\": \"障碍\"}}\n"
        "3. 动作成本：参照 `layout_text` 检查距离。若角色要跨越障碍或与远处人/物互动，必须在 `narration` 中描写其位移过程（如“绕过桌子走向...”）。严禁瞬移或穿透物理障碍。\n"
        "【强制输出 JSON】：\n"
        "{\n"
        '  "current_location": "当前镜头的具体舞台",\n'
        '  "scene_description": "该舞台当前的具体环境描写",\n'
        '  "scene_structure": {\n'
        '    "layout_text": "用简易字符图表示站位与障碍，如: [角色A] | [桌子] | [角色B]",\n'
        '    "objects": {"手机": {"owner": "角色A", "status": "锁定"}, "药瓶": {"accessible_by": ["角色B", "角色C"]}},\n'
        '    "positions": {"角色A": "桌子旁", "角色B": "门口"}\n'
        '  },\n'
        '  "plot_push": "导演OS：剧情发展与物理逻辑考量",\n'
        f'  "narration": "{len_instruction} 严禁代写台词！新角色入场或位移必须在此描写。",\n'
        '  "next_speaker": "下一个说话的角色名 (若剧情演完填 END)",\n'
        '  "global_stats_update": {} \n'
        "}\n"
    )

    trimmed_history = chapter_script[-4000:] if len(chapter_script) > 4000 else chapter_script

    director_reply = call_llm(
        "编剧", director_prompt, f"镜头当前位置：{current_location}。请推演下一步。",
        history=director_context + trimmed_history
    )

    # 深度修复：彻底废除用正则替换单引号的危险做法
    try:
        match = re.search(r'\{[\s\S]*\}', director_reply)
        if match:
            clean_json_str = match.group(0)
            clean_json_str = re.sub(r",\s*([}\]])", r"\1", clean_json_str) # 清理结尾多余逗号
            data = json.loads(clean_json_str)
        else:
            raise ValueError("No JSON block found")
    except Exception as e:
        data = {"narration": "（场景剧烈震荡，视角强行切换）", "next_speaker": "END"}

    new_location = data.get("current_location", current_location)
    scene_description = data.get("scene_description", "环境未明")
    new_scene_structure = data.get("scene_structure", current_scene_structure)
    narration = data.get("narration", "").strip()
    next_speaker = str(data.get("next_speaker", "END")).strip()
    stats_update = data.get("global_stats_update", {})

    return new_location, scene_description, new_scene_structure, narration, next_speaker, stats_update