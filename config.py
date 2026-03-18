import os
from datetime import timedelta

API_KEY = 
BASE_URL = 
MODEL_LOGIC = 
MODEL_PERFORM = 

# 目录路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHAR_DIR = os.path.join(DATA_DIR, "characters")
WORLD_DIR = os.path.join(DATA_DIR, "world")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")

# 运行时参数
MAX_TURNS = 20                                   # 每章最大推演轮数
TIMEZONE = timedelta(hours=8)                    # 事件记录时区（默认东八区）

# 初始化目录结构
for path in [CHAR_DIR, WORLD_DIR, SCRIPT_DIR, ARCHIVE_DIR]:
    os.makedirs(path, exist_ok=True)