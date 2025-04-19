from typing import Optional
from pydantic import BaseSettings

class MongoConfig(BaseSettings):
    """MongoDB configuration settings.
    
    All settings can be overridden by environment variables with the same name.
    """
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_USER: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_DATABASE: str = "media_db"
    MONGO_AUTH_SOURCE: str = "admin"
    MONGO_AUTH_MECHANISM: str = "SCRAM-SHA-256"
    
    @property
    def connection_string(self) -> str:
        """Generate MongoDB connection string based on configuration."""
        if self.MONGO_USER and self.MONGO_PASSWORD:
            auth = f"{self.MONGO_USER}:{self.MONGO_PASSWORD}@"
            auth_params = (f"?authSource={self.MONGO_AUTH_SOURCE}"
                         f"&authMechanism={self.MONGO_AUTH_MECHANISM}")
        else:
            auth = ""
            auth_params = ""
            
        return f"mongodb://{auth}{self.MONGO_HOST}:{self.MONGO_PORT}/{auth_params}"

# Create default config instance
mongo_config = MongoConfig() 