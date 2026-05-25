"""应用配置，从环境变量加载"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # AI API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # 模型配置
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    llm_model: str = "claude-sonnet-4-6"

    # 应用
    app_env: str = "development"
    cors_origins: str = "https://miaoda.feishu.cn,http://localhost:3000"

    # 文件上传
    max_upload_size_mb: int = 20

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
