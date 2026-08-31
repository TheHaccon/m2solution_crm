from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://crm:changeme@127.0.0.1:5432/crm"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    public_app_url: str = "http://localhost:5173"
    seed_email: str = "admin@m2solution.com"
    seed_password: str = "changeme"
    company_name: str = "M2 Solution"
    company_email: str = "billing@m2solution.com"
    company_address: str = ""
    company_phone: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
