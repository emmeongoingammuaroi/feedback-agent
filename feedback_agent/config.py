from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_region: str = "us-east-1"
    anthropic_model: str = "anthropic.claude-sonnet-5"
    classification_confidence_threshold: float = 0.6
    max_tool_iterations: int = 6
