# FastAPI 主程序 - 路由和接口

import os
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional

from config import HOST, PORT, MUSIC_STYLES, DEFAULT_DURATION, MAX_DURATION, DEFAULT_TEMPERATURE, DEFAULT_TOP_K, DEFAULT_TOP_P
from database import init_database, save_generation, get_generation, get_history, delete_generation
from music_service import music_service


# ========== 请求/响应模型 ==========

class GenerateRequest(BaseModel):
    """音乐生成请求"""
    prompt: str = Field(..., min_length=1, max_length=500, description="音乐描述文本")
    style: Optional[str] = Field(None, description="预设风格 ID")
    duration: Optional[int] = Field(DEFAULT_DURATION, ge=5, le=MAX_DURATION, description="时长（秒）")
    temperature: Optional[float] = Field(DEFAULT_TEMPERATURE, ge=0.1, le=2.0, description="生成温度")
    top_k: Optional[int] = Field(DEFAULT_TOP_K, ge=0, le=1000, description="Top-K 采样")
    top_p: Optional[float] = Field(DEFAULT_TOP_P, ge=0.0, le=1.0, description="Top-P 采样")


class ApiResponse(BaseModel):
    """统一响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[dict | list] = None


# ========== 应用初始化 ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    init_database()
    # 在后台线程加载模型，不阻塞服务启动
    thread = threading.Thread(target=music_service.load_model, daemon=True)
    thread.start()
    print(f"🚀 服务已启动: http://localhost:{PORT}")
    print(f"📖 API 文档: http://localhost:{PORT}/docs")
    yield
    # 关闭时
    print("👋 服务已关闭")


app = FastAPI(
    title="🎵 智能音乐生成器",
    description="基于 MusicGen 的 AI 音乐生成 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== API 路由 ==========

@app.get("/api/status")
async def get_status():
    """获取服务状态"""
    return ApiResponse(
        code=200,
        message="服务正常",
        data=music_service.get_status()
    )


@app.get("/api/styles")
async def get_styles():
    """获取预设风格列表"""
    return ApiResponse(
        code=200,
        message="success",
        data=MUSIC_STYLES
    )


@app.post("/api/generate")
async def generate_music(req: GenerateRequest):
    """生成音乐（核心接口）"""
    # 检查模型状态
    if music_service.status == "loading":
        raise HTTPException(status_code=503, detail="模型加载中，请稍后再试")
    if music_service.status == "error":
        raise HTTPException(status_code=500, detail="模型加载失败，请检查后端日志")
    if music_service.is_generating:
        raise HTTPException(status_code=429, detail="当前有任务正在生成，请稍后再试")

    try:
        # 调用音乐生成服务
        result = music_service.generate(
            prompt=req.prompt,
            style=req.style,
            duration=req.duration,
            temperature=req.temperature,
            top_k=req.top_k,
            top_p=req.top_p,
        )

        # 保存到数据库
        record_id = save_generation(
            prompt=req.prompt,
            style=req.style or "",
            duration=req.duration,
            file_path=result["file_path"],
            file_size=result["file_size"],
            temperature=req.temperature,
            top_k=req.top_k,
            top_p=req.top_p,
        )

        return ApiResponse(
            code=200,
            message="生成成功",
            data={
                "id": record_id,
                "prompt": req.prompt,
                "style": req.style or "",
                "duration": req.duration,
                "file_url": f"/api/music/{record_id}",
                "file_size": result["file_size"],
                "temperature": req.temperature,
                "created_at": get_generation(record_id)["created_at"]
            }
        )

    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@app.get("/api/music/{record_id}")
async def get_music_file(record_id: int):
    """获取音频文件"""
    record = get_generation(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="音频记录不存在")

    file_path = record["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")

    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=f"music_{record_id}.wav"
    )


@app.get("/api/history")
async def get_music_history(page: int = 1, page_size: int = 12, style: Optional[str] = None):
    """获取生成历史"""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 50:
        page_size = 12

    result = get_history(page=page, page_size=page_size, style=style)
    return ApiResponse(
        code=200,
        message="success",
        data=result
    )


@app.delete("/api/history/{record_id}")
async def delete_music_record(record_id: int):
    """删除历史记录"""
    success = delete_generation(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")

    return ApiResponse(
        code=200,
        message="删除成功",
        data=None
    )


# ========== 启动入口 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
