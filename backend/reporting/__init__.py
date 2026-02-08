"""
Report generation module for CRM Analytics.
"""

from .report_generator import ReportGenerator, generate_report_from_json
from .metric_parser import MetricParser, ParsedMetric

__all__ = ['ReportGenerator', 'generate_report_from_json', 'MetricParser', 'ParsedMetric']
