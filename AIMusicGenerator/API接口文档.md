# 🎵 智能音乐生成器 - API 接口文档

## 📌 基础信息

- **Base URL**: `http://localhost:8000`
- **数据格式**: JSON
- **音频格式**: WAV（采样率 32000Hz）

---

## 📡 接口列表

### 1. 获取服务状态

**GET** `/api/status`

检查后端服务和模型加载状态。

**响应示例：**
```json
{
    "code": 200,
    "message": "服务正常",
    "data": {
        "status": "ready",
        "model_name": "facebook/musicgen-small",
        "device": "cpu",
        "gpu_available": false
    }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | "loading" 模型加载中 / "ready" 就绪 / "error" 异常 |
| model_name | string | 当前使用的模型名称 |
| device | string | 运行设备 "cpu" 或 "cuda" |
| gpu_available | boolean | 是否有可用 GPU |

---

### 2. 获取预设风格列表

**GET** `/api/styles`

获取所有可用的音乐风格预设。

**响应示例：**
```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": "happy",
            "name": "欢快",
            "prompt_en": "happy upbeat cheerful music",
            "icon": "😊"
        },
        {
            "id": "sad",
            "name": "悲伤",
            "prompt_en": "sad melancholic emotional music",
            "icon": "😢"
        },
        {
            "id": "epic",
            "name": "史诗",
            "prompt_en": "epic orchestral cinematic music",
            "icon": "⚔️"
        },
        {
            "id": "electronic",
            "name": "电子",
            "prompt_en": "electronic dance EDM music with synthesizers",
            "icon": "🎛️"
        },
        {
            "id": "classical",
            "name": "古典",
            "prompt_en": "classical piano orchestral music",
            "icon": "🎻"
        },
        {
            "id": "rock",
            "name": "摇滚",
            "prompt_en": "rock music with electric guitar and drums",
            "icon": "🎸"
        },
        {
            "id": "jazz",
            "name": "爵士",
            "prompt_en": "smooth jazz music with saxophone",
            "icon": "🎷"
        },
        {
            "id": "relaxing",
            "name": "轻松",
            "prompt_en": "relaxing calm ambient music",
            "icon": "🌿"
        },
        {
            "id": "tense",
            "name": "紧张",
            "prompt_en": "tense suspenseful dramatic music",
            "icon": "😰"
        },
        {
            "id": "romantic",
            "name": "浪漫",
            "prompt_en": "romantic love ballad soft music",
            "icon": "💕"
        }
    ]
}
```

---

### 3. 生成音乐

**POST** `/api/generate`

根据文本描述生成音乐，这是核心接口。

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 音乐描述文本（中文会自动翻译为英文） |
| style | string | 否 | 预设风格 ID，如 "happy"、"epic" |
| duration | integer | 否 | 时长秒数，默认 10，可选 5/10/15/30 |
| temperature | float | 否 | 生成温度，默认 1.0，范围 0.1-2.0 |
| top_k | integer | 否 | Top-K 采样，默认 250，范围 0-1000 |
| top_p | float | 否 | Top-P 采样，默认 0.95，范围 0.0-1.0 |

**请求示例：**
```json
{
    "prompt": "欢快的钢琴曲，适合早晨听",
    "style": "happy",
    "duration": 10,
    "temperature": 1.0,
    "top_k": 250,
    "top_p": 0.95
}
```

**响应示例（成功）：**
```json
{
    "code": 200,
    "message": "生成成功",
    "data": {
        "id": 1,
        "prompt": "欢快的钢琴曲，适合早晨听",
        "style": "happy",
        "duration": 10,
        "file_url": "/api/music/1",
        "file_size": 640256,
        "temperature": 1.0,
        "created_at": "2026-03-02 14:30:00"
    }
}
```

**响应示例（模型未就绪）：**
```json
{
    "code": 503,
    "message": "模型加载中，请稍后再试",
    "data": null
}
```

**响应示例（正在生成中）：**
```json
{
    "code": 429,
    "message": "当前有任务正在生成，请稍后再试",
    "data": null
}
```

> ⚠️ **注意**：生成音乐是计算密集型任务，CPU 模式下可能需要 30-60 秒。前端应显示加载动画并设置较长的超时时间。

---

### 4. 获取音频文件

**GET** `/api/music/{id}`

获取生成的音频文件，用于播放和下载。

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 音乐记录 ID |

**响应**：返回 WAV 音频文件流

- Content-Type: `audio/wav`
- 可直接用于 `<audio>` 标签的 `src` 属性

**错误响应：**
```json
{
    "code": 404,
    "message": "音频文件不存在",
    "data": null
}
```

---

### 5. 获取生成历史

**GET** `/api/history`

分页获取音乐生成历史记录。

**查询参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页条数，默认 12 |
| style | string | 否 | 按风格筛选 |

**请求示例：**
```
GET /api/history?page=1&page_size=12&style=happy
```

**响应示例：**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total": 25,
        "page": 1,
        "page_size": 12,
        "items": [
            {
                "id": 25,
                "prompt": "欢快的钢琴曲",
                "style": "happy",
                "duration": 10,
                "file_url": "/api/music/25",
                "file_size": 640256,
                "temperature": 1.0,
                "created_at": "2026-03-02 14:30:00"
            }
        ]
    }
}
```

---

### 6. 删除历史记录

**DELETE** `/api/history/{id}`

删除指定的生成记录及对应音频文件。

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 音乐记录 ID |

**响应示例：**
```json
{
    "code": 200,
    "message": "删除成功",
    "data": null
}
```

---

## 📌 统一响应格式

所有接口统一使用以下 JSON 格式：

```json
{
    "code": 200,
    "message": "描述信息",
    "data": {}
}
```

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 429 | 当前有任务正在生成（限流） |
| 500 | 服务器内部错误 |
| 503 | 模型未就绪 |
