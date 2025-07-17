"""
Custom LLM implementation with Global Token Tracking - Fixed Import
"""

import json
import urllib.request
from langchain.llms.base import LLM
from datetime import datetime
import sys
import os

GPT_API_KEY = "2b24fef721d14c94a333ab2e4f686f40"

# Global tracker instance (initialized on first access)
_global_tracker = None

def get_global_tracker():
    """Get the global token tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        try:
            # Try importing from the same directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            # Add paths to ensure import works
            for path in [current_dir, project_root]:
                if path not in sys.path:
                    sys.path.insert(0, path)

            from llm.global_token_tracker import global_token_tracker
            _global_tracker = global_token_tracker
            print("✅ Global token tracker loaded successfully")
        except ImportError as e:
            print(f"⚠️ Could not import global token tracker: {e}")
            # Create a dummy tracker that does nothing
            class DummyTracker:
                def start_session(self, *args, **kwargs):
                    print("⚠️ DummyTracker: start_session called but tracker not available")
                def log_call(self, *args, **kwargs):
                    print("⚠️ DummyTracker: log_call called but tracker not available")
                def export_session(self):
                    print("⚠️ DummyTracker: export_session called but tracker not available")
                    return None
                def get_session_summary(self):
                    return {"error": "Tracker not available"}
            _global_tracker = DummyTracker()

    return _global_tracker

class CustomGPT(LLM):
    """Custom GPT with global token tracking."""

    def _call(self, prompt: str, model="gpt-4o", version="2024-02-01", **kwargs):
        url = f"https://apigatewayinnovation.azure-api.net/openai-api/deployments/{model}/chat/completions?api-version={version}"
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": GPT_API_KEY,
        }
        data = {
            "messages": [
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt},
            ],
            "stop": ["\nThought:", "\nObservation:"],
        }

        call_start_time = datetime.now()

        try:
            request = urllib.request.Request(
                url, headers=headers, data=json.dumps(data).encode("utf-8")
            )
            request.get_method = lambda: "POST"
            response = urllib.request.urlopen(request)
            response_data = json.loads(response.read())

            call_end_time = datetime.now()
            call_duration = (call_end_time - call_start_time).total_seconds()

            # 🔥 LOG TO GLOBAL TOKEN TRACKER
            tool_context = self._identify_tool_context(prompt)
            tracker = get_global_tracker()
            tracker.log_call(prompt, response_data, tool_context, call_duration)

            return response_data["choices"][0]["message"]["content"]

        except Exception as e:
            call_end_time = datetime.now()
            call_duration = (call_end_time - call_start_time).total_seconds()

            # 🔥 LOG ERROR TO GLOBAL TOKEN TRACKER
            error_response = {
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "choices": [{"message": {"content": f"ERROR: {str(e)}"}}]
            }
            tracker = get_global_tracker()
            tracker.log_call(prompt, error_response, "ERROR", call_duration)

            return f"Erreur lors de l'appel à l'API : {e}"

    def _identify_tool_context(self, prompt: str) -> str:
        """Identify the tool/context based on prompt content."""
        prompt_lower = prompt.lower()

        if "analyze this database query" in prompt_lower or "intent" in prompt_lower:
            return "Intent_Analyzer"
        elif "generate clickhouse sql" in prompt_lower or "sql" in prompt_lower or "select" in prompt_lower:
            return "SQL_Generator"
        elif "analyze this schema" in prompt_lower or "schema" in prompt_lower or "table" in prompt_lower:
            return "Schema_Tool"
        elif "visualization" in prompt_lower or "chart" in prompt_lower:
            return "Visualization_Tool"
        elif "router" in prompt_lower or "classify" in prompt_lower or "query_type" in prompt_lower:
            return "Smart_Router"
        elif "format" in prompt_lower or "response" in prompt_lower:
            return "Response_Formatter"
        else:
            return "Unknown_Tool"

    @property
    def _llm_type(self) -> str:
        return "customGPT"