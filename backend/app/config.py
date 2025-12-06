from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Greenhouse Backend"
    database_url: str = "sqlite:///./backend/dev.db"
    jwt_secret: str = "replace_this_with_secure_random_value"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    thingsboard_url: str = ""
    thingsboard_token: str = ""
    thingsboard_device_check_path: str = "api/device/{serial_number}"
    thingsboard_username: str = ""
    thingsboard_password: str = ""
    thingsboard_login_path: str = "/api/auth/login"
    thingsboard_request_timeout: float = 10.0
    thingsboard_telemetry_path: str = "/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
    thingsboard_telemetry_keys: str = "temperature,humidity,windowPosition"
    thingsboard_telemetry_limit: int = 120

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"