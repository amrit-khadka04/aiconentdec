from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    groq_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    default_sample_rate: int = 30
    default_max_frames: int = 40

    class Config:
        env_file = "../.env"


settings = Settings()
