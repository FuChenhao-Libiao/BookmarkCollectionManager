# 配置文件

import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据存储目录
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# 数据库配置
DATABASE_PATH = os.path.join(DATA_DIR, "music.db")

# 服务配置
HOST = "0.0.0.0"
PORT = 8000

# 模型配置
MODEL_NAME = "facebook/musicgen-small"  # 可选: musicgen-small / musicgen-medium / musicgen-large
MODEL_CACHE_DIR = os.path.join(DATA_DIR, "models")  # 模型缓存目录，默认存放在 data/models/ 下
SAMPLE_RATE = 32000  # MusicGen 输出采样率

# 生成参数默认值
DEFAULT_DURATION = 10       # 默认生成时长（秒）
MAX_DURATION = 20           # 最大生成时长（秒）（musicgen-small 超过 20s 质量明显下降）
GUIDANCE_SCALE = 1.5        # 提示词引导强度（越高越贴合描述但越慢；1.0=不引导最快，3.0=高质量但慢）
DEFAULT_TEMPERATURE = 1.0   # 默认温度
DEFAULT_TOP_K = 250         # 默认 Top-K
DEFAULT_TOP_P = 0.95        # 默认 Top-P

# 预设音乐风格
MUSIC_STYLES = [
    {"id": "happy", "name": "欢快", "prompt_en": "happy upbeat cheerful music", "icon": "😊"},
    {"id": "sad", "name": "悲伤", "prompt_en": "sad melancholic emotional music", "icon": "😢"},
    {"id": "epic", "name": "史诗", "prompt_en": "epic orchestral cinematic music", "icon": "⚔️"},
    {"id": "electronic", "name": "电子", "prompt_en": "electronic dance EDM music with synthesizers", "icon": "🎛️"},
    {"id": "classical", "name": "古典", "prompt_en": "classical piano orchestral music", "icon": "🎻"},
    {"id": "rock", "name": "摇滚", "prompt_en": "rock music with electric guitar and drums", "icon": "🎸"},
    {"id": "jazz", "name": "爵士", "prompt_en": "smooth jazz music with saxophone", "icon": "🎷"},
    {"id": "relaxing", "name": "轻松", "prompt_en": "relaxing calm ambient music", "icon": "🌿"},
    {"id": "tense", "name": "紧张", "prompt_en": "tense suspenseful dramatic music", "icon": "😰"},
    {"id": "romantic", "name": "浪漫", "prompt_en": "romantic love ballad soft music", "icon": "💕"},
]

# HuggingFace 镜像（国内加速下载模型）
HF_MIRROR = "https://hf-mirror.com"

# 禁用符号链接警告（Windows 非开发者模式下无法使用符号链接，不影响功能）
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
