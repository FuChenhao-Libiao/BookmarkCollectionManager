# 音乐生成服务模块 - 封装 MusicGen 模型

import os
import uuid
import time
import threading
import numpy as np
import scipy.io.wavfile as wavfile
import torch
from config import (
    MODEL_NAME, MODEL_CACHE_DIR, SAMPLE_RATE, OUTPUTS_DIR, HF_MIRROR,
    DEFAULT_TEMPERATURE, DEFAULT_TOP_K, DEFAULT_TOP_P,
    GUIDANCE_SCALE, MUSIC_STYLES
)


class MusicService:
    """音乐生成服务，管理模型加载和推理"""

    def __init__(self):
        self.model = None
        self.processor = None
        self.device = "cpu"
        self.status = "loading"  # loading / ready / error
        self.is_generating = False  # 是否正在生成（同一时刻只允许一个任务）
        self._lock = threading.Lock()

    def load_model(self):
        """加载 MusicGen 模型（在后台线程中调用）"""
        try:
            print(f"🎵 正在加载模型 {MODEL_NAME}...")

            # 设置 HuggingFace 镜像（国内加速）
            os.environ.setdefault("HF_ENDPOINT", HF_MIRROR)

            # 检查模型是否已缓存
            model_cached = MODEL_CACHE_DIR and os.path.exists(
                os.path.join(MODEL_CACHE_DIR, f"models--{MODEL_NAME.replace('/', '--')}")
            )
            if model_cached:
                print(f"   📦 从本地缓存加载模型...")
            else:
                print(f"   ⬇️ 首次运行，正在下载模型（约 2GB），请耐心等待...")

            from transformers import AutoProcessor, MusicgenForConditionalGeneration

            self.processor = AutoProcessor.from_pretrained(MODEL_NAME, cache_dir=MODEL_CACHE_DIR)
            self.model = MusicgenForConditionalGeneration.from_pretrained(
                MODEL_NAME, cache_dir=MODEL_CACHE_DIR,
                attn_implementation="eager"  # 避免 scaled_dot_product_attention fallback，减少开销
            )

            # 检测 GPU并优化
            if torch.cuda.is_available():
                self.device = "cuda"
                self.model = self.model.half().to("cuda")  # float16 加速，显存减半
                print(f"   🚀 使用 GPU 加速 (float16): {torch.cuda.get_device_name(0)}")
            else:
                # CPU 模式尝试用 BetterTransformer 加速
                try:
                    self.model = self.model.to_bettertransformer()
                    print(f"   💻 CPU 模式 (BetterTransformer 加速已启用)")
                except Exception:
                    print(f"   💻 CPU 模式（标准）")

            self.status = "ready"
            print(f"✅ 模型加载完成！")

        except Exception as e:
            self.status = "error"
            print(f"❌ 模型加载失败: {e}")
            raise

    def get_status(self) -> dict:
        """获取服务状态"""
        return {
            "status": self.status,
            "model_name": MODEL_NAME,
            "device": self.device,
            "gpu_available": torch.cuda.is_available(),
            "is_generating": self.is_generating
        }

    def _build_prompt(self, prompt: str, style: str = None) -> str:
        """
        构建最终的英文 prompt
        - 如果用户选了预设风格，拼接风格描述
        - 用户输入的中文描述直接传给模型（MusicGen 对中文支持有限，但可做基本理解）
        """
        parts = []

        # 添加预设风格的英文描述
        if style:
            style_info = next((s for s in MUSIC_STYLES if s["id"] == style), None)
            if style_info:
                parts.append(style_info["prompt_en"])

        # 添加用户描述
        if prompt:
            parts.append(prompt)

        return ", ".join(parts) if parts else "pleasant background music"

    def generate(self, prompt: str, style: str = None, duration: int = 10,
                 temperature: float = DEFAULT_TEMPERATURE,
                 top_k: int = DEFAULT_TOP_K,
                 top_p: float = DEFAULT_TOP_P) -> dict:
        """
        生成音乐

        参数:
            prompt: 用户输入的文本描述
            style: 预设风格 ID
            duration: 时长（秒）
            temperature: 生成温度
            top_k: Top-K 采样
            top_p: Top-P 采样

        返回:
            {"file_path": "xxx.wav", "file_size": 12345, "duration": 10}
        """
        if self.status != "ready":
            raise RuntimeError("模型未就绪，请等待加载完成")

        # 防止并发生成
        with self._lock:
            if self.is_generating:
                raise RuntimeError("当前有任务正在生成，请稍后再试")
            self.is_generating = True

        try:
            start_time = time.time()

            # 构建 prompt
            final_prompt = self._build_prompt(prompt, style)
            print(f"🎵 开始生成音乐...")
            print(f"   Prompt: {final_prompt}")
            print(f"   时长: {duration}s | Temperature: {temperature} | Top-K: {top_k} | Top-P: {top_p}")

            # 计算生成的 token 数量
            # MusicGen 采样率 32000Hz，codebook 每帧 640 个音频采样点 → 约 50 tokens/秒
            max_new_tokens = int(duration * 51.2)  # 精确值: 32000 / 640 = 50, 略多留余量

            # 预处理输入
            inputs = self.processor(
                text=[final_prompt],
                padding=True,
                return_tensors="pt",
            )

            # 移动到对应设备
            if self.device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            # 模型推理
            with torch.no_grad():
                audio_values = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    guidance_scale=GUIDANCE_SCALE,  # 提示词引导，显著提升质量
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                )

            # 转换为 numpy 数组
            audio_data = audio_values[0, 0].cpu().numpy()

            # 归一化到 int16 范围
            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_int16 = (audio_data * 32767).astype(np.int16)

            # 保存为 WAV 文件
            file_name = f"{uuid.uuid4().hex}.wav"
            file_path = os.path.join(OUTPUTS_DIR, file_name)
            wavfile.write(file_path, SAMPLE_RATE, audio_int16)

            file_size = os.path.getsize(file_path)
            elapsed = time.time() - start_time

            print(f"✅ 生成完成！耗时 {elapsed:.1f}s | 文件大小 {file_size / 1024:.1f}KB")

            return {
                "file_path": file_path,
                "file_size": file_size,
                "duration": duration
            }

        finally:
            self.is_generating = False


# 全局单例
music_service = MusicService()
