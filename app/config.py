import json
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    SECRET_KEY: str = Field(default="dev-secret-key-library-catalog-watcher-2026")
    
    # Library Catalog Target Parameters (Configurable via ENV)
    LIBRARY_BASE_URL: str = Field(default="https://givat-shmuel.libraries.co.il")
    LIBRARY_SITE_NAME: str = Field(default="LIB_givat-shmuel")
    LIBRARY_NEW_NAME_MADE: str = Field(default="30213")
    LIBRARY_BUYER_ID: str = Field(default="285010242")
    LIBRARY_DISPLAY_NAME: str = Field(default="הספרייה העירונית")
    
    # MongoDB Connection (MongoDB Atlas connection string or local)
    MONGODB_URI: str = Field(default="mongodb://localhost:27017")
    DATABASE_NAME: str = Field(default="library_catalog_db")
    
    # Cron Secret Key for /api/cron/check endpoint
    CRON_SECRET: str = Field(default="cron-secret-library-watcher-secure")
    
    # Optional in-process polling interval
    ENABLE_INTERNAL_SCHEDULER: bool = Field(default=False)
    POLL_INTERVAL_MINUTES: int = Field(default=15)
    
    # Brevo Email
    BREVO_API_KEY: str = Field(default="")
    BREVO_SENDER_EMAIL: str = Field(default="noreply@library-watcher.local")
    BREVO_SENDER_NAME: str = Field(default="התראות ספרייה")
    
    # Predefined users JSON
    SEED_USERS: str = Field(
        default='[{"username": "admin", "email": "admin@example.com", "password": "password123"}]'
    )
    
    @property
    def parsed_seed_users(self):
        try:
            return json.loads(self.SEED_USERS)
        except Exception:
            return []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
