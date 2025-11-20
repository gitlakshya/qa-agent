"""
TestRail Integration Module
Handles all TestRail API interactions and data mapping.
"""

from .testrail_client import TestRailClient
from .testrail_mapper import TestRailMapper
from .testrail_config import TestRailConfig

__all__ = ['TestRailClient', 'TestRailMapper', 'TestRailConfig']
