import asyncio
import edge_tts
import pygame
import threading
import queue
import tempfile
import os
import uuid

class TTSManager:
    def __init__(self):
        self.q = queue.Queue()
        self.is_playing = False
        self.muted = True # 默认静音，UI里可以加开关
        pygame.mixer.init()
        
        # 简单分配音色
        self.voices = {
            "旁白": "zh-CN-YunxiNeural",
            "男": "zh-CN-YunjianNeural",
            "女": "zh-CN-XiaoxiaoNeural"
        }
        
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def add_task(self, char_name, text):
        if self.muted or not text: return
        voice = self.voices.get("旁白")
        # 这里可以根据你的 char_data 里的性别设定来扩展判断
        if char_name and char_name != "旁白":
            voice = self.voices.get("男") # 默认给个男声，或者你可以随机/查表
            
        self.q.put((voice, text))

    def set_mute(self, state):
        self.muted = state
        if state:
            pygame.mixer.music.stop()

    def _worker_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            voice, text = self.q.get()
            if self.muted: 
                self.q.task_done()
                continue
                
            self.is_playing = True
            
            # 使用 UUID 防止多句堆叠时的文件并发锁定冲突
            temp_file = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.mp3")
            try:
                communicate = edge_tts.Communicate(text, voice)
                loop.run_until_complete(communicate.save(temp_file))
                
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and not self.muted:
                    pygame.time.Clock().tick(10)
                pygame.mixer.music.unload()
            except Exception as e:
                print(f"[TTS 错误] {e}")
            finally:
                # 清理临时文件，确保不留垃圾
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except OSError:
                    pass
                    
                self.is_playing = False
                self.q.task_done()