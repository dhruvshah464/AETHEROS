from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "dev-secret-change-in-production"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql://aetheros:aetheros@localhost:5432/aetheros"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-4o-mini"
    fallback_llm_provider: str = "ollama"
    fallback_llm_model: str = "llama3.2"

    telemetry_interval_ms: int = 1000
    agent_max_iterations: int = 10
    agent_approval_mode: bool = True
    browser_headless: bool = False
    browser_approval_mode: bool = True
    terminal_sandbox_dir: str = "/tmp/aetheros-sandbox"
    terminal_allowed_commands: str = "ls,cat,pwd,echo,python,python3,node,npm,git,curl,wget,mkdir,touch,cp,mv,rm,find,grep,head,tail,wc,whoami,date"
    whisper_model: str = "base"
    tts_voice: str = "en-US-GuyNeural"
    demo_mode_enabled: bool = True
    event_store_path: str = "data/event_store.jsonl"
    plugins_dir: str = "plugins"

    chroma_host: str = "localhost"
    chroma_port: int = 8001
    embedding_model: str = "all-MiniLM-L6-v2"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def terminal_allowed_list(self) -> list[str]:
        return [c.strip() for c in self.terminal_allowed_commands.split(",") if c.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
