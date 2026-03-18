import os
import re
import logging
import config
import memory_manager as mem
import scene_manager as sm
from engine_director import direct_next_scene
from engine_actor import act_reaction

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [Orchestrator] - %(message)s')

def extract_personal_scene(global_structure, character_name):
    """提取对演员可见的场景切片"""
    perspective = {
        "my_location": "未知",
        "nearby_objects": [],
        "other_actors": [],
        "environment": {},
        "scale_hint": global_structure.get("scale_hint", "")
    }
    if not global_structure:
        return perspective

    pos_dict = global_structure.get("positions", {})
    raw_location = pos_dict.get(character_name, "场景中心")
    perspective["my_location"] = "刚刚进入此地，位置尚未确定" if raw_location == "[刚进入/位置待定]" else raw_location

    for actor, loc in pos_dict.items():
        if actor != character_name:
            loc_desc = "刚刚进入" if loc == "[刚进入/位置待定]" else loc
            perspective["other_actors"].append(f"{actor} ({loc_desc})")

    obj_dict = global_structure.get("objects", {})
    nearby = []
    for k, v in obj_dict.items():
        owner = v.get("owner")
        acc = v.get("accessible_by", [])
        if owner == character_name or character_name in acc or (not owner and not acc):
            nearby.append(k)
    perspective["nearby_objects"] = nearby
    perspective["environment"] = global_structure.get("environment", {})
    return perspective

def filter_context_for_actor(scene_histories_list, character_name):
    """隔离其他角色的内心戏"""
    filtered = []
    for line in scene_histories_list:
        if f"【{character_name}_OS】" in line or f"【{character_name}】" in line:
            filtered.append(line)
        elif "_OS】" in line:
            continue
        else:
            filtered.append(line)
    return "".join(filtered[-8:])

def run_chapter(chapter_num, chapter_title, user_directive, length_mode="中", genre_prompt="", on_data_change=None, max_turns=None):
    """主推演函数 - 被 worker.py 导入"""
    
    # 设置当前章节号（用于临时角色缓存）
    mem.temp_cache.set_chapter(chapter_num)
    
    world_data = mem.load_world_state()
    global_stats = world_data.get('global_stats', {})
    global_history = "\n".join(world_data.get('chapter_summaries', []))
    world_context = f"【背景】: {world_data.get('background','')}\n"

    current_turn = 0
    max_turns = max_turns or config.MAX_TURNS 
    active_characters = set()
    chapter_script = ""
    current_location = "未指定区域"
    scene_histories = {}

    while current_turn < max_turns:
        current_turn += 1
        
        # 汇总全员位置供导演决策
        chars_summary = ""
        if os.path.exists(config.CHAR_DIR):
            for f in os.listdir(config.CHAR_DIR):
                if f.endswith(".json"):
                    c_tmp = mem.load_character(f.replace(".json", ""))
                    chars_summary += f"- {c_tmp.get('name')}: {c_tmp.get('last_known_location')}\n"

        dir_ctx = f"{world_context}\n【全员分布】:\n{chars_summary}\n【指令】: {user_directive}\n"
        cur_structure = sm.load_scene(current_location)

        # 1. 导演推演：生成新的世界逻辑和坐标
        new_loc, scn_desc, new_structure, narration, next_spk, stats_up = direct_next_scene(
            current_location, dir_ctx, global_stats, cur_structure, chapter_script, genre_prompt, length_mode, chapter_num
        )

        # ========================================================
        # 深度修复：保存与场务的先后顺序
        # 必须先保存导演定下的新物理空间基座，然后才能执行附带物品搬运的角色迁移
        # ========================================================
        
        # 2. 率先落地场景底座（此时里面只有导演写死的空架子坐标）
        sm.save_scene(new_loc, new_structure)
        
        # 3. 自动化场务：搬运角色，并将他们的物品一起塞进刚刚生成的场景 JSON 里
        if new_structure.get("positions"):
            for name in list(new_structure["positions"].keys()):
                if mem.character_exists(name):
                    try:
                        char_rec = mem.load_character(name)
                        old_loc = char_rec.get("last_known_location", "未知")
                        if old_loc != new_loc and old_loc != "未知":
                            sm.move_actor(name, old_loc, new_loc) # 内部自动更新两边文件的 JSON
                            char_rec["last_known_location"] = new_loc
                            mem.save_character(name, char_rec)
                    except Exception as e:
                        logging.error(f"搬运角色 {name} 时出错: {e}")
                else:
                    mem.update_temp_location(name, new_loc)
                    logging.info(f"📝 临时角色位置缓存: {name} @ {new_loc}")

        # 4. 重新读取“被场务填充满物品”的真实场景发送给 UI
        final_structure = sm.load_scene(new_loc)
        if on_data_change:
            on_data_change({"stats": stats_up, "structure": final_structure})

        # ========================================================

        # 5. 更新数值
        if stats_up:
            world_data = mem.load_world_state()
            stats = world_data.setdefault("global_stats", {})
            stats.update({k: v for k, v in stats_up.items() if k in stats})
            mem.save_world_state(world_data)
            global_stats = world_data["global_stats"]

        # 6. 场景切换提示
        if new_loc != current_location:
            print(f"\n【🎬 场景切换：{new_loc}】")
        current_location = new_loc

        if current_location not in scene_histories:
            scene_histories[current_location] = []
        if narration:
            msg = f"【旁白】: {narration}\n"
            chapter_script += msg
            scene_histories[current_location].append(msg)
            print(msg, end="")

        if not next_spk or next_spk.upper() == "END":
            break

        # 7. 演员反应
        next_spk = re.sub(r'[（\(].*?[）\)]', '', next_spk).strip()
        
        is_formal = mem.character_exists(next_spk)
        
        if is_formal:
            char_data = mem.load_character(next_spk)
        else:
            char_data = mem.get_temp_character(next_spk)
            mem.update_temp_location(next_spk, current_location)

        active_characters.add(next_spk)
        
        # 获取最新鲜的场景
        fresh_scene = sm.load_scene(current_location)
        perspective = extract_personal_scene(fresh_scene, next_spk)
        isolated_ctx = filter_context_for_actor(scene_histories[current_location], next_spk)

        phys_chk, os_thought, action, dialogue = act_reaction(
            next_spk, current_location, scn_desc, char_data, genre_prompt, isolated_ctx, chapter_num, personal_scene=perspective
        )

        # 记录与展示
        if phys_chk:
            p_msg = f"【物理自检】: {phys_chk}\n"
            chapter_script += p_msg
            scene_histories[current_location].append(p_msg)
            print(f"  [物理校准]: {phys_chk}")

        if os_thought and os_thought != "无":
            print(f"【{next_spk}_OS】: {os_thought}")
            if is_formal:
                char_data.setdefault("memories", []).append(f"我在{current_location}时想过：{os_thought}")
            else:
                mem.add_temp_memory(next_spk, f"我在{current_location}时想过：{os_thought}")

        if dialogue or action:
            for other in perspective.get("other_actors", []):
                other_name = other.split(" (")[0] if " (" in other else other
                if not is_formal:
                    mem.add_temp_interaction(next_spk, other_name)

        if action and not is_formal:
            mem.add_temp_action(next_spk, action)

        act_part = f"（{action}）" if action else ""
        if dialogue:
            fmt = f"【{next_spk}】: {act_part}{dialogue}\n"
        elif action:
            fmt = f"【旁白】: {next_spk}{action}\n"
        else:
            fmt = ""

        if fmt:
            chapter_script += fmt
            scene_histories[current_location].append(fmt)
            print(fmt, end="")

        if is_formal:
            char_data["last_known_location"] = current_location
            mem.save_character(next_spk, char_data)

    return chapter_script, list(active_characters)