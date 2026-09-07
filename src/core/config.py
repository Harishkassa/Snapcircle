from src.core import *

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )

    # General
    PROJECT_NAME: str = "Enterprise-FastAPI-Service"
    ENVIRONMENT: str

    # Database Components
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    TESTPOSTGRES_DB: str

    # Assemble Database URL dynamically (Production pattern)
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg", # Using standard enterprise async/sync driver pattern
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB
        )   
    
    @computed_field
    @property
    def SQLALCHEMY_TEST_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg", # Using standard enterprise async/sync driver pattern
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.TESTPOSTGRES_DB
        )   
    
    # aws cloud setup
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_ENDPOINT_URL: str | None = None
    AWS_S3_BUCKET_NAME: str

    # Email setup
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str

    # Redis connection setup
    REDIS_PORT: int 
    REDIS_PASSWORD: str
    REDIS_HOST: str

    # Otp expiration and lock
    OTP_EXPIRE_SECONDS: int
    OTP_LOCK_SECONDS: int

    # Blacklisted token
    ACCESS_TOKEN_EXPIRES_MINUTES: int
    ALGORITHM: str
    SECURITY_KEY: str

    # Twilio SMS setup
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    DEFAULT_COUNTRY_CODE: str = "+91"
    
    REFRESH_TOKEN_EXPIRE_DAYS : int = 7
    REFRESH_COOKIE_NAME : str = "refresh_token"

    LOG_LEVEL : str = "DEBUG" 
    
settings = Settings()
