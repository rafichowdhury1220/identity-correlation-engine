"""Configuration management for Identity Correlation Engine"""

import os
from typing import Dict, Any, Optional
import yaml


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file
    
    Falls back to environment variables and defaults
    
    Args:
        config_path: Path to config file (YAML)
    
    Returns:
        Configuration dictionary
    """
    config = get_default_config()
    
    # Load from file if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            file_config = yaml.safe_load(f) or {}
            config.update(file_config)
    
    # Override with environment variables
    config.update(get_env_config())
    
    return config


def get_default_config() -> Dict[str, Any]:
    """Get default configuration
    
    Returns:
        Default configuration dictionary
    """
    return {
        "identity_engine": {
            "name": "Identity Correlation Engine",
            "version": "1.0.0",
        },
        "sources": {
            "workday": {
                "enabled": True,
                "connector_type": "rest_api",
            },
            "activedirectory": {
                "enabled": True,
                "connector_type": "ldap",
            },
            "okta": {
                "enabled": True,
                "connector_type": "rest_api",
            },
        },
        "normalization": {
            "case_sensitive": False,
            "remove_diacritics": True,
            "standardize_spacing": True,
            "remove_punctuation": False,
        },
        "matching": {
            "strategies": [
                {
                    "name": "exact_match",
                    "weight": 0.4,
                    "threshold": 0.95,
                },
                {
                    "name": "fuzzy_match",
                    "weight": 0.3,
                    "algorithm": "levenshtein",
                    "threshold": 0.85,
                },
                {
                    "name": "composite_match",
                    "weight": 0.2,
                    "threshold": 0.80,
                    "field_weights": {
                        "email": 0.4,
                        "first_name": 0.3,
                        "last_name": 0.3,
                    },
                },
                {
                    "name": "ml_match",
                    "weight": 0.1,
                    "model_path": "models/trained_matcher.pkl",
                    "threshold": 0.75,
                },
            ],
            "minimum_confidence": 0.85,
            "fuzzy": {
                "threshold": 0.85,
            },
        },
        "storage": {
            "backend": "in_memory",
            "connection_string": None,
        },
        "audit": {
            "enabled": True,
            "immutable_log": True,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }


def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables
    
    Returns:
        Configuration from environment variables
    """
    config = {}
    
    # Database configuration
    if os.getenv("DATABASE_URL"):
        config.setdefault("storage", {})["connection_string"] = os.getenv("DATABASE_URL")
        config["storage"]["backend"] = "postgresql"
    
    # Source system credentials (would be set in production)
    if os.getenv("WORKDAY_URL"):
        config.setdefault("sources", {}).setdefault("workday", {})["base_url"] = (
            os.getenv("WORKDAY_URL")
        )
    
    if os.getenv("OKTA_URL"):
        config.setdefault("sources", {}).setdefault("okta", {})["base_url"] = (
            os.getenv("OKTA_URL")
        )
    
    # Matching configuration
    if os.getenv("MATCHING_THRESHOLD"):
        config.setdefault("matching", {})["minimum_confidence"] = float(
            os.getenv("MATCHING_THRESHOLD")
        )
    
    # Logging configuration
    if os.getenv("LOG_LEVEL"):
        config.setdefault("logging", {})["level"] = os.getenv("LOG_LEVEL")
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration
    
    Args:
        config: Configuration dictionary
    
    Returns:
        True if valid, raises exception otherwise
    """
    required_keys = ["matching", "normalization"]
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    
    # Validate matching config
    min_confidence = config["matching"].get("minimum_confidence", 0.85)
    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError(f"minimum_confidence must be between 0 and 1, got {min_confidence}")
    
    return True
