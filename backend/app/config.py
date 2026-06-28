from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    tmdb_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    openrouter_api_key: str = ""
    llm_provider: str = "openrouter"  # "openrouter" or "gemini"
    llm_model: str = "google/gemini-2.0-flash-exp:free"
    database_url: str = "postgresql://cineread:cineread@localhost:5433/cineread"
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]


settings = Settings()
