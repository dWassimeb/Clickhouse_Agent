"""
Simple Session-Based Token Tracker - No need to pass shared LLM everywhere
This approach uses a global session tracker that any CustomGPT can write to
"""

import json
import csv
import os
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

class GlobalTokenTracker:
    """Global token tracker that any CustomGPT instance can use."""

    def __init__(self):
        self.current_session = None
        self.session_data = {}
        self.lock = threading.Lock()
        self.export_dir = "token_usage_reports"
        os.makedirs(self.export_dir, exist_ok=True)

    def start_session(self, user_question: str, username: str = "unknown"):
        """Start a new tracking session."""
        with self.lock:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_session = session_id
            self.session_data[session_id] = {
                "user_question": user_question,
                "username": username,
                "start_time": datetime.now(),
                "calls": [],
                "total_tokens": 0,
                "total_calls": 0
            }
            print(f"🚀 Started token tracking session: {session_id} for question: {user_question[:50]}...")

    def log_call(self, prompt: str, response_data: Dict[str, Any], tool_context: str, call_duration: float):
        """Log an LLM call to the current session."""
        if not self.current_session:
            return  # No active session

        with self.lock:
            session_data = self.session_data.get(self.current_session)
            if not session_data:
                return

            # Extract token usage
            usage = response_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # Create call record
            call_record = {
                "call_number": len(session_data["calls"]) + 1,
                "timestamp": datetime.now().isoformat(),
                "tool_context": tool_context,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "call_duration_seconds": call_duration,
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "response_preview": response_data["choices"][0]["message"]["content"][:200] + "..."
                                  if len(response_data["choices"][0]["message"]["content"]) > 200
                                  else response_data["choices"][0]["message"]["content"]
            }

            # Update session data
            session_data["calls"].append(call_record)
            session_data["total_tokens"] += total_tokens
            session_data["total_calls"] += 1

            print(f"🔥 LLM Call #{call_record['call_number']}: {total_tokens} tokens (prompt: {prompt_tokens}, completion: {completion_tokens}) - Tool: {tool_context}")

    def export_session(self) -> Optional[str]:
        """Export current session to CSV."""
        if not self.current_session:
            return None

        with self.lock:
            session_data = self.session_data.get(self.current_session)
            if not session_data:
                return None

            # Prepare CSV data
            csv_data = []

            # Session summary
            end_time = datetime.now()
            total_duration = (end_time - session_data["start_time"]).total_seconds()

            session_summary = {
                "call_number": "SESSION_SUMMARY",
                "timestamp": session_data["start_time"].isoformat(),
                "tool_context": "TOTAL_SESSION",
                "prompt_tokens": sum(call["prompt_tokens"] for call in session_data["calls"]),
                "completion_tokens": sum(call["completion_tokens"] for call in session_data["calls"]),
                "total_tokens": session_data["total_tokens"],
                "call_duration_seconds": total_duration,
                "prompt_preview": session_data["user_question"],
                "response_preview": f"Session completed with {session_data['total_calls']} LLM calls",
                "username": session_data["username"],
                "estimated_cost_usd": round((session_data["total_tokens"] / 1000) * 0.005, 4)
            }
            csv_data.append(session_summary)

            # Separator
            separator = {key: "---" for key in session_summary.keys()}
            csv_data.append(separator)

            # Individual calls
            for call in session_data["calls"]:
                call_with_meta = call.copy()
                call_with_meta["username"] = session_data["username"]
                call_with_meta["estimated_cost_usd"] = round((call["total_tokens"] / 1000) * 0.005, 4)
                csv_data.append(call_with_meta)

            # Write CSV
            filename = f"token_usage_{self.current_session}.csv"
            filepath = os.path.join(self.export_dir, filename)

            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    if csv_data:
                        fieldnames = csv_data[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(csv_data)

                print(f"📊 Token usage exported to: {filepath}")
                print(f"📊 Session Summary: {session_data['total_tokens']} tokens, {session_data['total_calls']} calls, ${round((session_data['total_tokens'] / 1000) * 0.005, 4)} estimated cost")

                return filepath

            except Exception as e:
                print(f"Failed to export CSV: {e}")
                return None

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session."""
        if not self.current_session:
            return {"error": "No active session"}

        with self.lock:
            session_data = self.session_data.get(self.current_session)
            if not session_data:
                return {"error": "Session not found"}

            return {
                "session_id": self.current_session,
                "question": session_data["user_question"],
                "username": session_data["username"],
                "total_calls": session_data["total_calls"],
                "total_tokens": session_data["total_tokens"],
                "session_duration_seconds": (datetime.now() - session_data["start_time"]).total_seconds(),
                "estimated_cost_usd": round((session_data["total_tokens"] / 1000) * 0.005, 4),
                "calls_breakdown": [
                    {"tool": call["tool_context"], "tokens": call["total_tokens"]}
                    for call in session_data["calls"]
                ]
            }

# Global instance
global_token_tracker = GlobalTokenTracker()