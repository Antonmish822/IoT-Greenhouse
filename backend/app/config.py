from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Greenhouse Backend"
    database_url: str = "sqlite:///./backend/dev.db"
    jwt_secret: str = "replace_this_with_secure_random_value"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60