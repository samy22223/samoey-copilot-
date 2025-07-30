"""
iOS App Configuration Generator
"""
import json
import os
from typing import Dict, Any

def generate_ios_config() -> Dict[str, Any]:
    """Generate iOS app configuration"""
    return {
        "app": {
            "name": "Pinnacle Copilot",
            "bundle_id": "com.pinnacle.copilot",
            "version": "1.0.0",
            "build": "1",
            "minimum_ios_version": "13.0"
        },
        "api": {
            "base_url": "https://api.pinnaclecopilot.com",
            "version": "v1",
            "timeout": 30
        },
        "features": {
            "push_notifications": True,
            "biometric_auth": True,
            "offline_mode": True,
            "analytics": True
        },
        "security": {
            "certificate_pinning": True,
            "jailbreak_detection": True,
            "data_encryption": True
        },
        "ui": {
            "theme": "auto",
            "color_scheme": {
                "primary": "#007AFF",
                "secondary": "#5856D6",
                "accent": "#FF2D55"
            }
        },
        "cache": {
            "max_size_mb": 50,
            "ttl_seconds": 3600,
            "cleanup_interval": 86400
        }
    }

def save_ios_config(config: Dict[str, Any], output_path: str) -> None:
    """Save iOS configuration to file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)

def main():
    """Generate and save iOS configuration"""
    config = generate_ios_config()
    output_path = "ios/PinnacleCopilot/Config/config.json"
    save_ios_config(config, output_path)
    print(f"iOS configuration saved to {output_path}")

if __name__ == "__main__":
    main()
