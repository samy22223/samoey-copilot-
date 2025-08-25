import asyncio
import json
import os
import subprocess
import socket
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from app.core.redis import redis_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SelfHostingService:
    """
    Self-Hosting Service for zero-configuration service management.
    Automatically manages all services without manual intervention.
    """

    def __init__(self):
        self.services = {}
        self.service_processes = {}
        self.service_ports = {}
        self.service_configs = {}
        self.is_initialized = False

    async def initialize_self_hosting(self) -> Dict[str, Any]:
        """
        Initialize self-hosting services with zero configuration.
        """
        try:
            logger.info("Starting self-hosting service initialization...")

            initialization_results = {}

            # Step 1: Detect available ports
            initialization_results["port_detection"] = await self._detect_available_ports()

            # Step 2: Setup service configurations
            initialization_results["service_configs"] = await self._setup_service_configurations()

            # Step 3: Start core services
            initialization_results["core_services"] = await self._start_core_services()

            # Step 4: Setup service discovery
            initialization_results["service_discovery"] = await self._setup_service_discovery()

            # Step 5: Configure auto-scaling
            initialization_results["auto_scaling"] = await self._configure_auto_scaling()

            # Step 6: Setup health monitoring
            initialization_results["health_monitoring"] = await self._setup_health_monitoring()

            # Step 7: Configure load balancing
            initialization_results["load_balancing"] = await self._configure_load_balancing()

            self.is_initialized = True

            logger.info("Self-hosting services initialized successfully!")

            return {
                "success": True,
                "message": "Self-hosting services initialized successfully",
                "results": initialization_results,
                "services_running": len(self.service_processes),
                "service_ports": self.service_ports,
                "system_ready": True
            }

        except Exception as e:
            logger.error(f"Error initializing self-hosting services: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to initialize self-hosting services"
            }

    async def start_service(self, service_name: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start a specific service with auto-configuration.
        """
        try:
            if service_name in self.service_processes:
                return {"success": False, "error": "Service already running"}

            # Get service configuration
            service_config = config or self._get_default_service_config(service_name)

            # Find available port
            port = self._find_available_port_for_service(service_name)

            # Start service process
            process = await self._start_service_process(service_name, service_config, port)

            # Store service information
            self.service_processes[service_name] = process
            self.service_ports[service_name] = port
            self.service_configs[service_name] = service_config

            # Update service status
            await self._update_service_status(service_name, "running", port)

            logger.info(f"Started service {service_name} on port {port}")

            return {
                "success": True,
                "service_name": service_name,
                "port": port,
                "process_id": process.pid,
                "message": f"Service {service_name} started successfully"
            }

        except Exception as e:
            logger.error(f"Error starting service {service_name}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def stop_service(self, service_name: str) -> Dict[str, Any]:
        """
        Stop a specific service.
        """
        try:
            if service_name not in self.service_processes:
                return {"success": False, "error": "Service not running"}

            process = self.service_processes[service_name]

            # Graceful shutdown
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()

            # Remove from tracking
            del self.service_processes[service_name]
            del self.service_ports[service_name]
            del self.service_configs[service_name]

            # Update service status
            await self._update_service_status(service_name, "stopped", None)

            logger.info(f"Stopped service {service_name}")

            return {
                "success": True,
                "service_name": service_name,
                "message": f"Service {service_name} stopped successfully"
            }

        except Exception as e:
            logger.error(f"Error stopping service {service_name}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """
        Restart a specific service.
        """
        try:
            # Stop service if running
            if service_name in self.service_processes:
                await self.stop_service(service_name)

            # Start service again
            result = await self.start_service(service_name)

            return result

        except Exception as e:
            logger.error(f"Error restarting service {service_name}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get status of a specific service.
        """
        try:
            # Check if service is running
            is_running = service_name in self.service_processes
            process = self.service_processes.get(service_name)

            if is_running and process:
                is_alive = process.poll() is None
                if not is_alive:
                    # Process died, clean up
                    del self.service_processes[service_name]
                    is_running = False
            else:
                is_alive = False

            # Get service information
            service_info = {
                "service_name": service_name,
                "running": is_running and is_alive,
                "port": self.service_ports.get(service_name),
                "process_id": process.pid if process else None,
                "config": self.service_configs.get(service_name),
                "last_checked": datetime.now().isoformat()
            }

            return {
                "success": True,
                "service_info": service_info
            }

        except Exception as e:
            logger.error(f"Error getting service status for {service_name}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def list_all_services(self) -> Dict[str, Any]:
        """
        List all services and their status.
        """
        try:
            services_status = {}

            # Check all known services
            all_services = list(self.service_processes.keys()) + ["api_server", "database", "redis", "ai_service"]

            for service_name in set(all_services):
                status = await self.get_service_status(service_name)
                services_status[service_name] = status

            return {
                "success": True,
                "services": services_status,
                "total_services": len(services_status),
                "running_services": len([s for s in services_status.values() if s.get("service_info", {}).get("running", False)]),
                "total_ports_used": len([p for p in self.service_ports.values() if p])
            }

        except Exception as e:
            logger.error(f"Error listing all services: {str(e)}")
            return {"success": False, "error": str(e)}

    async def auto_scale_services(self) -> Dict[str, Any]:
        """
        Auto-scale services based on system resources and demand.
        """
        try:
            scaling_results = {}

            # Get system resources
            system_resources = self._get_system_resources()

            # Check each service for scaling needs
            for service_name, process in self.service_processes.items():
                scaling_decision = await self._should_scale_service(service_name, system_resources)

                if scaling_decision["should_scale"]:
                    if scaling_decision["scale_direction"] == "up":
                        result = await self._scale_up_service(service_name)
                    else:
                        result = await self._scale_down_service(service_name)

                    scaling_results[service_name] = result

            return {
                "success": True,
                "scaling_results": scaling_results,
                "message": "Auto-scaling completed"
            }

        except Exception as e:
            logger.error(f"Error in auto-scaling services: {str(e)}")
            return {"success": False, "error": str(e)}

    async def heal_services(self) -> Dict[str, Any]:
        """
        Auto-heal services that are not running properly.
        """
        try:
            healing_results = {}

            # Check all services
            for service_name in list(self.service_processes.keys()):
                status = await self.get_service_status(service_name)
                service_info = status.get("service_info", {})

                # If service should be running but isn't
                if not service_info.get("running", False):
                    logger.info(f"Detected unhealthy service: {service_name}")

                    # Try to restart the service
                    restart_result = await self.restart_service(service_name)
                    healing_results[service_name] = restart_result

            return {
                "success": True,
                "healing_results": healing_results,
                "services_healed": len([r for r in healing_results.values() if r.get("success", False)]),
                "message": "Service healing completed"
            }

        except Exception as e:
            logger.error(f"Error healing services: {str(e)}")
            return {"success": False, "error": str(e)}

    # Private helper methods

    async def _detect_available_ports(self) -> Dict[str, Any]:
        """Detect available ports for services."""
        try:
            port_ranges = {
                "api_server": (8000, 8100),
                "database": (5432, 5442),
                "redis": (6379, 6389),
                "ai_service": (8001, 8010),
                "monitoring": (9090, 9100),
                "load_balancer": (8080, 8090)
            }

            available_ports = {}

            for service_name, (start_port, end_port) in port_ranges.items():
                port = self._find_available_port(start_port, end_port)
                available_ports[service_name] = port

            return {"success": True, "available_ports": available_ports}

        except Exception as e:
            logger.error(f"Error detecting available ports: {str(e)}")
            return {"success": False, "error": str(e)}

    def _find_available_port(self, start_port: int, end_port: int) -> int:
        """Find an available port in the given range."""
        for port in range(start_port, end_port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('', port))
                sock.close()
                return port
            except OSError:
                continue
        return start_port  # Fallback to start port

    async def _setup_service_configurations(self) -> Dict[str, Any]:
        """Setup default service configurations."""
        try:
            default_configs = {
                "api_server": {
                    "workers": 1,
                    "max_memory_mb": 512,
                    "timeout": 30,
                    "auto_restart": True
                },
                "database": {
                    "max_connections": 100,
                    "shared_buffers": "128MB",
                    "effective_cache_size": "256MB"
                },
                "redis": {
                    "maxmemory": "256MB",
                    "maxmemory_policy": "allkeys-lru",
                    "timeout": 0
                },
                "ai_service": {
                    "workers": 1,
                    "max_memory_mb": 2048,
                    "model_cache_size": 5,
                    "timeout": 60
                }
            }

            # Store configurations
            for service_name, config in default_configs.items():
                self.service_configs[service_name] = config

            return {"success": True, "configurations_setup": True}

        except Exception as e:
            logger.error(f"Error setting up service configurations: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _start_core_services(self) -> Dict[str, Any]:
        """Start core services."""
        try:
            core_services = ["api_server", "database",
