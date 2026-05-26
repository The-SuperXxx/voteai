"""配置管理 - 从环境变量读取 API Keys"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # 智谱 AI
    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
    ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    # Kimi (月之暗面)
    KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
    KIMI_BASE_URL = "https://api.moonshot.cn/v1"

    # 阿里百炼（千问）
    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
    QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 豆包（火山方舟）
    DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")
    DOUBAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

    # 模型列表
    MODELS = [
        {
            "name": "GLM-4-Flash",
            "api_key": ZHIPU_API_KEY,
            "base_url": ZHIPU_BASE_URL,
            "model_id": "glm-4-flash",
        },
        {
            "name": "GLM-Z1-Flash",
            "api_key": ZHIPU_API_KEY,
            "base_url": ZHIPU_BASE_URL,
            "model_id": "glm-z1-flash",
        },
        {
            "name": "Qwen-Turbo",
            "api_key": QWEN_API_KEY,
            "base_url": QWEN_BASE_URL,
            "model_id": "qwen-turbo",
        },
        {
            "name": "Kimi",
            "api_key": KIMI_API_KEY,
            "base_url": KIMI_BASE_URL,
            "model_id": "moonshot-v1-8k",
        },
    ]

    # 投票配置
    VOTING_TIMEOUT = 60  # 单个 AI 调用超时（秒）
    MAX_RETRIES = 2  # 失败重试次数

    # 数据库
    DB_PATH = os.path.join(os.path.dirname(__file__), "voteai.db")


config = Config()
