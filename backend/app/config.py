from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Fung-song Plus"
    navidrome_base: str = "http://your-navidrome-host:4533"
    navidrome_user: str = "your_username"
    navidrome_password: str = "your_password"
    navidrome_client: str = "fung-song-plus"
    music_roots: str = "/music"
    cors_origins: str = "*"

settings = Settings()
