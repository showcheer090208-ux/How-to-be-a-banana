import re
import json
from llm_client import call_llm

def act_reaction(next_speaker, current_location, scene_description, char_data, genre_prompt, isolated_context, chapter_num, personal_scene=None):
    # 记忆隔离规则
    isolation_warning = (
        "【严格记忆隔离规则 - 必须绝对遵守】\n"
        "你只能使用以下信息进行思考、内心独白、行动和台词：\n"
        "1. 你的综合人设、当前身心状态、过往重大记忆（仅限你自己的）\n"
        "2. 当前场景刚刚发生的事（isolated_context中明确写给你的部分）\n"
        "3. 你自己能直接感知到的感官信息（听到的声音、看到的短信/灯光变化、对方说出口的话）\n\n"
        "严禁使用/引用/暗示/体现以下任何内容：\n"
        "- 旁白中描述的其他角色隐藏动作、表情、内心OS、未让你感知到的行为\n"
        "- 其他角色未说出口的任何想法、未让你直接听到的/看到的细节\n"
        "即使上下文里出现了上述内容，你也必须立即忘记它们，视作不存在。\n"
        "违反隔离规则 = 角色崩坏 = 严重OOC，必须自我修正。\n"
        "现在严格遵守以上规则开始表演。\n"
    )

    # 构建提示词
    rel_data = char_data.get('relationships', {})
    rel_str = "暂无特别羁绊"
    if rel_data:
        rel_lines = [f"- 对 {k}: 【{v.get('关系', '未知')}】 (好感度: {v.get('好感度', 0)})" for k, v in rel_data.items()]
        rel_str = "\n".join(rel_lines)

    # 提取最近记忆（最多5条）
    memories = char_data.get('memories', [])
    mem_str = "\n".join(memories[-5:]) if memories else "无"

    # 提取情报库（最近3条）
    knowledge = char_data.get('knowledge_base', [])
    knowledge_str = "、".join(knowledge[-3:]) if knowledge else "无"

    char_prompt = (
        f"你是【{next_speaker}】。当前是故事的【第 {chapter_num} 章】。\n"
        f"{isolation_warning}\n"
        f"你目前位于独立舞台：[{current_location}]。\n"
        f"【你眼前的环境】：{scene_description}\n"
        f"【你的综合人设】：\n{char_data.get('profile', '自由发挥')}\n"
        f"【你的人际关系网】(请据此判断对待眼前人的态度)：\n{rel_str}\n\n"
        f"【你当前的身心状态】：{char_data.get('current_status', '正常')}\n"
        f"【你掌握的关键情报】：{knowledge_str}\n\n"
        f"【过往重大记忆】：\n{mem_str}\n\n"
        f"【文风风格】：{genre_prompt}\n\n"
    )

    if personal_scene:
        # 将 personal_scene 以紧凑 JSON 格式嵌入
        personal_json = json.dumps(personal_scene, ensure_ascii=False, separators=(',', ':'))
        char_prompt += f"""
【你当前感知到的具体场景】（JSON格式，只包含你能直接接触和观察到的信息）：
{personal_json}

请严格遵守以下物理规则：
1. 你只能与 `nearby_objects` 中列出的物件互动。如果需要拿取不在身边的物件，必须通过对话请求他人传递或移动过去。
2. 你的动作必须符合你的位置 `my_location` 和环境 `environment`。
3. 你可以与 `other_actors` 中列出的角色对话或互动，但不能涉及你不知道的信息。
\n
"""

    char_prompt += (
        "【表演禁令】：严格遵循“Show, Don't Tell”，仅输出角色原生的瞬时念头和纯肢体动作，严禁解释动机、严禁充当旁白解说局势。若无必要，inner_thought/action/dialogue 均可置空 \"\"，以留白彰显张力。\n\n"
        "【强制输出 JSON】:\n"
        "{\n"
        '  "physics_check": "角色瞬间自检：分析我与目标/物品的距离和障碍，确认动作可行性（若无物理考量可留空）",\n'
        '  "inner_thought": "角色的瞬时第一反应（无则留空）",\n'
        '  "action": "纯粹的肢体动作/微表情（无则留空）",\n'
        '  "dialogue": "角色说出口的台词（无则留空）"\n'
        "}\n"
        "【重要】严禁输出任何非JSON格式的内容，必须严格遵循上述JSON结构，所有字段均为字符串。"
    )

    char_reply = call_llm(
        next_speaker,
        char_prompt,
        user_input="镜头给到了你，请对本场景的状况做出反应。",
        history=f"【本场景刚刚发生的事】:\n{isolated_context}"
    )

    # 深度修复：健壮的 JSON 提取，抛弃危险的单引号正则替换
    char_res = {}
    try:
        match = re.search(r'\{[\s\S]*\}', char_reply)
        if match:
            clean_json_str = match.group(0)
            clean_json_str = re.sub(r",\s*([}\]])", r"\1", clean_json_str)  # 去除尾随逗号
            char_res = json.loads(clean_json_str)
        else:
            raise ValueError("No valid JSON found")
    except Exception as e:
        # 记录错误但不中断，兜底正则提取
        pass

    # 兜底提取（若解析失败）
    if not char_res:
        for key in ["physics_check", "inner_thought", "action", "dialogue"]:
            m = re.search(rf'(?i)"?{key}"?\s*[:=]\s*["\']?([^"\']*?)(?=["\']?\s*(?:,|\}}|$))', char_reply, re.DOTALL)
            if m:
                char_res[key] = m.group(1).strip()

    # 设置默认空值
    char_res.setdefault("physics_check", "")
    char_res.setdefault("inner_thought", "")
    char_res.setdefault("action", "")
    char_res.setdefault("dialogue", "")

    # 清洗 action 字段
    action = str(char_res["action"]).strip()
    action = re.sub(r'[（\(][无none None]*[）\)]', '', action, flags=re.IGNORECASE).strip()
    invalid_action_values = {"none", "null", "无", "", "(动作)none", "(动作)无", "None", "Null", "（动作）None", "none", "null"}
    if action.lower() in invalid_action_values or not action:
        char_res["action"] = ""
    else:
        char_res["action"] = action

    # 清洗 dialogue
    dialogue = str(char_res["dialogue"]).strip()
    if dialogue.lower() in {"null", "none", "无"}:
        dialogue = ""
    char_res["dialogue"] = dialogue

    # 返回四个值
    return (
        char_res["physics_check"],
        char_res["inner_thought"],
        char_res["action"],
        char_res["dialogue"]
    )