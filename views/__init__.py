"""
Views Package - Modular view components for the Transportation System
"""
import logging

from .overview_view import OverviewView

try:
    from .analytics_view import AnalyticsView
except Exception as e:
    logging.warning(f"AnalyticsView not available: {e}")
    AnalyticsView = None

try:
    from .active_routes_view import ActiveRoutesView
except Exception as e:
    logging.warning(f"ActiveRoutesView not available: {e}")
    ActiveRoutesView = None

try:
    from .new_routes_view import NewRoutesView
except Exception as e:
    logging.warning(f"NewRoutesView not available: {e}")
    NewRoutesView = None

try:
    from .map_visualizer_view import MapVisualizerView
except Exception as e:
    logging.warning(f"MapVisualizerView not available: {e}")
    MapVisualizerView = None

# Build only available views
VIEW_CLASSES = {
    k: v for k, v in {
        "Overview": OverviewView,
        "Analytics": AnalyticsView,
        "Active Routes": ActiveRoutesView,
        "New Routes": NewRoutesView,
        "Map Visualizer": MapVisualizerView
    }.items() if v is not None
}

__all__ = [
    'OverviewView',
    'AnalyticsView',
    'ActiveRoutesView',
    'NewRoutesView',
    'MapVisualizerView',
    'VIEW_CLASSES'
]