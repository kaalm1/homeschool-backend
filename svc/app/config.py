from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Security
    secret_key: str = Field(..., description="Secret key for JWT encoding")
    access_token_expire_minutes: int = Field(
        default=60 * 24 * 30, description="Access token expiration in minutes"
    )

    # Database
    database_url: str = Field(
        default="postgresql://homeschool_user:random@localhost:5432/homeschool_db",
        description="Database connection URL",
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of allowed origins",
    )

    # Environment
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # LLM Configuration
    openai_api_key: Optional[str] = Field(
        default=None, description="OpenAI API key for LLM services"
    )
    openai_base_url: Optional[str] = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenAI Base URL for LLM services. Use https://openrouter.ai/models to find models.",
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use (gpt-4o-mini, gpt-4o, gpt-4-turbo, etc.)",
    )
    llm_temperature: float = Field(
        default=0.0,
        description="Temperature for LLM responses (0.0-2.0)",
        ge=0.0,
        le=2.0,
    )
    llm_max_retries: int = Field(
        default=1,
        description="Maximum number of retries for failed LLM requests",
        ge=0,
        le=5,
    )
    llm_timeout: float = Field(
        default=30.0, description="Timeout in seconds for LLM requests", gt=0
    )
    llm_enabled: bool = Field(
        default=True, description="Whether LLM features are enabled"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment setting."""
        allowed_environments = ["development", "staging", "production"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of: {allowed_environments}")
        return v

    @field_validator("llm_model")
    def validate_llm_model(cls, v: str) -> str:
        """Validate LLM model setting."""
        allowed_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "deepseek/deepseek-chat-v3.1:free",
            "tngtech/deepseek-r1t-chimera:free",
            "qwen/qwen3-coder:free",
        ]
        if v not in allowed_models:
            raise ValueError(f"LLM model must be one of: {allowed_models}")
        return v

    @model_validator(mode="after")
    def validate_llm_configuration(self) -> "Settings":
        # Can access all fields via self.field_name
        if self.llm_enabled and not self.openai_api_key:
            raise ValueError("API key required when LLM enabled")
        return self

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def is_llm_available(self) -> bool:
        """Check if LLM features are available."""
        return self.llm_enabled and bool(self.openai_api_key)

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
