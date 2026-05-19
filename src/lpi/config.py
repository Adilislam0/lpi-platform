from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    daily_cost_cap_usd: float = 10.0

    class Config:
        env_file = ".env"


settings = Settings()
