"""
Mobile and Cross-platform Configuration
"""
import os
from typing import Dict, Any, List

# Mobile-specific settings
MOBILE_CONFIG = {
    "max_upload_size": 5 * 1024 * 1024,  # 5MB for mobile
    "compression_enabled": True,
    "image_optimization": True,
    "cache_enabled": True,
    "offline_mode_enabled": True
}

# iOS-specific settings
IOS_CONFIG = {
    "minimum_version": "13.0",
    "push_notifications": True,
    "touch_id_enabled": True,
    "face_id_enabled": True,
    "background_fetch_interval": 900  # 15 minutes
}

# Platform-specific paths
PLATFORM_PATHS = {
    "Darwin": {  # macOS
        "data_dir": "~/Library/Application Support/PinnacleCopilot",
        "cache_dir": "~/Library/Caches/PinnacleCopilot",
        "log_dir": "~/Library/Logs/PinnacleCopilot"
    },
    "iOS": {  # iOS
        "data_dir": "Documents",
        "cache_dir": "Library/Caches",
        "log_dir": "Library/Logs"
    }
}

def get_platform_paths() -> Dict[str, str]:
    """Get platform-specific paths"""
    import platform
    system = platform.system()
    
    # Default to macOS paths
    paths = PLATFORM_PATHS.get(system, PLATFORM_PATHS["Darwin"])
    
    # Expand user paths
    return {k: os.path.expanduser(v) for k, v in paths.items()}

def get_mobile_config() -> Dict[str, Any]:
    """Get mobile-specific configuration"""
    return MOBILE_CONFIG

def get_ios_config() -> Dict[str, Any]:
    """Get iOS-specific configuration"""
    return IOS_CONFIG

# Create necessary directories
def setup_platform_directories() -> None:
    """Create platform-specific directories if they don't exist"""
    paths = get_platform_paths()
    for path in paths.values():
        os.makedirs(path, exist_ok=True)

# Mobile optimization settings
MOBILE_OPTIMIZATIONS = {
    "enable_compression": True,
    "enable_caching": True,
    "enable_lazy_loading": True,
    "enable_image_optimization": True,
    "max_image_size": 1024,  # pixels
    "cache_ttl": 3600,  # 1 hour
    "offline_cache_size": 50 * 1024 * 1024  # 50MB
}
