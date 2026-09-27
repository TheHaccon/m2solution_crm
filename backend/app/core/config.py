from pydantic_settings import BaseSettings, SettingsConfigDict

_OLD_SEED_EMAIL = "admin@m2solution.com"
_DEFAULT_SEED_EMAILS = "matcote111@gmail.com,mathieu.laureti@gmail.com"

SEED_DISPLAY_NAMES = {
    "matcote111@gmail.com": "Mat",
    "mathieu.laureti@gmail.com": "Mathieu Laureti",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://crm:changeme@127.0.0.1:5432/crm"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    public_app_url: str = "http://localhost:5173"
    seed_email: str = _DEFAULT_SEED_EMAILS
    seed_password: str = "changeme"
    company_name: str = "M2 Solution"
    company_email: str = "billing@m2solution.com"
    company_address: str = ""
    company_phone: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""
    files_root: str = "data/files"
    files_max_bytes: int = 25_000_000

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def google_oauth_configured(self) -> bool:
        return bool(
            self.google_client_id.strip()
            and self.google_client_secret.strip()
            and self.google_redirect_uri.strip()
        )

    @property
    def seed_email_list(self) -> list[str]:
        raw = self.seed_email.strip()
        if raw.lower() in {"", _OLD_SEED_EMAIL}:
            raw = _DEFAULT_SEED_EMAILS
        emails: list[str] = []
        for part in raw.split(","):
            email = part.strip().lower()
            if email and email not in emails:
                emails.append(email)
        return emails


settings = Settings()


def seed_display_name(email: str) -> str:
    if email in SEED_DISPLAY_NAMES:
        return SEED_DISPLAY_NAMES[email]
    local = email.split("@", 1)[0]
    return local.replace(".", " ").replace("_", " ").title()
