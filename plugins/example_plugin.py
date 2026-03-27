# name: Example Plugin
# description: Template for creating custom data source plugins
# version: 0.1
#
# To activate: set {"plugins": {"example_plugin": {"enabled": true}}} in config.json

from _base import DataSourcePlugin

class ExamplePlugin(DataSourcePlugin):
    name = "Example Plugin"
    description = "A template showing the plugin interface"
    version = "0.1"

    def scan(self):
        # Return empty data — replace with your data source logic
        return {
            "models": {},
            "daily": {},
            "projects": {},
            "total_messages": 0,
            "total_sessions": 0,
            "total_tokens": 0,
        }

    def get_sessions(self):
        return []
