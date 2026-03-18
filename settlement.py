import json
import re
import os
import config
from llm_client import call_llm
import memory_manager as mem
from memory_manager import temp_cache, promote_temp


def settlement_phase(chapter_num, script, active_characters):
    """章节结束后的世界线状态更新与长期记忆写入"""
    print(f"\n[世界线演进] 正在结算第{chapter_num}章状态与长期记忆...")
    
    # 检查角色目录是否存在
    if not os.path.exists(config.CHAR_DIR):
        print(f"⚠️ 角色目录不存在: {config.CHAR_DIR}")
        return
        
    all_files = [f.replace(".json", "") for f in os.listdir(config.CHAR_DIR) if f.endswith(".json")]
    
    # 如果没有角色文件，提前返回
    if not all_files:
        print("⚠️ 没有找到任何角色文件")
        return

    system_prompt = (
        "阅读剧本并返回合法 JSON:\n"
        "{\n"
        '  "summary": "50字内本章核心剧情梗概",\n'
        '  "event": "引发世界级变动的大事件或 null",\n'
        '  "dead_characters": ["死者A"] (🔥受致命伤或剧情判定死亡必填，使其杀青！若无则填[]),\n'
        '  "new_profiles": {"新龙套角色名": {"profile": "提炼设定", "faction": "推测阵营"}},\n'
        '  "character_updates": {\n'
        '    "角色名": {\n'
        '      "status": "当前的最新身心状态(如: 吃饱喝足、重伤)。覆盖旧状态！",\n'
        '      "new_memory": "本章重大事件(琐事填 null)。",\n'
        '      "new_knowledge": ["得知了某人身份", "发现了抽屉里的信"] (记录其本章新掌握的关键事实/情报，无则填[]),\n'
        '      "faction": "新阵营（如果改变，否则填 null）",\n'
        '      "role_weight": "新定位（主角/重要配角/龙套炮灰，不变填 null）",\n'
        '      "relationships": {\n'
        '        "对方角色名": {\n'
        '          "关系": "新关系描述(若不变填 null)",\n'
        '          "好感度": 10 (整数, -100到100, 若不变填 null)\n'
        '        }\n'
        '      }\n'
        '    }\n'
        '  }\n'
        "}\n"
        f"全角色名单（包含未出场，允许后台推演）：{', '.join(all_files)}"
    )
    
    response = call_llm("结算", system_prompt, user_input="开始推演各角色的最新状态与记忆。", history=script)
    if not response:
        print("⚠️ LLM返回空响应")
        return
        
    try:
        # 深度修复：通过提取 JSON 区块防止啰嗦的模型导致解析失败
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            clean_json_str = match.group(0)
            result = json.loads(clean_json_str)
        else:
            raise ValueError("未找到合法JSON块")
            
        # 更新世界状态
        world_data = mem.load_world_state()
        world_data["chapter_summaries"].append(f"第{chapter_num}章: {result.get('summary','')}")
        mem.save_world_state(world_data)
        
        # 记录重大事件
        event = result.get("event")
        if event and str(event).lower() != "null":
            mem.record_event(chapter_num, event)
        
        # 处理死亡角色
        dead_characters = result.get("dead_characters", [])
        for dead_name in dead_characters:
            if dead_name:  # 确保不是空字符串
                mem.archive_character(dead_name)
        
        # 处理角色更新
        updates = result.get("character_updates", {})
        if not updates:
            print("⚠️ 没有角色更新数据")
            
        for name, data in updates.items():
            # 跳过已死亡角色
            if name in dead_characters:
                continue
                
            char_path = os.path.join(config.CHAR_DIR, f"{name}.json")
            if not os.path.exists(char_path):
                print(f"⚠️ 角色文件不存在: {name}")
                continue
                
            char_data = mem.load_character(name)
            if not char_data:
                print(f"⚠️ 无法加载角色数据: {name}")
                continue
            
            # 更新状态
            new_status = data.get("status")
            if new_status and str(new_status).lower() != "null":
                char_data["current_status"] = new_status
            
            # 更新记忆
            new_mem = data.get("new_memory")
            if new_mem and isinstance(new_mem, str) and str(new_mem).lower() != "null":
                new_mem = new_mem.strip('"\'')
                char_data["memories"].append(f"第{chapter_num}章: {new_mem}")

            # 更新情报库
            new_knowledge = data.get("new_knowledge", [])
            if isinstance(new_knowledge, list) and new_knowledge:
                current_kb = char_data.setdefault("knowledge_base", [])
                current_kb.extend(new_knowledge)
                char_data["knowledge_base"] = current_kb[-15:]  # 仅保留最近15条
            
            # 更新新角色信息
            new_profiles = result.get("new_profiles", {})
            if name in new_profiles and "新登场" in char_data.get("profile", ""):
                char_data["profile"] = new_profiles[name].get("profile", char_data["profile"])
                char_data["faction"] = new_profiles[name].get("faction", char_data["faction"])

            # 更新阵营和定位
            if data.get("faction") and str(data["faction"]).lower() != "null":
                char_data["faction"] = data["faction"]
            if data.get("role_weight") and str(data["role_weight"]).lower() != "null":
                char_data["role_weight"] = data["role_weight"]

            # 更新关系
            new_rels = data.get("relationships", {})
            if isinstance(new_rels, dict):
                current_rels = char_data.get("relationships", {})
                for target_name, rel_updates in new_rels.items():
                    if target_name not in current_rels:
                        current_rels[target_name] = {"关系": "未知", "好感度": 0}
                    
                    if "关系" in rel_updates and str(rel_updates["关系"]).lower() != "null":
                        current_rels[target_name]["关系"] = rel_updates["关系"]
                    
                    if "好感度" in rel_updates and rel_updates["好感度"] is not None:
                        好感度值 = rel_updates["好感度"]
                        if str(好感度值).lower() != "null":
                            try:
                                current_rels[target_name]["好感度"] = int(好感度值)
                            except (ValueError, TypeError):
                                print(f"  警告: {name}对{target_name}的好感度格式错误: {好感度值}")
                
                char_data["relationships"] = current_rels

            # 记忆压缩
            if len(char_data.get("memories", [])) > 8:
                print(f"  [记忆压缩] 正在提炼 {name} 的生平记忆...")
                compress_prompt = (
                    "你是一个记忆提炼模块。请将以下角色的冗长记忆压缩为3-5条最核心的【人生重大转折】。\n"
                    "要求：\n"
                    "1. 抛弃流水账，保留第一人称。\n"
                    "2. 必须输出严格的 JSON 数组格式（不要包含任何 markdown 代码块）。\n"
                    f"原记忆：\n{json.dumps(char_data['memories'], ensure_ascii=False, indent=2)}"
                )
                compressed = call_llm("记忆压缩", compress_prompt, "请直接输出JSON数组。", history="")
                if compressed:
                    try:
                        mem_match = re.search(r'\[.*\]', compressed, re.DOTALL)
                        if mem_match:
                            new_mems = json.loads(mem_match.group(0))
                            if isinstance(new_mems, list) and new_mems:
                                char_data["memories"] = new_mems
                    except Exception as e:
                        print(f"  [记忆压缩解析失败]: {e}")

            # 保存角色数据
            if not mem.save_character(name, char_data):
                print(f"⚠️ 保存角色失败: {name}")
        
        # 结算完成后评估临时角色转正
        suggest_promotions(chapter_num)
                
    except json.JSONDecodeError as e:
        print(f"⚠️ [JSON解析错误]: {e}")
    except Exception as e:
        print(f"⚠️ [结算异常]: {e}")
        import traceback
        traceback.print_exc()


def suggest_promotions(chapter_num):
    """根据临时角色缓存，让LLM建议转正角色"""
    if temp_cache is None:
        print("⚠️ temp_cache不可用")
        return
        
    try:
        temp_report = temp_cache.get_report()
        if not temp_report:
            return
        
        print("\n[临时角色评估] 正在分析是否有人值得转正...")
        
        prompt = (
            f"以下是第{chapter_num}章结束后仍在活跃的临时角色统计：\n{temp_report}\n\n"
            "请根据他们的出场次数、互动情况，选出最多3个值得转为正式角色的名字。"
            "输出格式：[\"角色A\", \"角色B\"] 或 []"
        )
        
        response = call_llm("结算", prompt, "请输出JSON数组。", history="")
        if not response:
            return
            
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            to_promote = json.loads(match.group(0))
            promoted_count = 0
            for name in to_promote:
                if name and promote_temp(name):
                    print(f"  ⭐ {name} 已自动转正为正式角色")
                    promoted_count += 1
            if promoted_count == 0:
                print("  没有符合条件的转正角色")
    except Exception as e:
        print(f"  [转正建议处理异常] {e}")