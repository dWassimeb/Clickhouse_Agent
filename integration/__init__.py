"""
Integration module for connecting Streamlit frontend with LangGraph backend
"""

from .agent_bridge import TelmiAgentBridge, telmi_bridge

__all__ = ['TelmiAgentBridge', 'telmi_bridge']