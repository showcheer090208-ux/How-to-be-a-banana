from openai import OpenAI, BadRequestError
import config

client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)

def call_llm(role, system_prompt, user_input, history=None):
    target_model = config.MODEL_LOGIC if role in ["编剧", "结算", "记忆压缩"] else config.MODEL_PERFORM
    temp = 0.7 if role in ["编剧", "结算"] else 0.9

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.append({"role": "user", "content": f"【当前上下文】:\n{history}"})
    messages.append({"role": "user", "content": user_input})

    try:
        # 尝试使用 JSON 模式
        response = client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=temp,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content.strip()
    except BadRequestError as e:
        # 模型不支持 JSON 模式，降级为普通调用但加强提示
        print(f"[LLM 警告] 模型 {target_model} 不支持 JSON 模式，降级为普通文本。错误: {e}")
        messages.append({"role": "system", "content": "请确保输出是严格的 JSON 对象，不要包含任何其他解释或 Markdown 代码块。"})
        response = client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=temp,
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM 错误] {role} (模型:{target_model}) 调用失败: {e}")
        return ""