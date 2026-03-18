# script_renderer.py
import re

def render_script_html(text, fsize, color_fetcher):
    text = text.strip()
    if not text: return ""
    style_base = f"line-height: 1.8; margin-top: 10px; margin-bottom: 10px; font-size: {fsize}px;"
    
    # 物理自检：战术风格 UI
    phys_match = re.search(r'【物理自检】[:：]\s*(.*)', text)
    if phys_match:
        return (f"<div style='{style_base} padding-left: 10px; border-left: 2px solid #4da8da; margin-bottom: -5px;'>"
                f"<span style='color: #4da8da; font-size: {max(10, fsize - 3)}px; font-family: Consolas, monospace;'>"
                f"🛡️ [物理模拟校验]: {phys_match.group(1).strip()}</span></div>")

    # 内心 OS
    os_match = re.search(r'【?(.*?)_OS】?[:：]\s*(.*)', text, re.IGNORECASE)
    if os_match:
        return (f"<div style='{style_base} padding-left: 20px;'>"
                f"<span style='color: rgba(180, 180, 200, 0.6); font-style: italic;'>"
                f"💭 [{os_match.group(1).strip()}的内心]: {os_match.group(2).strip()}</span></div>")

    # 镜头切换
    if "镜头切换" in text or text.startswith("—"):
        return f"<div style='{style_base} color: #f39c12; font-weight: bold; text-align: center; margin: 20px 0;'>— {text.strip('【】— ')} —</div>"

    # 旁白
    if text.startswith("【旁白】") or text.startswith("旁白:"):
        content = text.replace("【旁白】:", "").replace("【旁白】", "").strip()
        return f"<div style='{style_base} color: #A0B0C0;'><b style='color: #607d8b;'>【旁白】</b>: {content}</div>"

    # 对话
    char_match = re.match(r'【?(.*?)】?[:：]\s*(.*)', text)
    if char_match:
        name, dlg = char_match.group(1).strip(), char_match.group(2).strip()
        color = color_fetcher(name)
        dlg_html = re.sub(r'([（\(].*?[）\)])', r'<span style="color: #888899;">\1</span>', dlg)
        return (f"<div style='{style_base} padding-left: 20px;'><b style='color: {color};'>【{name}】:</b> "
                f"<span style='color: #e8eaed;'>{dlg_html}</span></div>")

    return f"<div style='{style_base} color: #e8eaed;'>{text}</div>"