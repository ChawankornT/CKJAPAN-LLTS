import json
import yaml
import os
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class FTPConfig:
    host: str
    port: int
    username: str
    password: str
    upload_path: str

@dataclass
class USRPConfig:
    sampling_rate: float
    center_freq: float
    gain: int

@dataclass
class AppConfig:
    app_name: str
    site_name: str
    ftp: FTPConfig
    usrp: USRPConfig
    data_path: str
    segment_path: str
    record_time: float

class ConfigManager:
    """
    A configuration manager that supports both JSON and YAML formats
    with environment variable overrides.
    """
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file with format detection."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        file_ext = os.path.splitext(self.config_path)[1].lower()

        with open(self.config_path, 'r') as config_file:
            if file_ext == '.json':
                self.config = json.load(config_file)
            elif file_ext in ('.yml', '.yaml'):
                self.config = yaml.safe_load(config_file)
            else:
                raise ValueError(f"Unsupported config format: {file_ext}")

        # Override with environment variables
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """Override configuration values with environment variables."""
        env_prefix = "APP_"
        for key in os.environ:
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                nested_keys = config_key.split('_')
                self._set_nested_value(self.config, nested_keys, os.environ[key])

    def _set_nested_value(self, config_dict: dict, keys: list, value: str) -> None:
        """Set a value in nested dictionary using a list of keys."""
        for key in keys[:-1]:
            config_dict = config_dict.setdefault(key, {})
        config_dict[keys[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key with optional default."""
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_ftp_config(self) -> FTPConfig:
        """Get typed ftp configuration."""
        db_config = self.config.get('ftp', {})
        return FTPConfig(
            host=db_config.get('host', 'localhost'),
            port=int(db_config.get('port', 21)),
            username=db_config.get('username', ''),
            password=db_config.get('password', ''),
            upload_path=db_config.get('path', '')
        )
    
    def get_usrp_config(self) -> USRPConfig:
        """Get typed USRP configuration."""
        usrp_config = self.config.get('usrp', {})
        return USRPConfig(
            sampling_rate=float(usrp_config.get('sampling_rate', 2e6)),
            center_freq=float(usrp_config.get('center_freq', 1000)),
            gain=int(usrp_config.get('gain', 0)),
        )

    def get_app_config(self) -> AppConfig:
        """Get typed application configuration."""
        return AppConfig(
            app_name=self.config.get('app_name', 'LLTS'),
            site_name=self.config.get('site_name', ''),
            ftp=self.get_ftp_config(),
            usrp=self.get_usrp_config(),
            data_path=self.config.get('data_path', ''),
            segment_path=self.config.get('segment_path', ''),
            record_time=float(self.config.get('record_time', 0.2)),
        )

# Usage example
if __name__ == '__main__':
    # Initialize with YAML config
    yaml_config = ConfigManager('config.yaml')
    app_config = yaml_config.get_app_config()
    
    # Access configuration values
    print(f"App Name: {app_config.app_name}")
    print(f"Site Name: {app_config.site_name}")
    print(f"Host Server: {app_config.ftp.host}")
        
    # Environment variable override example:
    # export APP_FTP_HOST=newftp.com
    # This will override the database.host value in the config
