# CCDash Plugin Base Class
# All custom plugins should inherit from DataSourcePlugin

class DataSourcePlugin:
    """Base class for CCDash data source plugins.

    To create a custom plugin:
    1. Create a .py file in the plugins/ directory
    2. Add metadata comments at the top:
       # name: My Plugin
       # description: What it does
       # version: 1.0
    3. Define a class that inherits from DataSourcePlugin
    4. Implement the required methods

    Example:
        class MyPlugin(DataSourcePlugin):
            name = "My Plugin"
            def scan(self):
                return {"models": {}, "daily": {}, "projects": {}}
            def get_sessions(self):
                return []
    """

    name: str = "Unnamed Plugin"
    description: str = ""
    version: str = "0.1"

    def scan(self) -> dict:
        """Scan data source and return aggregated data.
        Should return a dict compatible with _scan_all_projects() format:
        {
            "models": {model_name: {"input": int, "output": int, "cache_read": int, "cache_create": int, "calls": int}},
            "daily": {date_str: {"messages": int, "sessions": int, "tools": int, "tokens": {model: {...}}}},
            "projects": {name: {"messages": int, "tokens_total": int, "sessions": int, "friendly_name": str}},
            "total_messages": int,
            "total_sessions": int,
            "total_tokens": int,
        }
        """
        return {}

    def get_sessions(self) -> list:
        """Return a list of session dicts for /api/sessions.
        Each dict: {"sessionId": str, "timestamp": int, "project": str, "projectShort": str, "firstPrompt": str, "source": str}
        """
        return []

    def get_session_detail(self, session_id: str) -> dict:
        """Return session detail for /api/session-detail. Optional."""
        return {}
