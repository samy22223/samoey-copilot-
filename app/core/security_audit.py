import logging
import json
from datetime import datetime
from typing import Dict, Any
import asyncio
from logging.handlers import RotatingFileHandler
import os

class SecurityAuditLogger:
    def __init__(self, log_dir: str = "logs/security"):
        self.log_dir = log_dir
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up the logging configuration"""
        # Create logs directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configure main security log
        self.security_logger = logging.getLogger('security')
        self.security_logger.setLevel(logging.INFO)
        
        # Configure audit log
        self.audit_logger = logging.getLogger('security.audit')
        self.audit_logger.setLevel(logging.INFO)
        
        # Configure alert log
        self.alert_logger = logging.getLogger('security.alerts')
        self.alert_logger.setLevel(logging.INFO)
        
        # Set up handlers
        self._setup_handler('security.log', self.security_logger)
        self._setup_handler('audit.log', self.audit_logger)
        self._setup_handler('alerts.log', self.alert_logger)

    def _setup_handler(self, filename: str, logger: logging.Logger):
        """Set up a rotating file handler for a logger"""
        handler = RotatingFileHandler(
            os.path.join(self.log_dir, filename),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log a security event"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'details': details
        }
        self.security_logger.info(json.dumps(log_entry))

    def log_audit_event(self, 
                       user: str, 
                       action: str, 
                       resource: str, 
                       status: str, 
                       details: Dict[str, Any]):
        """Log an audit event"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user': user,
            'action': action,
            'resource': resource,
            'status': status,
            'details': details
        }
        self.audit_logger.info(json.dumps(log_entry))

    def log_security_alert(self, 
                         severity: str, 
                         alert_type: str, 
                         details: Dict[str, Any]):
        """Log a security alert"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            'type': alert_type,
            'details': details
        }
        self.alert_logger.info(json.dumps(log_entry))

    async def get_recent_logs(self, 
                            log_type: str = 'security', 
                            limit: int = 100) -> list:
        """Get recent log entries"""
        log_file = os.path.join(self.log_dir, f'{log_type}.log')
        entries = []
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        # Extract the JSON part of the log entry
                        json_str = line[line.index('{'):line.rindex('}')+1]
                        entry = json.loads(json_str)
                        entries.append(entry)
                    except:
                        continue
        except Exception as e:
            print(f"Error reading log file: {str(e)}")
        
        return entries

    async def cleanup_old_logs(self, days: int = 30):
        """Clean up old log files"""
        cutoff = datetime.utcnow().timestamp() - (days * 86400)
        
        for filename in os.listdir(self.log_dir):
            filepath = os.path.join(self.log_dir, filename)
            try:
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
            except Exception as e:
                print(f"Error cleaning up log file {filename}: {str(e)}")

# Create global instance
security_audit_logger = SecurityAuditLogger()
