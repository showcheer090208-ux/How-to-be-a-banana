# worker.py
import sys
import threading
from PySide6.QtCore import QThread, Signal
from orchestrator import run_chapter
from settlement import settlement_phase

# 深度修复：不再劫持 builtins.print，使用标准的输出流重定向类
class UIOutputLogger(object):
    def __init__(self, emit_func):
        self.emit_func = emit_func
        
    def write(self, text):
        # PyQt UI 更新不能频繁传空字符
        if text: 
            self.emit_func(text)
            
    def flush(self):
        pass

class EngineWorker(QThread):
    text_updated = Signal(str)
    chapter_finished = Signal(str, list)
    data_changed = Signal(dict) # 🚀 用于实时同步 UI 状态
    
    def __init__(self, n, t, d, l, genre_prompt): 
        super().__init__()
        self.n, self.t, self.d, self.l = n, t, d, l
        self.genre_prompt = genre_prompt 
        
    def run(self):
        # 拦截标准输出，线程安全地将底层引擎的 print 转发到 UI
        old_stdout = sys.stdout
        sys.stdout = UIOutputLogger(self.text_updated.emit)
        
        def handle_data_change(payload):
            self.data_changed.emit(payload)

        try:
            s, c = run_chapter(self.n, self.t, self.d, length_mode=self.l, genre_prompt=self.genre_prompt, on_data_change=handle_data_change)
            settlement_phase(self.n, s, c)
            
            from llm_client import call_llm
            branch_prompt = "提供3个下一章发展简述(20字内)。格式：A.xxx\nB.xxx\nC.xxx"
            branches = call_llm("编剧", branch_prompt, "给出选项。", history=s[-2000:])
            self.chapter_finished.emit(s, branches) 
            
        except Exception as e:
            self.text_updated.emit(f"\n⚠️ [引擎错误]: {str(e)}\n")
            import traceback
            traceback.print_exc() # 这会打印到 UI 里方便你查错
        finally: 
            # 必须恢复 stdout，防止内存泄露和主线程崩溃
            sys.stdout = old_stdout