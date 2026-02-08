"""
Metric Parser Utility

Parses unstructured metric strings into structured data for better visualization.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedMetric:
    """Structured representation of a metric."""
    original_text: str
    value: Optional[float] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    metric_type: Optional[str] = None  # 'volume', 'growth', 'percentage', 'count', 'time'
    trend: Optional[str] = None  # 'up', 'down', 'neutral'
    label: Optional[str] = None


class MetricParser:
    """Parses metric strings into structured data."""
    
    # Patterns for different metric types
    PATTERNS = {
        'growth_percentage': re.compile(r'([+-]?\d+\.?\d*)\s*%\s*growth', re.IGNORECASE),
        'percentage': re.compile(r'([+-]?\d+\.?\d*)\s*%'),
        'requests': re.compile(r'(\d+)\s*requests?'),
        'increase': re.compile(r'([+-]?\d+)\s*(?:requests?|items?|units?)?\s*(?:increase|decrease)', re.IGNORECASE),
        'count': re.compile(r'(\d+)\s*(?:requests?|items?|units?|cases?)'),
    }
    
    # Keywords for metric types
    TYPE_KEYWORDS = {
        'growth': ['growth', 'increase', 'decrease', 'change', 'trend'],
        'volume': ['requests', 'volume', 'total', 'count'],
        'percentage': ['%', 'percent', 'percentage'],
        'time': ['time', 'duration', 'hours', 'days', 'minutes'],
    }
    
    # Trend indicators
    TREND_KEYWORDS = {
        'up': ['increase', 'growth', 'up', 'rise', 'higher', '+'],
        'down': ['decrease', 'decline', 'down', 'fall', 'lower', '-'],
    }
    
    @classmethod
    def parse(cls, metric_string: str) -> ParsedMetric:
        """
        Parse a metric string into structured data.
        
        Args:
            metric_string: Raw metric string like "663 requests" or "73.1% growth"
            
        Returns:
            ParsedMetric object with extracted information
        """
        metric_string = metric_string.strip()
        parsed = ParsedMetric(original_text=metric_string)
        
        # Extract value and unit
        value, unit = cls._extract_value_and_unit(metric_string)
        parsed.value = value
        parsed.unit = unit
        
        # Determine metric type
        parsed.metric_type = cls._determine_type(metric_string)
        
        # Extract category (if mentioned)
        parsed.category = cls._extract_category(metric_string)
        
        # Determine trend
        parsed.trend = cls._determine_trend(metric_string)
        
        # Generate label
        parsed.label = cls._generate_label(metric_string, parsed)
        
        return parsed
    
    @classmethod
    def _extract_value_and_unit(cls, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Extract numeric value and unit from text."""
        # Try percentage first
        percent_match = cls.PATTERNS['percentage'].search(text)
        if percent_match:
            value = float(percent_match.group(1))
            return value, '%'
        
        # Try growth percentage
        growth_match = cls.PATTERNS['growth_percentage'].search(text)
        if growth_match:
            value = float(growth_match.group(1))
            return value, '%'
        
        # Try requests/count
        requests_match = cls.PATTERNS['requests'].search(text)
        if requests_match:
            value = float(requests_match.group(1))
            return value, 'requests'
        
        # Try increase/decrease
        increase_match = cls.PATTERNS['increase'].search(text)
        if increase_match:
            value = float(increase_match.group(1))
            unit = 'requests' if 'request' in text.lower() else 'units'
            return value, unit
        
        # Try generic count
        count_match = cls.PATTERNS['count'].search(text)
        if count_match:
            value = float(count_match.group(1))
            return value, 'units'
        
        # Try to find any number
        number_match = re.search(r'([+-]?\d+\.?\d*)', text)
        if number_match:
            value = float(number_match.group(1))
            return value, None
        
        return None, None
    
    @classmethod
    def _determine_type(cls, text: str) -> str:
        """Determine the type of metric."""
        text_lower = text.lower()
        
        for metric_type, keywords in cls.TYPE_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return metric_type
        
        return 'unknown'
    
    @classmethod
    def _extract_category(cls, text: str) -> Optional[str]:
        """Extract category name from metric text."""
        # Common category patterns
        # Look for "in [Category]" or "[Category] with"
        patterns = [
            r'in\s+([A-Z][a-zA-Z\s&,]+?)(?:\s|$|,|\.)',
            r'([A-Z][a-zA-Z\s&,]+?)\s+(?:with|shows|has|is)',
            r'([A-Z][a-zA-Z\s&,]+?)\s+(?:requests?|growth|increase)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                category = match.group(1).strip()
                # Clean up common words
                category = re.sub(r'\s+(with|shows|has|is|requests?|growth|increase)', '', category, flags=re.IGNORECASE)
                if len(category) > 3:  # Filter out short matches
                    return category
        
        return None
    
    @classmethod
    def _determine_trend(cls, text: str) -> Optional[str]:
        """Determine trend direction."""
        text_lower = text.lower()
        
        for trend, keywords in cls.TREND_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return trend
        
        # Check for explicit + or - signs
        if '+' in text or re.search(r'\+\d', text):
            return 'up'
        if '-' in text and not text.startswith('-'):
            return 'down'
        
        return None
    
    @classmethod
    def _generate_label(cls, text: str, parsed: ParsedMetric) -> str:
        """Generate a human-readable label for the metric."""
        if parsed.metric_type == 'growth':
            return f"{parsed.value:+.1f}% Growth" if parsed.value else "Growth Rate"
        elif parsed.metric_type == 'volume':
            return f"{int(parsed.value)} {parsed.unit or 'Items'}" if parsed.value else "Volume"
        elif parsed.metric_type == 'percentage':
            return f"{parsed.value:.1f}%" if parsed.value else "Percentage"
        else:
            # Try to create a label from the original text
            # Remove numbers and common words, capitalize
            label = re.sub(r'\d+\.?\d*\s*%?', '', text)
            label = re.sub(r'\b(in|with|shows|has|is|requests?|growth|increase|decrease)\b', '', label, flags=re.IGNORECASE)
            label = label.strip().title()
            return label if label else "Metric"
    
    @classmethod
    def parse_all(cls, metrics: List[str]) -> List[ParsedMetric]:
        """Parse a list of metric strings."""
        return [cls.parse(metric) for metric in metrics]
    
    @classmethod
    def group_by_type(cls, parsed_metrics: List[ParsedMetric]) -> Dict[str, List[ParsedMetric]]:
        """Group parsed metrics by their type."""
        grouped = {}
        for metric in parsed_metrics:
            metric_type = metric.metric_type or 'unknown'
            if metric_type not in grouped:
                grouped[metric_type] = []
            grouped[metric_type].append(metric)
        return grouped
    
    @classmethod
    def group_by_category(cls, parsed_metrics: List[ParsedMetric]) -> Dict[str, List[ParsedMetric]]:
        """Group parsed metrics by category."""
        grouped = {}
        for metric in parsed_metrics:
            category = metric.category or 'Other'
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(metric)
        return grouped
