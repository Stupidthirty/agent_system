# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # RabbitMQ配置
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # OpenAI配置
    OPENAI_API_KEY: str = "your-api-key"
    
    # Worker配置
    WORKER_NODES: int = 2
    
    # Agent配置
    AGENTS_REGISTRY_URL: str = "redis://localhost:6379/1"
    
    class Config:
        env_file = ".env"

settings = Settings()
