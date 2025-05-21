"""
Secure configuration management for BensBot trading system.

This module provides utilities for secure configuration management including:
- Loading configuration from multiple sources with priority
- Secret encryption/decryption
- Environment-specific configuration
- Validation of configuration
"""

import os
import json
import yaml
import logging
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Set
from dataclasses import dataclass
import tempfile
import uuid
import shutil
from contextlib import contextmanager
import dotenv
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

@dataclass
class ConfigSource:
    """Represents a source of configuration with priority."""
    name: str
    source_type: str  # 'file', 'env', 'keyring', 'vault', etc.
    location: str  # Path, URL, or identifier
    format: Optional[str] = None  # 'json', 'yaml', 'toml', 'ini', etc.
    priority: int = 100  # Higher values override lower ones
    is_secret: bool = False  # Whether this source contains sensitive data
    enabled: bool = True  # Whether this source is enabled

class SecureConfigManager:
    """
    Secure configuration manager with support for encryption and multiple sources.
    """
    
    def __init__(
        self,
        config_dir: str = "./config",
        app_name: str = "bensbot",
        env: Optional[str] = None,
        master_key_env_var: str = "BENSBOT_MASTER_KEY",
        default_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the secure configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
            app_name: Application name for namespacing
            env: Environment (development, staging, production)
            master_key_env_var: Environment variable for master encryption key
            default_config: Default configuration values
        """
        self.config_dir = Path(config_dir)
        self.app_name = app_name
        self.env = env or os.environ.get("BENSBOT_ENV", "development")
        self.master_key_env_var = master_key_env_var
        
        # Get key for decryption
        self._master_key = self._get_master_key()
        
        # Load .env file if present
        dotenv_path = Path(".env")
        if dotenv_path.exists():
            dotenv.load_dotenv(dotenv_path)
        
        # Create config directory if needed
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Default configuration and sources
        self._default_config = default_config or {}
        self._config_sources: List[ConfigSource] = []
        self._config_cache: Dict[str, Any] = {}
        self._loaded = False
        
        # Set up default sources
        self._setup_default_sources()
    
    def _setup_default_sources(self):
        """Set up default configuration sources with priorities."""
        # Default configuration file
        self.add_source(
            name="default",
            source_type="file",
            location=str(self.config_dir / "default.yaml"),
            format="yaml",
            priority=10
        )
        
        # Environment-specific configuration
        self.add_source(
            name=f"env-{self.env}",
            source_type="file",
            location=str(self.config_dir / f"{self.env}.yaml"),
            format="yaml",
            priority=20
        )
        
        # Local development overrides (not committed to version control)
        self.add_source(
            name="local",
            source_type="file",
            location=str(self.config_dir / "local.yaml"),
            format="yaml",
            priority=30
        )
        
        # Environment variables
        self.add_source(
            name="env-vars",
            source_type="env",
            location=f"{self.app_name.upper()}_",
            priority=40
        )
        
        # Encrypted secrets
        self.add_source(
            name="secrets",
            source_type="file",
            location=str(self.config_dir / "secrets.enc"),
            is_secret=True,
            priority=50
        )
    
    def add_source(
        self,
        name: str,
        source_type: str,
        location: str,
        format: Optional[str] = None,
        priority: int = 100,
        is_secret: bool = False,
        enabled: bool = True
    ):
        """
        Add a configuration source.
        
        Args:
            name: Unique name for this source
            source_type: Type of source ('file', 'env', etc.)
            location: Path, URL, or identifier
            format: Format for file sources
            priority: Priority (higher values override lower ones)
            is_secret: Whether this source contains sensitive data
            enabled: Whether this source is enabled
        """
        source = ConfigSource(
            name=name,
            source_type=source_type,
            location=location,
            format=format,
            priority=priority,
            is_secret=is_secret,
            enabled=enabled
        )
        
        # Replace existing source with same name
        self._config_sources = [s for s in self._config_sources if s.name != name]
        self._config_sources.append(source)
        
        # Sort by priority
        self._config_sources.sort(key=lambda s: s.priority)
        
        # Invalidate cache
        self._loaded = False
        self._config_cache = {}
    
    def load(self, reload: bool = False) -> Dict[str, Any]:
        """
        Load configuration from all sources.
        
        Args:
            reload: Whether to force reload
            
        Returns:
            Merged configuration
        """
        if self._loaded and not reload:
            return self._config_cache
        
        # Start with default config
        config = self._default_config.copy()
        
        # Load from each source in priority order
        for source in self._config_sources:
            if not source.enabled:
                continue
            
            try:
                source_config = self._load_from_source(source)
                if source_config:
                    # Deep merge
                    config = self._deep_merge(config, source_config)
            except Exception as e:
                if source.source_type == "file" and "default" in source.name:
                    # Critical error if default config can't be loaded
                    logger.error(f"Failed to load default config: {e}")
                    raise
                else:
                    # Just log errors for other sources
                    logger.warning(f"Failed to load config from {source.name}: {e}")
        
        # Store in cache
        self._config_cache = config
        self._loaded = True
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        config = self.load()
        
        # Support dot notation
        if "." in key:
            parts = key.split(".")
            value = config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        
        return config.get(key, default)
    
    def set(self, key: str, value: Any, source_name: Optional[str] = None) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
            source_name: Name of source to update (defaults to highest priority)
        """
        # Find source to update
        source = None
        if source_name:
            for s in self._config_sources:
                if s.name == source_name:
                    source = s
                    break
            if not source:
                raise ValueError(f"Config source '{source_name}' not found")
        else:
            # Get highest priority writable source
            for s in reversed(self._config_sources):
                if s.source_type == "file" and s.enabled:
                    source = s
                    break
            
            if not source:
                raise ValueError("No writable config source found")
        
        # Load current config from the source
        try:
            source_config = self._load_from_source(source) or {}
        except Exception:
            source_config = {}
        
        # Update with new value
        if "." in key:
            parts = key.split(".")
            current = source_config
            for i, part in enumerate(parts[:-1]):
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            source_config[key] = value
        
        # Save back to source
        self._save_to_source(source, source_config)
        
        # Invalidate cache
        self._loaded = False
        self._config_cache = {}
    
    def set_secret(self, key: str, value: str) -> None:
        """
        Set a secret value in the encrypted secrets store.
        
        Args:
            key: Secret key
            value: Secret value
        """
        # Find secrets source
        secrets_source = None
        for source in self._config_sources:
            if source.is_secret and source.enabled:
                secrets_source = source
                break
        
        if not secrets_source:
            raise ValueError("No secrets source configured")
        
        try:
            # Load current secrets
            current_secrets = self._load_from_source(secrets_source) or {}
        except Exception:
            current_secrets = {}
        
        # Add/update secret
        if "." in key:
            parts = key.split(".")
            current = current_secrets
            for i, part in enumerate(parts[:-1]):
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            current_secrets[key] = value
        
        # Save back
        self._save_to_source(secrets_source, current_secrets)
        
        # Invalidate cache
        self._loaded = False
        self._config_cache = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.load().copy()
    
    def _load_from_source(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """
        Load configuration from a single source.
        
        Args:
            source: Configuration source
            
        Returns:
            Configuration from source or None if not available
        """
        if source.source_type == "file":
            return self._load_from_file(source)
        elif source.source_type == "env":
            return self._load_from_env(source)
        elif source.source_type == "keyring":
            return self._load_from_keyring(source)
        else:
            logger.warning(f"Unsupported config source type: {source.source_type}")
            return None
    
    def _load_from_file(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """
        Load configuration from a file.
        
        Args:
            source: File configuration source
            
        Returns:
            Configuration from file or None if file doesn't exist
        """
        file_path = Path(source.location)
        if not file_path.exists():
            logger.debug(f"Config file {file_path} does not exist")
            return None
        
        # Handle encrypted files
        if source.is_secret:
            if not self._master_key:
                logger.warning(f"Skipping encrypted config {source.name} because no master key is available")
                return None
            
            try:
                # Read encrypted file
                with open(file_path, "rb") as f:
                    encrypted_data = f.read()
                
                # Decrypt
                fernet = self._get_fernet()
                try:
                    decrypted_data = fernet.decrypt(encrypted_data).decode("utf-8")
                    return json.loads(decrypted_data)
                except InvalidToken:
                    logger.error(f"Failed to decrypt {source.name} - invalid encryption key")
                    return None
            except Exception as e:
                logger.error(f"Error loading encrypted config {source.name}: {e}")
                return None
        
        # Handle regular files
        try:
            with open(file_path, "r") as f:
                format = source.format or file_path.suffix.lstrip(".")
                
                if format.lower() in ("yaml", "yml"):
                    return yaml.safe_load(f)
                elif format.lower() == "json":
                    return json.load(f)
                else:
                    logger.warning(f"Unsupported config format: {format}")
                    return None
        except Exception as e:
            logger.error(f"Error loading config file {source.name}: {e}")
            return None
    
    def _load_from_env(self, source: ConfigSource) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Args:
            source: Environment configuration source
            
        Returns:
            Configuration from environment variables
        """
        prefix = source.location
        result = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to nested structure
                config_key = key[len(prefix):].lower()
                
                # Handle nested keys (using double underscore as separator)
                if "__" in config_key:
                    parts = config_key.split("__")
                    current = result
                    for i, part in enumerate(parts[:-1]):
                        if part not in current:
                            current[part] = {}
                        elif not isinstance(current[part], dict):
                            # If this part exists but is not a dict, create a new dict
                            # and move the existing value to a special key
                            old_value = current[part]
                            current[part] = {"_value": old_value}
                        current = current[part]
                    current[parts[-1]] = self._convert_env_value(value)
                else:
                    result[config_key] = self._convert_env_value(value)
        
        return result
    
    def _load_from_keyring(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """
        Load configuration from keyring/credential store.
        
        Args:
            source: Keyring configuration source
            
        Returns:
            Configuration from keyring
        """
        # For system keyring we need to import the module
        try:
            import keyring
            service_name = f"{self.app_name}-{source.location}"
            
            # Keyring typically stores individual secrets, not entire configs
            # Here we assume there's a master secret that contains JSON data
            secret_data = keyring.get_password(service_name, "config")
            if secret_data:
                try:
                    return json.loads(secret_data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in keyring config {source.name}")
            
            return None
        except ImportError:
            logger.warning("Keyring module not available")
            return None
        except Exception as e:
            logger.error(f"Error loading from keyring {source.name}: {e}")
            return None
    
    def _save_to_source(self, source: ConfigSource, config_data: Dict[str, Any]) -> None:
        """
        Save configuration to a source.
        
        Args:
            source: Configuration source
            config_data: Configuration data to save
        """
        if source.source_type == "file":
            self._save_to_file(source, config_data)
        elif source.source_type == "keyring":
            self._save_to_keyring(source, config_data)
        else:
            logger.warning(f"Cannot save to config source type: {source.source_type}")
    
    def _save_to_file(self, source: ConfigSource, config_data: Dict[str, Any]) -> None:
        """
        Save configuration to a file.
        
        Args:
            source: File configuration source
            config_data: Configuration data to save
        """
        file_path = Path(source.location)
        
        # Create directory if needed
        os.makedirs(file_path.parent, exist_ok=True)
        
        # Handle encrypted files
        if source.is_secret:
            if not self._master_key:
                raise ValueError("Cannot save encrypted config without master key")
            
            # Convert to JSON and encrypt
            json_data = json.dumps(config_data, indent=2)
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(json_data.encode("utf-8"))
            
            # Write securely
            temp_file = self._secure_temp_file()
            try:
                with open(temp_file, "wb") as f:
                    f.write(encrypted_data)
                
                # Replace original file
                shutil.move(temp_file, file_path)
            finally:
                # Clean up temp file if still exists
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            
            return
        
        # Handle regular files
        format = source.format or file_path.suffix.lstrip(".")
        
        # Write securely using temp file
        temp_file = self._secure_temp_file()
        try:
            with open(temp_file, "w") as f:
                if format.lower() in ("yaml", "yml"):
                    yaml.dump(config_data, f, default_flow_style=False)
                elif format.lower() == "json":
                    json.dump(config_data, f, indent=2)
                else:
                    raise ValueError(f"Unsupported config format: {format}")
            
            # Replace original file
            shutil.move(temp_file, file_path)
        finally:
            # Clean up temp file if still exists
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def _save_to_keyring(self, source: ConfigSource, config_data: Dict[str, Any]) -> None:
        """
        Save configuration to keyring/credential store.
        
        Args:
            source: Keyring configuration source
            config_data: Configuration data to save
        """
        try:
            import keyring
            service_name = f"{self.app_name}-{source.location}"
            
            # Convert to JSON and store
            json_data = json.dumps(config_data)
            keyring.set_password(service_name, "config", json_data)
        except ImportError:
            logger.warning("Keyring module not available")
            raise ValueError("Keyring module not available")
        except Exception as e:
            logger.error(f"Error saving to keyring {source.name}: {e}")
            raise
    
    def _get_master_key(self) -> Optional[bytes]:
        """
        Get master encryption key from environment.
        
        Returns:
            Master key as bytes or None if not available
        """
        key = os.environ.get(self.master_key_env_var)
        if not key:
            return None
        
        try:
            # Decode key (assuming base64 encoding)
            return base64.b64decode(key)
        except Exception as e:
            logger.error(f"Invalid master key format: {e}")
            return None
    
    def generate_key(self) -> str:
        """
        Generate a new master encryption key.
        
        Returns:
            Base64-encoded master key
        """
        key = Fernet.generate_key()
        return base64.b64encode(key).decode("utf-8")
    
    def _get_fernet(self) -> Fernet:
        """
        Get Fernet encryption instance.
        
        Returns:
            Fernet instance for encryption/decryption
        
        Raises:
            ValueError: If master key is not available
        """
        if not self._master_key:
            raise ValueError("No master key available for encryption/decryption")
        
        # Derive a key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.app_name.encode(),
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._master_key))
        
        return Fernet(key)
    
    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable string to appropriate type.
        
        Args:
            value: String value from environment variable
            
        Returns:
            Converted value
        """
        # Convert common types
        if value.lower() in ("true", "yes", "1"):
            return True
        elif value.lower() in ("false", "no", "0"):
            return False
        elif value.lower() in ("none", "null"):
            return None
        
        # Try to convert to numeric types
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            # Return as string if not a numeric value
            return value
    
    def _deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            dict1: Base dictionary
            dict2: Dictionary to merge on top
            
        Returns:
            Merged dictionary
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _secure_temp_file(self) -> str:
        """
        Create a secure temporary file.
        
        Returns:
            Path to temporary file
        """
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"{self.app_name}-{uuid.uuid4().hex}.tmp")
        return temp_file

@contextmanager
def secure_config(
    config_dir: str = "./config",
    app_name: str = "bensbot",
    env: Optional[str] = None,
    master_key_env_var: str = "BENSBOT_MASTER_KEY",
    default_config: Optional[Dict[str, Any]] = None
):
    """
    Context manager for secure configuration.
    
    Args:
        config_dir: Directory containing configuration files
        app_name: Application name for namespacing
        env: Environment (development, staging, production)
        master_key_env_var: Environment variable for master encryption key
        default_config: Default configuration values
    
    Yields:
        SecureConfigManager instance
    """
    config_manager = SecureConfigManager(
        config_dir=config_dir,
        app_name=app_name,
        env=env,
        master_key_env_var=master_key_env_var,
        default_config=default_config
    )
    
    try:
        yield config_manager
    finally:
        # Perform any cleanup if needed
        pass

# Global instance for easier access
config_manager = None 