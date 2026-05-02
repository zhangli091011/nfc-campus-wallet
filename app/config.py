"""
Configuration management for NFC Campus E-Wallet System.

Loads configuration from environment variables with sensible defaults.
Validates required configuration values on startup.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Security Configuration
    secret_key: str = Field(
        ...,
        description="Secret key for signature verification (required)"
    )
    
    # Database Configuration
    database_host: str = Field(
        default="localhost",
        description="MySQL database host"
    )
    database_port: int = Field(
        default=3306,
        description="MySQL database port"
    )
    database_name: str = Field(
        default="nfc_wallet",
        description="MySQL database name"
    )
    database_user: str = Field(
        ...,
        description="MySQL database user (required)"
    )
    database_password: str = Field(
        ...,
        description="MySQL database password (required)"
    )
    
    # Timestamp Validation Configuration
    timestamp_window: int = Field(
        default=60,
        description="Timestamp validation window in seconds (default: 60)"
    )
    
    # Transaction Configuration
    max_transaction_amount: float = Field(
        default=10000.00,
        description="Maximum transaction amount (default: 10000.00)"
    )
    
    # Database Connection Pool Configuration
    database_pool_size: int = Field(
        default=10,
        description="Database connection pool size (default: 10)"
    )
    database_max_overflow: int = Field(
        default=20,
        description="Maximum connections beyond pool_size (default: 20)"
    )
    database_pool_timeout: int = Field(
        default=30,
        description="Timeout in seconds for getting connection from pool (default: 30)"
    )
    database_pool_recycle: int = Field(
        default=3600,
        description="Recycle connections after this many seconds (default: 3600)"
    )
    
    # Server Configuration
    server_host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    server_port: int = Field(
        default=8000,
        description="Server port"
    )
    
    @property
    def database_url(self) -> str:
        """Construct database URL from configuration."""
        return (
            f"mysql+pymysql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )
    
    @field_validator("timestamp_window")
    @classmethod
    def validate_timestamp_window(cls, v):
        """Ensure timestamp window is positive."""
        if v <= 0:
            raise ValueError("timestamp_window must be positive")
        return v
    
    @field_validator("max_transaction_amount")
    @classmethod
    def validate_max_transaction_amount(cls, v):
        """Ensure max transaction amount is positive."""
        if v <= 0:
            raise ValueError("max_transaction_amount must be positive")
        return v
    @field_validator("database_pool_size")
    @classmethod
    def validate_pool_size(cls, v):
        """Ensure pool size is positive."""
        if v <= 0:
            raise ValueError("database_pool_size must be positive")
        return v
    
    @field_validator("database_max_overflow")
    @classmethod
    def validate_max_overflow(cls, v):
        """Ensure max overflow is non-negative."""
        if v < 0:
            raise ValueError("database_max_overflow must be non-negative")
        return v
    
    @field_validator("database_pool_timeout")
    @classmethod
    def validate_pool_timeout(cls, v):
        """Ensure pool timeout is positive."""
        if v <= 0:
            raise ValueError("database_pool_timeout must be positive")
        return v
    
    @field_validator("database_pool_recycle")
    @classmethod
    def validate_pool_recycle(cls, v):
        """Ensure pool recycle is positive."""
        if v <= 0:
            raise ValueError("database_pool_recycle must be positive")
        return v


# Global settings instance
settings: Optional[Settings] = None


def load_settings() -> Settings:
    """
    Load and validate application settings.
    
    Raises:
        ValueError: If required configuration values are missing
        
    Returns:
        Settings: Validated settings instance
    """
    global settings
    
    try:
        settings = Settings()
        return settings
    except Exception as e:
        raise ValueError(
            f"Failed to load configuration: {e}. "
            "Ensure required environment variables are set: "
            "SECRET_KEY, DATABASE_USER, DATABASE_PASSWORD"
        )


def get_settings() -> Settings:
    """
    Get the current settings instance.
    
    Returns:
        Settings: Current settings instance
        
    Raises:
        RuntimeError: If settings have not been loaded
    """
    if settings is None:
        raise RuntimeError(
            "Settings not loaded. Call load_settings() first."
        )
    return settings
