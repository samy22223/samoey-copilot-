#!/usr/bin/env python3

"""
Samoey Copilot - Configuration Generator
Automatically generates configuration files based on environment detection and mode
"""

import json
import os
import sys
import subprocess
import secrets
import string
import ipaddress
import socket
import datetime
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

class ConfigGenerator:
    def __init__(self, mode: str = "dev", project_dir: Optional[str] = None):
        self.mode = mode
        self.project_dir = Path(project_dir) if project_dir else Path(__file__).parent.parent
        self.automation_dir = self.project_dir / "automation"
        self.config_dir = self.project_dir / "config-templates"
        self.logs_dir = self.project_dir / "logs"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        
        # Load environment data
        self.env_data = self._load_environment_data()
        
        # Configuration templates
        self.config_templates = {
            "dev": self._get_dev_config(),
            "staging": self._get_staging_config(),
            "prod": self._get_prod_config()
        }
        
        # Generated configuration
        self.generated_config: Dict[str, Any] = {}
        
    def _load_environment_data(self) -> Dict[str, Any]:
        """Load environment detection data"""
        env_file = self.automation_dir / "environment.json"
        if env_file.exists():
            with open(env_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _log(self, level: str, message: str):
        """Log message with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} [{level}] {message}"
        print(log_message)
        
        # Write to log file
        log_file = self.logs_dir / "config-generator.log"
        with open(log_file, 'a') as f:
            f.write(log_message + "\n")
    
    def _log_info(self, message: str):
        self._log("INFO", message)
    
    def _log_success(self, message: str):
        self._log("SUCCESS", message)
    
    def _log_warning(self, message: str):
        self._log("WARNING", message)
    
    def _log_error(self, message: str):
        self._log("ERROR", message)
    
    def _generate_secret_key(self, length: int = 32) -> str:
        """Generate a secure secret key"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _generate_jwt_secret(self) -> str:
        """Generate JWT secret key"""
        return self._generate_secret_key(64)
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Connect to a remote server to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    def _check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
            return True
        except OSError:
            return False
    
    def _get_available_port(self, default_port: int) -> int:
        """Get an available port, fallback to default if not available"""
        if self._check_port_available(default_port):
            return default_port
        
        # Find an available port
        for port in range(default_port + 1, default_port + 100):
            if self._check_port_available(port):
                return port
        
        return default_port  # Fallback to default
    
    def _get_dev_config(self) -> Dict[str, Any]:
        """Get development configuration template"""
        return {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "samoey_copilot_dev",
                "user": "samoey_dev",
                "password": self._generate_secret_key(16),
                "pool_size": 10,
                "max_overflow": 20
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": "",
                "ssl": False
            },
            "backend": {
                "host": "localhost",
                "port": self._get_available_port(8000),
                "workers": 1,
                "reload": True,
                "debug": True,
                "log_level": "DEBUG"
            },
            "frontend": {
                "host": "localhost",
                "port": self._get_available_port(3000),
                "dev_mode": True,
                "hot_reload": True
            },
            "security": {
                "secret_key": self._generate_secret_key(),
                "jwt_secret": self._generate_jwt_secret(),
                "algorithm": "HS256",
                "access_token_expire_minutes": 30,
                "ssl_verify": False,
                "cors_origins": ["http://localhost:3000", "http://127.0.0.1:3000"]
            },
            "ai": {
                "default_provider": "openai",
                "model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.7,
                "timeout": 30,
                "retry_attempts": 3
            },
            "monitoring": {
                "enabled": True,
                "prometheus_port": self._get_available_port(9090),
                "grafana_port": self._get_available_port(3001),
                "log_level": "DEBUG"
            }
        }
    
    def _get_staging_config(self) -> Dict[str, Any]:
        """Get staging configuration template"""
        return {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "samoey_copilot_staging",
                "user": "samoey_staging",
                "password": self._generate_secret_key(24),
                "pool_size": 20,
                "max_overflow": 30
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 1,
                "password": self._generate_secret_key(16),
                "ssl": True
            },
            "backend": {
                "host": "0.0.0.0",
                "port": self._get_available_port(8000),
                "workers": 4,
                "reload": False,
                "debug": False,
                "log_level": "INFO"
            },
            "frontend": {
                "host": "0.0.0.0",
                "port": self._get_available_port(3000),
                "dev_mode": False,
                "hot_reload": False
            },
            "security": {
                "secret_key": self._generate_secret_key(64),
                "jwt_secret": self._generate_jwt_secret(),
                "algorithm": "HS256",
                "access_token_expire_minutes": 60,
                "ssl_verify": True,
                "cors_origins": ["http://localhost:3000", "https://staging.example.com"]
            },
            "ai": {
                "default_provider": "openai",
                "model": "gpt-4",
                "max_tokens": 4000,
                "temperature": 0.5,
                "timeout": 60,
                "retry_attempts": 5
            },
            "monitoring": {
                "enabled": True,
                "prometheus_port": self._get_available_port(9090),
                "grafana_port": self._get_available_port(3001),
                "log_level": "INFO"
            }
        }
    
    def _get_prod_config(self) -> Dict[str, Any]:
        """Get production configuration template"""
        return {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "samoey_copilot_prod",
                "user": "samoey_prod",
                "password": self._generate_secret_key(32),
                "pool_size": 50,
                "max_overflow": 50
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 2,
                "password": self._generate_secret_key(24),
                "ssl": True
            },
            "backend": {
                "host": "0.0.0.0",
                "port": self._get_available_port(8000),
                "workers": 8,
                "reload": False,
                "debug": False,
                "log_level": "WARNING"
            },
            "frontend": {
                "host": "0.0.0.0",
                "port": self._get_available_port(3000),
                "dev_mode": False,
                "hot_reload": False
            },
            "security": {
                "secret_key": self._generate_secret_key(128),
                "jwt_secret": self._generate_jwt_secret(),
                "algorithm": "HS256",
                "access_token_expire_minutes": 120,
                "ssl_verify": True,
                "cors_origins": ["https://yourdomain.com"]
            },
            "ai": {
                "default_provider": "openai",
                "model": "gpt-4",
                "max_tokens": 8000,
                "temperature": 0.3,
                "timeout": 120,
                "retry_attempts": 5
            },
            "monitoring": {
                "enabled": True,
                "prometheus_port": self._get_available_port(9090),
                "grafana_port": self._get_available_port(3001),
                "log_level": "WARNING"
            }
        }
    
    def _adapt_config_to_environment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt configuration based on environment capabilities"""
        if not self.env_data:
            return config
        
        # Adjust based on available memory
        memory_info = self.env_data.get("resources", {}).get("memory", {})
        if memory_info:
            memory_total = memory_info.get("total", "4GB")
            if "GB" in memory_total:
                memory_gb = float(memory_total.replace("GB", ""))
                if memory_gb < 4:
                    # Low memory configuration
                    config["database"]["pool_size"] = min(config["database"]["pool_size"], 5)
                    config["backend"]["workers"] = min(config["backend"]["workers"], 2)
        
        # Adjust based on available disk space
        disk_info = self.env_data.get("resources", {}).get("disk", {})
        if disk_info:
            disk_available = disk_info.get("available", "10GB")
            if "GB" in disk_available:
                disk_gb = float(disk_available.replace("GB", ""))
                if disk_gb < 5:
                    self._log_warning("Low disk space available. Consider freeing up space.")
        
        # Adjust based on network status
        network_status = self.env_data.get("network", {}).get("status", "good")
        if network_status == "poor":
            config["ai"]["timeout"] = min(config["ai"]["timeout"], 15)
            config["ai"]["retry_attempts"] = min(config["ai"]["retry_attempts"], 2)
        
        return config
    
    def _generate_env_file(self, config: Dict[str, Any]) -> str:
        """Generate .env file content"""
        env_lines = [
            "# Samoey Copilot Environment Configuration",
            f"# Generated on {datetime.datetime.now().isoformat()}",
            f"# Mode: {self.mode}",
            ""
        ]
        
        # Database configuration
        db_config = config["database"]
        env_lines.extend([
            "# Database Configuration",
            f"DB_HOST={db_config['host']}",
            f"DB_PORT={db_config['port']}",
            f"DB_NAME={db_config['name']}",
            f"DB_USER={db_config['user']}",
            f"DB_PASSWORD={db_config['password']}",
            f"DB_POOL_SIZE={db_config['pool_size']}",
            f"DB_MAX_OVERFLOW={db_config['max_overflow']}",
            ""
        ])
        
        # Redis configuration
        redis_config = config["redis"]
        env_lines.extend([
            "# Redis Configuration",
            f"REDIS_HOST={redis_config['host']}",
            f"REDIS_PORT={redis_config['port']}",
            f"REDIS_DB={redis_config['db']}",
            f"REDIS_PASSWORD={redis_config['password']}",
            f"REDIS_SSL={redis_config['ssl']}",
            ""
        ])
        
        # Backend configuration
        backend_config = config["backend"]
        env_lines.extend([
            "# Backend Configuration",
            f"BACKEND_HOST={backend_config['host']}",
            f"BACKEND_PORT={backend_config['port']}",
            f"BACKEND_WORKERS={backend_config['workers']}",
            f"BACKEND_RELOAD={backend_config['reload']}",
            f"BACKEND_DEBUG={backend_config['debug']}",
            f"BACKEND_LOG_LEVEL={backend_config['log_level']}",
            ""
        ])
        
        # Frontend configuration
        frontend_config = config["frontend"]
        env_lines.extend([
            "# Frontend Configuration",
            f"FRONTEND_HOST={frontend_config['host']}",
            f"FRONTEND_PORT={frontend_config['port']}",
            f"FRONTEND_DEV_MODE={frontend_config['dev_mode']}",
            f"FRONTEND_HOT_RELOAD={frontend_config['hot_reload']}",
            ""
        ])
        
        # Security configuration
        security_config = config["security"]
        env_lines.extend([
            "# Security Configuration",
            f"SECRET_KEY={security_config['secret_key']}",
            f"JWT_SECRET={security_config['jwt_secret']}",
            f"ALGORITHM={security_config['algorithm']}",
            f"ACCESS_TOKEN_EXPIRE_MINUTES={security_config['access_token_expire_minutes']}",
            f"SSL_VERIFY={security_config['ssl_verify']}",
            f"CORS_ORIGINS={','.join(security_config['cors_origins'])}",
            ""
        ])
        
        # AI configuration
        ai_config = config["ai"]
        env_lines.extend([
            "# AI Configuration",
            f"AI_DEFAULT_PROVIDER={ai_config['default_provider']}",
            f"AI_MODEL={ai_config['model']}",
            f"AI_MAX_TOKENS={ai_config['max_tokens']}",
            f"AI_TEMPERATURE={ai_config['temperature']}",
            f"AI_TIMEOUT={ai_config['timeout']}",
            f"AI_RETRY_ATTEMPTS={ai_config['retry_attempts']}",
            ""
        ])
        
        # Monitoring configuration
        monitoring_config = config["monitoring"]
        env_lines.extend([
            "# Monitoring Configuration",
            f"MONITORING_ENABLED={monitoring_config['enabled']}",
            f"PROMETHEUS_PORT={monitoring_config['prometheus_port']}",
            f"GRAFANA_PORT={monitoring_config['grafana_port']}",
            f"LOG_LEVEL={monitoring_config['log_level']}",
            ""
        ])
        
        return "\n".join(env_lines)
    
    def _generate_docker_compose_override(self, config: Dict[str, Any]) -> str:
        """Generate docker-compose.override.yml content"""
        compose_lines = [
            "version: '3.8'",
            "services:",
            ""
        ]
        
        # Backend service
        backend_config = config["backend"]
        compose_lines.extend([
            "  backend:",
            f"    environment:",
            f"      - NODE_ENV={'development' if self.mode == 'dev' else 'production'}",
            f"      - BACKEND_HOST={backend_config['host']}",
            f"      - BACKEND_PORT={backend_config['port']}",
            f"      - BACKEND_WORKERS={backend_config['workers']}",
            f"      - BACKEND_DEBUG={backend_config['debug']}",
            f"    ports:",
            f"      - \"{backend_config['port']}:{backend_config['port']}\"",
            f"    depends_on:",
            f"      - postgres",
            f"      - redis",
            ""
        ])
        
        # Frontend service
        frontend_config = config["frontend"]
        compose_lines.extend([
            "  frontend:",
            f"    environment:",
            f"      - NODE_ENV={'development' if self.mode == 'dev' else 'production'}",
            f"      - FRONTEND_HOST={frontend_config['host']}",
            f"      - FRONTEND_PORT={frontend_config['port']}",
            f"      - FRONTEND_DEV_MODE={frontend_config['dev_mode']}",
            f"    ports:",
            f"      - \"{frontend_config['port']}:{frontend_config['port']}\"",
            f"    depends_on:",
            f"      - backend",
            ""
        ])
        
        # Monitoring services (if enabled)
        if config["monitoring"]["enabled"]:
            monitoring_config = config["monitoring"]
            compose_lines.extend([
                "  prometheus:",
                f"    ports:",
                f"      - \"{monitoring_config['prometheus_port']}:9090\"",
                f"    volumes:",
                f"      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml",
                "",
                
                "  grafana:",
                f"    ports:",
                f"      - \"{monitoring_config['grafana_port']}:3000\"",
                f"    environment:",
                f"      - GF_SECURITY_ADMIN_PASSWORD={self._generate_secret_key(16)}",
                f"    depends_on:",
                f"      - prometheus",
                ""
            ])
        
        return "\n".join(compose_lines)
    
    def generate_configuration(self) -> Dict[str, Any]:
        """Generate complete configuration"""
        self._log_info(f"Generating configuration for mode: {self.mode}")
        
        # Get base configuration template
        base_config = self.config_templates.get(self.mode, self._get_dev_config())
        
        # Adapt to environment
        adapted_config = self._adapt_config_to_environment(base_config)
        
        # Add metadata
        adapted_config["_metadata"] = {
            "generated_at": datetime.datetime.now().isoformat(),
            "mode": self.mode,
            "generator_version": "1.0.0",
            "environment_adapted": bool(self.env_data)
        }
        
        self.generated_config = adapted_config
        
        self._log_success("Configuration generated successfully")
        return adapted_config
    
    def save_configuration_files(self) -> List[str]:
        """Save all configuration files"""
        saved_files: List[str] = []
        
        if not self.generated_config:
            self._log_error("No configuration generated. Call generate_configuration() first.")
            return saved_files
        
        # Save main configuration JSON
        config_file = self.automation_dir / "current-config.json"
        with open(config_file, 'w') as f:
            json.dump(self.generated_config, f, indent=2)
        saved_files.append(str(config_file))
        self._log_info(f"Saved configuration to: {config_file}")
        
        # Save .env file
        env_file = self.project_dir / f".env.{self.mode}"
        env_content = self._generate_env_file(self.generated_config)
        with open(env_file, 'w') as f:
            f.write(env_content)
        saved_files.append(str(env_file))
        self._log_info(f"Saved environment file to: {env_file}")
        
        # Save docker-compose override
        override_file = self.project_dir / f"docker-compose.{self.mode}.override.yml"
        override_content = self._generate_docker_compose_override(self.generated_config)
        with open(override_file, 'w') as f:
            f.write(override_content)
        saved_files.append(str(override_file))
        self._log_info(f"Saved docker-compose override to: {override_file}")
        
        # Create symlink to default .env for development
        if self.mode == "dev":
            default_env = self.project_dir / ".env"
            if default_env.exists():
                default_env.unlink()
            default_env.symlink_to(env_file)
            saved_files.append(str(default_env))
            self._log_info(f"Created symlink: {default_env} -> {env_file}")
        
        return saved_files
    
    def print_summary(self):
        """Print configuration summary"""
        if not self.generated_config:
            self._log_error("No configuration generated")
            return
        
        config = self.generated_config
        print("\n" + "="*60)
        print("🎯 CONFIGURATION GENERATION SUMMARY")
        print("="*60)
        print(f"Mode: {self.mode.upper()}")
        print(f"Generated: {config['_metadata']['generated_at']}")
        print(f"Environment Adapted: {config['_metadata']['environment_adapted']}")
        print()
        
        print("📊 Key Configuration:")
        print(f"  • Database: {config['database']['host']}:{config['database']['port']}/{config['database']['name']}")
        print(f"  • Backend: {config['backend']['host']}:{config['backend']['port']}")
        print(f"  • Frontend: {config['frontend']['host']}:{config['frontend']['port']}")
        print(f"  • Redis: {config['redis']['host']}:{config['redis']['port']}")
        print(f"  • AI Model: {config['ai']['model']}")
        print(f"  • Workers: {config['backend']['workers']}")
        print(f"  • Monitoring: {'Enabled' if config['monitoring']['enabled'] else 'Disabled'}")
        print()
        
        print("🔒 Security:")
        print(f"  • Secret Key: {'✓ Generated' if config['security']['secret_key'] else '✗ Missing'}")
        print(f"  • JWT Secret: {'✓ Generated' if config['security']['jwt_secret'] else '✗ Missing'}")
        print(f"  • Algorithm: {config['security']['algorithm']}")
        print(f"  • SSL Verify: {config['security']['ssl_verify']}")
        print()
        
        if self.env_data:
            print("🌍 Environment Adaptations:")
            network_status = self.env_data.get("network", {}).get("status", "unknown")
            print(f"  • Network Status: {network_status}")
            
            memory_info = self.env_data.get("resources", {}).get("memory", {})
            if memory_info:
                print(f"  • Memory: {memory_info.get('total', 'Unknown')}")
            
            disk_info = self.env_data.get("resources", {}).get("disk", {})
            if disk_info:
                print(f"  • Disk: {disk_info.get('available', 'Unknown')} available")
            print()
        
        print("📁 Generated Files:")
        saved_files: List[str] = self.save_configuration_files()
        for file_path in saved_files:
            print(f"  • {file_path}")
        print()
        
        print("✅ Configuration generation completed successfully!")
        print("="*60)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Samoey Copilot Configuration Generator")
    parser.add_argument("--mode", choices=["dev", "staging", "prod"], default="dev",
                       help="Configuration mode (default: dev)")
    parser.add_argument("--project-dir", help="Project directory path")
    parser.add_argument("--output-dir", help="Output directory for configuration files")
    parser.add_argument("--summary", action="store_true", help="Print configuration summary")
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = ConfigGenerator(mode=args.mode, project_dir=args.project_dir)
        
        # Generate configuration
        config = generator.generate_configuration()
        
        # Save configuration files
        saved_files = generator.save_configuration_files()
        
        # Print summary if requested
        if args.summary:
            generator.print_summary()
        else:
            print(f"✅ Configuration generated successfully for mode: {args.mode}")
            print(f"📁 Saved {len(saved_files)} configuration files:")
            for file_path in saved_files:
                print(f"   • {file_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Configuration generation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
