from pathlib import Path
import importlib.util
import sys
import os
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class Plugin:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path
        self.module = None
        self.enabled = False

class PluginManager:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, Plugin] = {}
        self._create_plugins_dir()

    def _create_plugins_dir(self):
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        (self.plugins_dir / "__init__.py").touch(exist_ok=True)

    def load_plugin(self, name: str):
        """Load a plugin by name."""
        plugin_path = self.plugins_dir / name
        if not (plugin_path / "__init__.py").exists():
            raise FileNotFoundError(f"Plugin {name} not found")

        spec = importlib.util.spec_from_file_location(
            f"pinnacle_plugins.{name}",
            plugin_path / "__init__.py"
        )
        if not spec or not spec.loader:
            raise ImportError(f"Could not load plugin {name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[f"pinnacle_plugins.{name}"] = module
        spec.loader.exec_module(module)
        
        self.plugins[name] = Plugin(name, str(plugin_path))
        self.plugins[name].module = module
        self.plugins[name].enabled = True
        return module

    def unload_plugin(self, name: str):
        """Unload a plugin."""
        if name in self.plugins:
            if hasattr(self.plugins[name].module, 'cleanup'):
                self.plugins[name].module.cleanup()
            del sys.modules[f"pinnacle_plugins.{name}"]
            del self.plugins[name]

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all available plugins."""
        return [{"name": name, "enabled": plugin.enabled} 
               for name, plugin in self.plugins.items()]
