import json
import yaml
import os
from typing import Any, Dict, Optional

class SFTPConfig:
    """SFTP configuration class"""
    def __init__(self, config_dict: dict):
        self.host = config_dict.get('host', 'localhost')
        self.port = int(config_dict.get('port', 22))
        self.username = config_dict.get('username', '')
        self.password = config_dict.get('password', '')
        self.remote_path = config_dict.get('remote_path', '')

    def __str__(self):
        return f"SFTPConfig(host={self.host}, port={self.port}, username={self.username})"
    
class USRPConfig:
    """USRP configuration class"""
    def __init__(self, config_dict: dict):
        self.sampling_rate = float(config_dict.get('sampling_rate', 2e6))
        self.center_freq = float(config_dict.get('center_freq', 100e6))
        self.gain = int(config_dict.get('gain', 0))
        self.adc_voltage_range = int(config_dict.get('adc_voltage_range', 1))

    def __str__(self):
        return f"USRPConfig(sampling_rate={self.sampling_rate}, center_freq={self.center_freq}, gain={self.gain})"

class AppConfig:
    """Application configuration class"""
    def __init__(self, config_dict: dict):
        self.app_name = config_dict.get('app_name', 'LLTS')
        self.site_name = config_dict.get('site_name', '')
        self.data_path = config_dict.get('data_path', '')
        self.segment_path = config_dict.get('segment_path', '')
        self.record_time = float(config_dict.get('record_time', 1))
        self.trigger_level = int(config_dict.get('trigger_level', 100))
        self.sftp = SFTPConfig(config_dict.get('sftp', {}))
        self.usrp = USRPConfig(config_dict.get('usrp', {}))

    def __str__(self):
        return f"AppConfig(app_name={self.app_name}, site_name={self.site_name})"
    
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
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                # Handle nested keys (e.g., APP_SFTP_HOST)
                keys = config_key.split('_')
                current = self.config
                for k in keys[:-1]:
                    current = current.setdefault(k, {})
                # Try to convert to appropriate type
                try:
                    # Try to convert to int
                    value = int(value)
                except ValueError:
                    try:
                        # Try to convert to float
                        value = float(value)
                    except ValueError:
                        # Convert to boolean if it's a boolean string
                        if value.lower() in ('true', 'false'):
                            value = value.lower() == 'true'
                current[keys[-1]] = value

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
        
    def get_sftp_config(self) -> SFTPConfig:
        """Get SFTP configuration object."""
        return SFTPConfig(self.config.get('sftp', {}))
    
    def get_usrp_config(self) -> USRPConfig:
        """Get USRP configuration object."""
        return USRPConfig(self.config.get('usrp', {}))

    def get_app_config(self) -> AppConfig:
        """Get application configuration object."""
        return AppConfig(self.config)

# Usage example
if __name__ == '__main__':
    # Initialize config manager
    config = ConfigManager('config.yaml')

    # Get typed configuration
    app_config = config.get_app_config()
    sftp_config = config.get_sftp_config()
    usrp_config = config.get_usrp_config()
    
    # Access configuration values
    print(f"App Name: {app_config.app_name}")
    print(f"Site Name: {app_config.site_name}")
    print(f"SFTP Host: {sftp_config.host}")
    print(f"USRP Sampling Rate: {usrp_config.sampling_rate}")
        
    # Get individual values with defaults
    data_path = config.get('data_path', '/default/path')
    record_time = config.get('record_time', 1)

    # Example of accessing nested values
    sftp_host = config.get('sftp.host', 'localhost')
    print(f"SFTP Host via get(): {sftp_host}")

    # Environment variable override example:
    # export APP_SFTP_HOST=newsftp.com
    # This will override the database.host value in the config