"""
Professional Report Generator for CRM Analytics

Converts JSON analytics output into PDF reports.
"""

from datetime import datetime
from typing import Dict, List, Optional
from io import BytesIO
import re
import os
from pathlib import Path

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from .metric_parser import MetricParser
except ImportError:
    from metric_parser import MetricParser

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Flowable
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.lib.units import inch
    from reportlab.graphics.shapes import Drawing, Rect, Line, Group
    from reportlab.graphics import renderPDF
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class MetricCardFlowable(Flowable):
    """Custom flowable for creating professional metric cards with visual indicators."""
    
    def __init__(self, category: str, growth_value: Optional[float], volume_value: Optional[float], 
                 width=400, height=50, max_volume=1000):
        """
        Create a metric card with category, growth, and volume.
        
        Args:
            category: Category name
            growth_value: Growth rate percentage (can be None)
            volume_value: Volume count (can be None)
            width: Width of the card
            height: Height of the card
            max_volume: Maximum volume for scaling progress bars
        """
        Flowable.__init__(self)
        self.category = category
        self.growth_value = growth_value
        self.volume_value = volume_value
        self.width = width
        self.height = height
        self.max_volume = max_volume
    
    def draw(self):
        canvas = self.canv
        
        # Card background (subtle)
        canvas.setFillColor(HexColor('#fafafa'))
        canvas.setStrokeColor(HexColor('#e5e7eb'))
        canvas.setLineWidth(0.5)
        canvas.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=1)
        
        # Category name
        canvas.setFont("Times-Bold", 10)
        canvas.setFillColor(HexColor('#111827'))
        category_text = self.category[:35] if len(self.category) > 35 else self.category
        canvas.drawString(12, self.height - 18, category_text)
        
        y_pos = self.height - 32
        
        # Growth indicator with visual bar
        if self.growth_value is not None:
            # Determine color based on growth
            if self.growth_value > 0:
                growth_color = HexColor('#10b981')  # Green for positive
                trend_symbol = "↑"
            elif self.growth_value < 0:
                growth_color = HexColor('#ef4444')  # Red for negative
                trend_symbol = "↓"
            else:
                growth_color = HexColor('#6b7280')  # Gray for neutral
                trend_symbol = "→"
            
            # Format growth value
            growth_text = f"{trend_symbol} {abs(self.growth_value):.1f}%"
            
            # Draw small colored indicator dot
            canvas.setFillColor(growth_color)
            canvas.circle(12, y_pos + 4, 3, fill=1, stroke=0)
            
            # Draw growth text
            canvas.setFont("Times-Roman", 9)
            canvas.setFillColor(HexColor('#374151'))
            canvas.drawString(20, y_pos, f"Growth: {growth_text}")
            
            # Draw small progress bar
            bar_width = min(abs(self.growth_value) / 100 * 80, 80)  # Scale to max 100%
            bar_x = self.width - 120
            bar_y = y_pos + 2
            bar_height = 6
            
            # Background bar
            canvas.setFillColor(HexColor('#e5e7eb'))
            canvas.roundRect(bar_x, bar_y, 80, bar_height, 2, fill=1, stroke=0)
            
            # Colored bar
            canvas.setFillColor(growth_color)
            canvas.roundRect(bar_x, bar_y, bar_width, bar_height, 2, fill=1, stroke=0)
            
            y_pos -= 14
        
        # Volume indicator
        if self.volume_value is not None:
            # Draw small indicator dot (blue for volume)
            canvas.setFillColor(HexColor('#3b82f6'))
            canvas.circle(12, y_pos + 4, 3, fill=1, stroke=0)
            
            # Draw volume text
            canvas.setFont("Times-Roman", 9)
            canvas.setFillColor(HexColor('#374151'))
            volume_text = f"{self.volume_value:,.0f} requests" if self.volume_value >= 1000 else f"{int(self.volume_value)} requests"
            canvas.drawString(20, y_pos, f"Volume: {volume_text}")
            
            # Draw small progress bar for volume (relative scale)
            bar_x = self.width - 120
            bar_y = y_pos + 2
            bar_height = 6
            
            # Scale volume bar relative to max volume
            if self.max_volume > 0:
                bar_width = min(self.volume_value / self.max_volume * 80, 80)
            else:
                bar_width = 0
            
            # Background bar
            canvas.setFillColor(HexColor('#e5e7eb'))
            canvas.roundRect(bar_x, bar_y, 80, bar_height, 2, fill=1, stroke=0)
            
            # Colored bar
            canvas.setFillColor(HexColor('#3b82f6'))
            canvas.roundRect(bar_x, bar_y, bar_width, bar_height, 2, fill=1, stroke=0)


class DualBarChartFlowable(Flowable):
    """Custom flowable for creating dual horizontal bar charts showing original value and percent increase."""
    
    def __init__(self, label, original_value, percent_increase, max_original_value, max_percent_increase=100, width=400, height=50):
        Flowable.__init__(self)
        self.label = label
        self.original_value = original_value
        self.percent_increase = percent_increase
        self.max_original_value = max_original_value
        self.max_percent_increase = max_percent_increase
        self.width = width
        self.height = height
    
    def draw(self):
        canvas = self.canv
        
        # Calculate the new value after increase
        # If percent_increase is 50%, new_value = original_value * 1.5
        new_value = None
        if self.original_value is not None and self.percent_increase is not None:
            # Calculate new value: original * (1 + percent_increase/100)
            new_value = self.original_value * (1 + self.percent_increase / 100)
        
        # Draw label - Times New Roman, smaller font
        canvas.setFont("Times-Roman", 9)
        canvas.setFillColor(HexColor('#111827'))
        label_text = self.label[:35] if len(self.label) > 35 else self.label
        canvas.drawString(0, self.height - 10, label_text)
        
        # Bar dimensions - adjusted for better spacing
        bar_start_x = 110  # Moved right to make room for labels
        bar_y_original = self.height - 26
        bar_y_increase = self.height - 40
        bar_height = 8
        bar_max_width = self.width - 180  # More space for labels
        
        # Calculate max value for scaling (use max of original values and new values)
        max_value_for_scaling = self.max_original_value
        if new_value is not None and self.original_value is not None:
            # Update max to include new values if they're larger
            max_value_for_scaling = max(self.max_original_value, abs(new_value))
        
        # Calculate bar widths - both scaled to max_value_for_scaling for comparison
        if max_value_for_scaling > 0 and self.original_value is not None:
            original_bar_width = (abs(self.original_value) / max_value_for_scaling) * bar_max_width
            original_bar_width = min(original_bar_width, bar_max_width)
        else:
            original_bar_width = 0
        
        # Calculate increase bar width based on NEW VALUE (not just increase amount)
        # This way a 50% increase shows as 1.5x the original bar, not 0.5x
        if new_value is not None and max_value_for_scaling > 0:
            increase_bar_width = (abs(new_value) / max_value_for_scaling) * bar_max_width
            increase_bar_width = min(increase_bar_width, bar_max_width)
        else:
            increase_bar_width = 0
        
        # Draw original value bar
        canvas.setFont("Times-Roman", 7)
        canvas.setFillColor(HexColor('#6b7280'))
        canvas.drawString(0, bar_y_original + 1, "Original:")
        
        # Original bar background
        canvas.setFillColor(HexColor('#e5e7eb'))
        canvas.rect(bar_start_x, bar_y_original, bar_max_width, bar_height, fill=1, stroke=0)
        
        # Original bar (blue)
        if original_bar_width > 0:
            canvas.setFillColor(HexColor('#3b82f6'))
            canvas.rect(bar_start_x, bar_y_original, original_bar_width, bar_height, fill=1, stroke=0)
        
        # Original value text - positioned after the bar to avoid intersection
        if self.original_value is not None:
            original_text = f"{int(self.original_value):,} requests"
            canvas.setFont("Times-Roman", 7)
            canvas.setFillColor(HexColor('#1f2937'))
            # Position text after the bar with some padding
            text_x = bar_start_x + bar_max_width + 8
            # If bar is too long, position text at the end of the bar
            if original_bar_width > bar_max_width - 50:
                text_x = bar_start_x + original_bar_width + 8
            canvas.drawString(text_x, bar_y_original + 1, original_text)
        
        # Draw new value bar (after increase)
        canvas.setFont("Times-Roman", 7)
        canvas.setFillColor(HexColor('#6b7280'))
        canvas.drawString(0, bar_y_increase + 1, "After Increase:")
        
        # Increase bar background
        canvas.setFillColor(HexColor('#e5e7eb'))
        canvas.rect(bar_start_x, bar_y_increase, bar_max_width, bar_height, fill=1, stroke=0)
        
        # Increase bar (green for positive, red for negative)
        if increase_bar_width > 0:
            if self.percent_increase and self.percent_increase > 0:
                increase_color = HexColor('#10b981')  # Green
            elif self.percent_increase and self.percent_increase < 0:
                increase_color = HexColor('#ef4444')  # Red
            else:
                increase_color = HexColor('#6b7280')  # Gray
            
            canvas.setFillColor(increase_color)
            canvas.rect(bar_start_x, bar_y_increase, increase_bar_width, bar_height, fill=1, stroke=0)
        
        # Show new value and percent increase text - positioned after the bar
        if self.percent_increase is not None and new_value is not None:
            increase_text = f"{int(new_value):,} requests ({self.percent_increase:+.1f}%)"
            canvas.setFont("Times-Roman", 7)
            canvas.setFillColor(HexColor('#1f2937'))
            # Position text after the bar with some padding
            text_x = bar_start_x + bar_max_width + 8
            # If bar is too long, position text at the end of the bar
            if increase_bar_width > bar_max_width - 50:
                text_x = bar_start_x + increase_bar_width + 8
            canvas.drawString(text_x, bar_y_increase + 1, increase_text)
        
        # Draw borders
        canvas.setStrokeColor(HexColor('#d1d5db'))
        canvas.setLineWidth(0.5)
        canvas.rect(bar_start_x, bar_y_original, bar_max_width, bar_height, fill=0, stroke=1)
        canvas.rect(bar_start_x, bar_y_increase, bar_max_width, bar_height, fill=0, stroke=1)


class BorderedChartGroup(Flowable):
    """Flowable that draws a border around a group of charts."""
    
    def __init__(self, charts, width, padding=4):
        Flowable.__init__(self)
        self.charts = charts
        self.width = width
        self.padding = padding
    
    def wrap(self, *args):
        """Calculate total height needed for all charts."""
        total_height = self.padding * 2  # Top and bottom padding
        for item in self.charts:
            if hasattr(item, 'height'):
                total_height += item.height
            elif isinstance(item, Spacer):
                total_height += item.height
            else:
                total_height += 8  # Default for other items
        return (self.width, total_height)
    
    def draw(self):
        """Draw border rectangle."""
        canvas = self.canv
        
        # Draw border rectangle around entire chart area
        canvas.setStrokeColor(HexColor('#d1d5db'))
        canvas.setLineWidth(1)
        canvas.rect(0, 0, self.width, self.height, fill=0, stroke=1)


class HorizontalBarChartFlowable(Flowable):
    """Custom flowable for creating horizontal bar charts."""
    
    def __init__(self, label, value, max_value, width=400, height=30, color=HexColor('#3b82f6'), unit=None):
        Flowable.__init__(self)
        self.label = label
        self.value = value
        self.max_value = max_value
        self.width = width
        self.height = height
        self.color = color
        self.unit = unit
    
    def draw(self):
        canvas = self.canv
        
        # Format value text first to calculate its width
        if isinstance(self.value, (int, float)):
            if self.unit == '%':
                value_text = f"{self.value:+.1f}%"
            elif abs(self.value) < 1:
                value_text = f"{self.value:+.2f}"
            elif abs(self.value) < 100:
                value_text = f"{self.value:+.1f}"
            else:
                value_text = f"{self.value:,.0f}"
            if self.unit and self.unit != '%':
                value_text += f" {self.unit}"
        else:
            value_text = str(self.value)
            if self.unit:
                value_text += f" {self.unit}"
        
        # Calculate value text width
        canvas.setFont("Times-Bold", 9)
        value_width = canvas.stringWidth(value_text, "Times-Bold", 9)
        
        # Horizontal bar chart layout
        # Text area: 1/5 of page width on left
        text_area_width = self.width / 5.0
        bar_area_x = text_area_width + 5  # Start of bar area (small gap)
        # Reserve space for value text on the right
        value_area_width = value_width + 10  # Space for value text + padding
        bar_area_width = self.width - bar_area_x - value_area_width  # Remaining width for bars
        
        # Calculate bar width as percentage of max value
        if self.max_value > 0:
            bar_width = (abs(self.value) / self.max_value) * bar_area_width
        else:
            bar_width = 0
        
        # Bar dimensions
        bar_y = 4
        bar_height = self.height - 8
        bar_center_y = bar_y + (bar_height / 2)  # Center of the bar
        
        # Draw label on left (with text wrapping, right-aligned within text area)
        canvas.setFont("Times-Roman", 9)
        canvas.setFillColor(HexColor('#111827'))
        
        # Wrap text to fit in text area
        label_lines = self._wrap_text(self.label, text_area_width - 5, canvas, "Times-Roman", 9)
        # Center text vertically to align with bar center
        # Calculate total text height
        line_height = 11  # Height per line
        total_text_height = len(label_lines) * line_height
        
        # Calculate starting Y position so center of text aligns with bar center
        # Text center = label_start_y + (total_text_height / 2)
        # We want: text center = bar_center_y
        # So: label_start_y = bar_center_y - (total_text_height / 2)
        label_start_y = bar_center_y - (total_text_height / 2)
        
        for i, line in enumerate(label_lines):
            # Right-align text within text area
            line_width = canvas.stringWidth(line, "Times-Roman", 9)
            label_x = text_area_width - line_width - 2  # Right-align with small margin
            # Position each line - first line at bottom, subsequent lines above
            line_y = label_start_y + (len(label_lines) - i - 1) * line_height
            canvas.drawString(label_x, line_y, line)
        
        # Draw bar (horizontal, going right)
        bar_x = bar_area_x
        if bar_width > 0:
            canvas.setFillColor(self.color)
            canvas.rect(bar_x, bar_y, bar_width, bar_height, fill=1, stroke=0)
        
        # Draw value label on the right side of bar (always after bar, right-aligned)
        canvas.setFont("Times-Bold", 9)
        canvas.setFillColor(HexColor('#1f2937'))
        
        # Position value text on the right side
        value_x = bar_x + bar_width + 5  # Always after bar with small gap
        # Ensure value doesn't go beyond page
        if value_x + value_width > self.width - 5:
            # If it would overflow, reduce bar width to make room
            max_bar_width = self.width - bar_area_x - value_area_width - 5
            if max_bar_width > 0:
                bar_width = min(bar_width, max_bar_width)
                # Redraw bar with adjusted width
                canvas.setFillColor(self.color)
                canvas.rect(bar_x, bar_y, bar_width, bar_height, fill=1, stroke=0)
                value_x = bar_x + bar_width + 5
        
        # Center value text vertically with bar center
        canvas.drawString(value_x, bar_center_y - 4.5, value_text)
    
    def _wrap_text(self, text, max_width, canvas, font_name, font_size):
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_width = canvas.stringWidth(word + " ", font_name, font_size)
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines if lines else [text[:int(max_width / 5)]]  # Fallback truncation


class BarChartFlowable(Flowable):
    """Custom flowable for creating vertical bar charts."""
    
    def __init__(self, label, value, max_value, width=400, height=30, color=HexColor('#3b82f6'), unit=None):
        Flowable.__init__(self)
        self.label = label
        self.value = value
        self.max_value = max_value
        self.width = width
        self.height = height
        self.color = color
        self.unit = unit
    
    def draw(self):
        canvas = self.canv
        
        # Vertical bar chart layout
        # Reserve space for label at bottom
        label_height = 30  # Space for label text
        chart_height = self.height - label_height  # Available height for bar
        
        # Bar width fills available width (compact, sharing edges) but ensure it fits
        bar_width = max(10, min(self.width - 4, self.width * 0.95))  # Ensure bar fits with margins
        bar_x = max(0, (self.width - bar_width) / 2)  # Center bar with small margins
        
        # Calculate bar height as percentage of max value
        if self.max_value > 0:
            bar_height = (abs(self.value) / self.max_value) * chart_height
        else:
            bar_height = 0
        
        # Bar starts from bottom
        bar_y = label_height
        
        # Draw bar (vertical, going up from bottom)
        if bar_height > 0:
            canvas.setFillColor(self.color)
            canvas.rect(bar_x, bar_y, bar_width, bar_height, fill=1, stroke=0)
        
        # Draw label at bottom (centered, with word wrapping if needed)
        canvas.setFont("Times-Roman", 8)
        canvas.setFillColor(HexColor('#111827'))
        # Truncate label to fit width, accounting for font size
        max_label_chars = int(self.width / 5)  # Approximate chars that fit
        label_text = self.label[:max_label_chars] if len(self.label) > max_label_chars else self.label
        label_width = canvas.stringWidth(label_text, "Times-Roman", 8)
        label_x = max(0, (self.width - label_width) / 2)  # Center label, ensure non-negative
        canvas.drawString(label_x, 5, label_text)
        
        # Draw value label on top of bar (centered)
        if isinstance(self.value, (int, float)):
            if self.unit == '%':
                value_text = f"{self.value:+.1f}%"
            elif abs(self.value) < 1:
                value_text = f"{self.value:+.2f}"
            elif abs(self.value) < 100:
                value_text = f"{self.value:+.1f}"
            else:
                value_text = f"{self.value:,.0f}"
            if self.unit and self.unit != '%':
                value_text += f" {self.unit}"
        else:
            value_text = str(self.value)
            if self.unit:
                value_text += f" {self.unit}"
        
        canvas.setFont("Times-Bold", 8)
        canvas.setFillColor(HexColor('#1f2937'))
        value_width = canvas.stringWidth(value_text, "Times-Bold", 8)
        value_x = max(0, (self.width - value_width) / 2)  # Center value text, ensure non-negative
        
        # Position value text: on top of bar if bar is tall enough, otherwise above it
        if bar_height > 18:
            # Put value on top of bar - use white text for visibility
            value_y = bar_y + bar_height - 10
            canvas.setFillColor(HexColor('#ffffff'))
        else:
            # Put value above bar
            value_y = bar_y + bar_height + 2
            canvas.setFillColor(HexColor('#1f2937'))
        
        # Ensure value text doesn't go beyond page
        if value_x + value_width <= self.width:
            canvas.drawString(value_x, value_y, value_text)


class ReportGenerator:
    """Generates professional reports from JSON analytics output."""
    
    def __init__(self, title: str = "CRM Analytics Report", subtitle: Optional[str] = None,
                 use_gemini: bool = False, gemini_api_key: Optional[str] = None):
        """Initialize the report generator."""
        self.title = title
        self.subtitle = subtitle or f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        self.use_gemini = use_gemini
        self.gemini_api_key = gemini_api_key
        self.metric_parser = MetricParser()
    
    def _generate_introduction(self, answer: str, rationale: List[str], key_metrics: List[str]) -> str:
        """Generate a professional introduction section using Gemini if available."""
        if self.use_gemini and self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""Write a professional introduction paragraph (3-4 sentences) for a CRM analytics report based on this data:

Main Finding: {answer}

Key Insights:
{chr(10).join(f'- {insight}' for insight in rationale[:3])}

Key Metrics:
{chr(10).join(f'- {metric}' for metric in key_metrics[:5])}

The introduction should:
- Set the context for the analysis by mentioning specific service categories that are analyzed
- Briefly explain what was analyzed (service request trends, growth patterns, volume distributions)
- Preview the main findings qualitatively by mentioning which categories are trending (avoid repeating specific numbers)
- Explain why this analysis matters for operational planning
- Be professional, concise, and specific about categories mentioned
- Do NOT repeat specific metric values (percentages, exact counts) that are shown in visualizations
- Reference actual category names from the data (e.g., "Recreation and leisure", "Trees", "Roads")

Write only the introduction paragraph, no headers or labels."""
                
                response = model.generate_content(prompt)
                intro = response.text.strip()
                # Clean up any markdown formatting
                intro = intro.replace('**', '').replace('*', '').replace('#', '').strip()
                if intro and len(intro) > 50:
                    return intro
            except Exception as e:
                print(f"Warning: Could not generate introduction with Gemini: {e}")
        
        # Fallback introduction - extract specific categories from answer
        if answer:
            # Extract category names from answer
            categories_mentioned = []
            common_categories = ['Recreation and leisure', 'Trees', 'Roads', 'Engineering', 'Building', 'City General']
            for cat in common_categories:
                if cat.lower() in answer.lower():
                    categories_mentioned.append(cat)
            
            # Build contextual introduction
            if categories_mentioned:
                cat_list = ', '.join(categories_mentioned[:3])
                intro = f"This report presents a comprehensive analysis of CRM service request trends and patterns across key service categories including {cat_list}."
            else:
                intro = "This report presents a comprehensive analysis of CRM service request trends and patterns across key service categories."
            
            # Add context about what the analysis reveals
            if 'trending' in answer.lower() or 'increase' in answer.lower() or 'growth' in answer.lower():
                intro += " The analysis identifies significant growth patterns and emerging trends that impact service delivery and resource allocation."
            else:
                intro += " The analysis examines request volumes, growth rates, and category distributions to inform strategic planning."
            
            return intro
        return "This report presents a comprehensive analysis of CRM service request trends and patterns based on quantitative data analysis."
    
    def _generate_executive_summary(self, answer: str, rationale: List[str], parsed_metrics: List) -> str:
        """Generate a substantive executive summary."""
        if self.use_gemini and self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Build context with metrics
                metrics_context = ""
                if parsed_metrics:
                    top_growth = [m for m in parsed_metrics if m.metric_type == 'growth' and m.value][:3]
                    top_volume = [m for m in parsed_metrics if m.metric_type == 'volume' and m.value][:3]
                    if top_growth:
                        metrics_context += "\nTop Growth Categories:\n" + "\n".join([f"- {m.category or m.label}: {m.value:+.1f}%" for m in top_growth])
                    if top_volume:
                        metrics_context += "\nTop Volume Categories:\n" + "\n".join([f"- {m.category or m.label}: {m.value:,.0f} requests" for m in top_volume])
                
                prompt = f"""Write a concise executive summary paragraph (2-3 sentences maximum) for a CRM analytics report. The executive summary should:

- Provide a brief high-level overview of the most critical findings
- Mention the top 1-2 trending service categories by name
- Highlight key strategic implications for resource allocation
- Be professional, executive-appropriate, and concise
- Do NOT repeat specific percentage values or exact request counts that are already shown in the metrics section

Main Finding: {answer}

Key Insights:
{chr(10).join(f'- {insight}' for insight in rationale[:3])}
{metrics_context}

Write only the executive summary paragraph (2-3 sentences), no headers, labels, or ellipses. Keep it brief and focused on the most important points."""
                
                response = model.generate_content(prompt)
                summary = response.text.strip()
                # Clean up any markdown formatting
                summary = summary.replace('**', '').replace('*', '').replace('#', '').strip()
                if summary and len(summary) > 100:
                    return summary
            except Exception as e:
                print(f"Warning: Could not generate executive summary with Gemini: {e}")
        
        # Fallback executive summary - concise version
        if parsed_metrics:
            growth_metrics = [m for m in parsed_metrics if m.metric_type == 'growth' and m.value]
            volume_metrics = [m for m in parsed_metrics if m.metric_type == 'volume' and m.value]
            
            summary_parts = []
            
            if growth_metrics:
                sorted_growth = sorted(growth_metrics, key=lambda x: abs(x.value), reverse=True)
                top_growth = sorted_growth[0]
                
                # Identify top categories
                top_categories = [m.category for m in sorted_growth[:2] if m.category]
                
                # Use qualitative description instead of exact percentage
                if abs(top_growth.value) > 75:
                    growth_desc = "exceptional growth"
                elif abs(top_growth.value) > 50:
                    growth_desc = "substantial growth"
                elif abs(top_growth.value) > 20:
                    growth_desc = "moderate growth"
                else:
                    growth_desc = "notable changes"
                
                if len(top_categories) >= 2:
                    cat_text = f"{', '.join(top_categories[:2])}"
                elif top_growth.category:
                    cat_text = top_growth.category
                else:
                    cat_text = "key service categories"
                
                summary_parts.append(f"This analysis reveals {cat_text} are experiencing {growth_desc}, requiring strategic resource allocation to maintain service quality.")
            
            # Keep it to 2-3 sentences max
            if len(summary_parts) < 2 and volume_metrics:
                sorted_volume = sorted(volume_metrics, key=lambda x: x.value, reverse=True)
                top_volume = sorted_volume[0]
                
                if top_volume.category:
                    summary_parts.append(f"{top_volume.category} represents a high-volume service area requiring focused capacity planning.")
            
            if summary_parts:
                return " ".join(summary_parts[:2])  # Limit to 2 sentences
        
        # Basic fallback - keep it short
        if answer:
            sentences = answer.split('.')
            if len(sentences) > 1:
                return f"This analysis reveals significant trends in service request patterns. {sentences[0]}."
            return f"This analysis reveals significant trends: {answer}"
        return "This analysis reveals significant trends in service request patterns that require strategic attention."
    
    def _generate_conclusion(self, answer: str, rationale: List[str], recommendations: List[Dict[str, str]]) -> str:
        """Generate a professional conclusion section using Gemini if available."""
        if self.use_gemini and self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                rec_summary = "\n".join([f"- {r.get('description', '')}" for r in recommendations[:3]])
                
                prompt = f"""Write a professional conclusion paragraph (3-4 sentences) for a CRM analytics report based on this data:

Main Finding: {answer}

Key Insights:
{chr(10).join(f'- {insight}' for insight in rationale[:3])}

Top Recommendations:
{rec_summary}

The conclusion should:
- Summarize the key findings qualitatively, mentioning specific service categories that are trending
- Highlight the significance of the trends for operational planning and resource management
- Connect the findings to strategic implications (e.g., capacity needs, service quality, citizen satisfaction)
- Emphasize the importance of taking action and what types of actions might be needed
- Be professional, forward-looking, and actionable
- Reference actual category names from the data when relevant
- Do NOT repeat specific metric values (percentages, exact counts) that are already shown in visualizations

Write only the conclusion paragraph, no headers or labels."""
                
                response = model.generate_content(prompt)
                conclusion = response.text.strip()
                # Clean up any markdown formatting
                conclusion = conclusion.replace('**', '').replace('*', '').replace('#', '').strip()
                if conclusion and len(conclusion) > 50:
                    return conclusion
            except Exception as e:
                print(f"Warning: Could not generate conclusion with Gemini: {e}")
        
        # Fallback conclusion - more contextual and actionable
        if answer:
            # Extract key categories mentioned
            categories_mentioned = []
            common_categories = ['Recreation and leisure', 'Trees', 'Roads', 'Engineering', 'Building', 'City General']
            for cat in common_categories:
                if cat.lower() in answer.lower():
                    categories_mentioned.append(cat)
            
            conclusion_parts = []
            
            if categories_mentioned:
                cat_list = ', '.join(categories_mentioned[:2])
                conclusion_parts.append(f"The analysis reveals significant trends across service categories including {cat_list}, indicating shifts in citizen service needs and operational priorities.")
            else:
                conclusion_parts.append("The analysis reveals significant trends across multiple service categories, indicating shifts in citizen service needs and operational priorities.")
            
            # Add strategic implications
            if 'growth' in answer.lower() or 'increase' in answer.lower():
                conclusion_parts.append("The observed growth patterns suggest that current resource allocation strategies may need adjustment to accommodate increasing demand while maintaining service quality standards.")
            
            conclusion_parts.append("These findings underscore the importance of proactive resource planning, capacity management, and strategic allocation to address emerging service demands effectively.")
            conclusion_parts.append("Continued monitoring and adaptive resource strategies will be essential to ensure responsive service delivery as these trends evolve.")
            
            return " ".join(conclusion_parts)
        return "In summary, this analysis provides valuable insights into service request trends that can inform strategic decision-making and resource allocation."
    
    def _generate_detailed_insights(self, rationale: List[str], parsed_metrics: List) -> List[str]:
        """Generate unique detailed insights that don't repeat previous information."""
        insights = []
        
        if self.use_gemini and self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Build context with parsed metrics
                metrics_context = ""
                if parsed_metrics:
                    category_data = {}
                    for m in parsed_metrics:
                        if m.category and m.value is not None:
                            if m.category not in category_data:
                                category_data[m.category] = {}
                            if m.metric_type == 'growth':
                                category_data[m.category]['growth'] = m.value
                            elif m.metric_type == 'volume':
                                category_data[m.category]['volume'] = m.value
                    
                    if category_data:
                        metrics_context = "\nCategory Metrics:\n"
                        for cat, metrics in list(category_data.items())[:5]:
                            parts = []
                            if 'growth' in metrics:
                                parts.append(f"{metrics['growth']:+.1f}% growth")
                            if 'volume' in metrics:
                                parts.append(f"{metrics['volume']:,.0f} requests")
                            metrics_context += f"- {cat}: {', '.join(parts)}\n"
                
                prompt = f"""Based on these initial insights:
{chr(10).join(f'- {insight}' for insight in rationale[:3])}

{metrics_context}

Generate 3-4 unique, detailed insights that:
- Provide deeper analysis beyond what's already stated
- Reference specific service categories by name when relevant
- Explain the implications and operational context of the trends
- Offer strategic perspective on what these trends mean for capacity planning, resource allocation, or service delivery
- Connect trends to actionable insights (e.g., which categories need more resources, which are emerging priorities)
- Do NOT simply restate the initial insights
- Do NOT repeat specific metric values (percentages, exact counts) that are already shown in visualizations
- Focus on analysis, implications, strategic insights, and operational recommendations

Each insight should be substantive and provide value beyond what's already visible in the metrics. Write each insight as a complete sentence. Format as a numbered list."""
                
                response = model.generate_content(prompt)
                text = response.text.strip()
                
                # Parse numbered list
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Remove numbering (1., 2., etc.)
                    line = re.sub(r'^\d+[\.\)]\s*', '', line)
                    # Remove markdown
                    line = line.replace('**', '').replace('*', '').replace('#', '').strip()
                    if line and len(line) > 30:
                        insights.append(line)
                
                if len(insights) >= 3:
                    return insights[:4]
            except Exception as e:
                print(f"Warning: Could not generate detailed insights with Gemini: {e}")
        
        # Fallback: Generate unique insights from data patterns
        if parsed_metrics:
            growth_metrics = [m for m in parsed_metrics if m.metric_type == 'growth' and m.value]
            volume_metrics = [m for m in parsed_metrics if m.metric_type == 'volume' and m.value]
            
            # Insight 1: Compare growth rates with context (use qualitative comparison)
            if len(growth_metrics) >= 2:
                sorted_growth = sorted(growth_metrics, key=lambda x: abs(x.value), reverse=True)
                top = sorted_growth[0]
                second = sorted_growth[1]
                # Use qualitative comparison instead of exact numbers
                diff = abs(top.value) - abs(second.value)
                if diff > 30:
                    comparison = "significantly higher"
                    implication = "represents a distinct priority area"
                elif diff > 15:
                    comparison = "notably higher"
                    implication = "warrants focused attention"
                else:
                    comparison = "somewhat higher"
                    implication = "shows emerging importance"
                
                if top.category and second.category:
                    insights.append(f"Comparative analysis reveals {top.category} demonstrates {comparison} growth momentum compared to {second.category}, which {implication} for strategic resource allocation and capacity planning.")
                else:
                    insights.append(f"Growth rate analysis reveals the leading category demonstrates {comparison} growth compared to other service areas, indicating accelerating demand that requires strategic attention.")
            
            # Insight 2: Volume vs growth correlation with strategic implications
            if growth_metrics and volume_metrics:
                # Find categories with high growth
                high_growth = sorted([m for m in growth_metrics if abs(m.value) > 50], key=lambda x: abs(x.value), reverse=True)
                # Find corresponding volume metrics
                if high_growth:
                    high_growth_cats = [m.category for m in high_growth if m.category]
                    # Check if these are also high volume
                    high_volume_cats = [m.category for m in volume_metrics if m.value > 300 and m.category]
                    
                    if high_growth_cats:
                        cat_name = high_growth_cats[0]
                        if cat_name in high_volume_cats:
                            insights.append(f"{cat_name} represents a critical service area experiencing both rapid growth and high volume, creating compounded operational challenges that require immediate capacity expansion and process optimization.")
                        else:
                            insights.append(f"Emerging service categories like {cat_name} show rapid growth rates from smaller bases, suggesting new or expanding service demands that may require dedicated resource allocation and specialized process development.")
            
            # Insight 3: Distribution analysis with operational context
            if volume_metrics:
                total_volume = sum(m.value for m in volume_metrics if m.value)
                if total_volume > 0:
                    sorted_volume = sorted(volume_metrics, key=lambda x: x.value, reverse=True)
                    top_volume = sorted_volume[0]
                    percentage = (top_volume.value / total_volume) * 100
                    
                    # Use qualitative description instead of exact percentage
                    if percentage > 40:
                        share_desc = "a dominant share"
                        operational_impact = "central to overall service delivery operations"
                    elif percentage > 25:
                        share_desc = "a substantial share"
                        operational_impact = "a critical component of service delivery"
                    else:
                        share_desc = "a notable share"
                        operational_impact = "an important part of the service portfolio"
                    
                    if top_volume.category:
                        insights.append(f"Volume distribution analysis reveals {top_volume.category} accounts for {share_desc} of total service requests, making it {operational_impact} and highlighting the importance of maintaining robust capacity and response capabilities in this area.")
                    else:
                        insights.append(f"Volume distribution analysis indicates the leading category accounts for {share_desc} of total service requests, highlighting its critical role in overall service delivery.")
            
            # Insight 4: Pattern recognition across categories
            if len(growth_metrics) >= 3:
                positive_growth = [m for m in growth_metrics if m.value > 0]
                if len(positive_growth) >= 3:
                    insights.append("The widespread positive growth across multiple service categories suggests broader trends in citizen engagement and service utilization, indicating a need for comprehensive capacity planning rather than isolated category responses.")
        
        # If we don't have enough insights, add contextual ones with specific value
        if len(insights) < 3:
            if parsed_metrics:
                growth_count = len([m for m in parsed_metrics if m.metric_type == 'growth' and m.value])
                if growth_count > 0:
                    insights.append("The observed growth trends across multiple service categories suggest a dynamic service landscape that requires adaptive resource management strategies and flexible capacity planning to respond effectively to changing demand patterns.")
                else:
                    insights.append("The analysis reveals important patterns in service request distribution that inform strategic resource allocation and operational planning decisions.")
            else:
                insights.append("The observed trends suggest a dynamic service landscape requiring adaptive resource management strategies.")
            
            if len(insights) < 3:
                insights.append("These patterns highlight the importance of continuous monitoring and proactive capacity planning to maintain service quality standards and ensure responsive citizen service delivery.")
        
        return insights[:4] if insights else rationale[:3]
    
    def _extract_key_takeaways(self, answer: str, rationale: List[str], max_items: int = 5) -> List[str]:
        """Extract key takeaways from answer and rationale, making them qualitative and contextual."""
        takeaways = []
        
        # Extract main finding from answer, but make it qualitative
        if answer:
            # Extract category names
            categories_mentioned = []
            common_categories = ['Recreation and leisure', 'Trees', 'Roads', 'traffic and sidewalks', 
                                'Engineering', 'infrastructure and construction', 'Building', 'City General']
            for cat in common_categories:
                if cat.lower() in answer.lower():
                    # Find the full category name
                    for full_cat in ['Recreation and leisure', 'Trees', 'Roads, traffic and sidewalks',
                                    'Engineering, infrastructure and construction', 'Building', 'City General']:
                        if cat.lower() in full_cat.lower() and full_cat not in categories_mentioned:
                            categories_mentioned.append(full_cat)
                            break
            
            # Create qualitative takeaway from answer
            if categories_mentioned:
                cat_list = ', '.join(categories_mentioned[:3])
                if 'trending' in answer.lower() or 'top' in answer.lower():
                    takeaways.append(f"The top trending service request categories include {cat_list}, showing significant growth patterns.")
                else:
                    takeaways.append(f"Key service categories showing notable trends include {cat_list}.")
            else:
                # Use first sentence but remove specific numbers
                sentences = answer.split('.')
                if sentences:
                    first_sent = sentences[0].strip()
                    # Remove specific percentages and numbers
                    first_sent = re.sub(r'\d+\.?\d*%', 'significant', first_sent)
                    first_sent = re.sub(r'\d+ requests?', 'substantial volume', first_sent)
                    first_sent = re.sub(r'\d+', '', first_sent).strip()
                    if first_sent and len(first_sent) > 20:
                        takeaways.append(first_sent + '.')
        
        # Extract qualitative insights from rationale
        for insight in rationale[:max_items - len(takeaways)]:
            if insight:
                # Remove specific numbers and make qualitative
                qualitative = insight
                # Replace percentages with qualitative terms
                qualitative = re.sub(r'\d+\.?\d*%', lambda m: 'substantial growth' if float(m.group().replace('%', '')) > 50 
                                     else 'moderate growth' if float(m.group().replace('%', '')) > 20 else 'notable growth', qualitative)
                # Replace request counts
                qualitative = re.sub(r'\d+ requests?', 'significant volume', qualitative)
                # Remove remaining numbers
                qualitative = re.sub(r'\d+', '', qualitative).strip()
                # Clean up extra spaces and punctuation
                qualitative = re.sub(r'\s+', ' ', qualitative).strip()
                qualitative = re.sub(r'[,\s]+\.', '.', qualitative)
                
                if qualitative and len(qualitative) > 30 and qualitative not in takeaways:
                    takeaways.append(qualitative)
        
        return takeaways[:max_items]
    
    def _find_product_file(self, product_name: str) -> Optional[Path]:
        """Find the CSV file for a given product name."""
        # Map product names to file paths
        product_mapping = {
            'top10_volume_30d': 'top10.csv',
            'backlog_ranked_list': 'backlog_ranked_list.csv',
            'frequency_over_time': 'frequency_over_time.csv',
            'priority_quadrant': 'priority_quadrant_data_p90.csv',
            'geographic_hot_spots': 'geographic_hot_spots.csv',
            'time_to_close': 'time_to_close.csv',
            'seasonality_heatmap': 'seasonality_heatmap.csv',
            'backlog_distribution': 'backlog_distribution.csv',
        }
        
        filename = product_mapping.get(product_name)
        if not filename:
            # Try using product_name directly as filename
            if product_name.endswith('.csv'):
                filename = product_name
            else:
                filename = f"{product_name}.csv"
        
        # Try multiple possible locations
        possible_paths = [
            # Relative to reporting directory
            Path(__file__).parent.parent / 'trends' / 'data' / filename,
            # Relative to backend directory
            Path(__file__).parent.parent.parent / 'trends' / 'data' / filename,
            # Absolute path from workspace
            Path('QHacks2026/backend/trends/data') / filename,
            Path('backend/trends/data') / filename,
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def _load_product_data(self, product_name: str) -> Optional[pd.DataFrame]:
        """Load data from a product CSV file."""
        if not PANDAS_AVAILABLE:
            print(f"Warning: pandas not available, cannot load product data for {product_name}")
            return None
        
        file_path = self._find_product_file(product_name)
        if not file_path:
            print(f"Warning: Could not find file for product {product_name}")
            return None
        
        try:
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            print(f"Warning: Could not load product data from {file_path}: {e}")
            return None
    
    def _detect_chart_type(self, df: pd.DataFrame) -> str:
        """
        Detect the appropriate chart type based on CSV structure.
        
        Returns: 'line', 'bar', 'scatter', 'pie', 'heatmap', or 'table'
        """
        if df.empty or len(df.columns) == 0:
            return 'table'
        
        columns = [col.lower() for col in df.columns]
        
        # Check for top10/ranking data - should be a table
        if 'ranking_type' in df.columns or 'rank' in df.columns:
            return 'bar'  # Will be handled as table in _generate_product_visualization
        
        # Check for backlog data with unresolved_count - should be horizontal bar chart
        if 'unresolved_count' in df.columns:
            return 'bar'  # Will be handled as horizontal bar chart in _generate_product_visualization
        
        # Check for time series data (Line Chart)
        # Has a time/date column + multiple numeric category columns
        time_indicators = ['time', 'date', 'period', 'month', 'year', 'week']
        has_time_col = any(indicator in col for col in columns for indicator in time_indicators)
        numeric_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
        
        if has_time_col and len(numeric_cols) > 2:
            return 'line'
        
        # Check for scatter plot data (Priority Quadrant)
        # Has x, y, and bubble_size or similar multi-dimensional numeric data
        scatter_indicators = ['time_to_close', 'request_count', 'bubble_size', 'open_count']
        if any(indicator in ' '.join(columns) for indicator in scatter_indicators):
            # Check if we have at least 2 numeric dimensions
            if len(numeric_cols) >= 2:
                return 'scatter'
        
        # Check for pie chart data
        # Has name/label column + single value column, or just 2 columns total
        if len(df.columns) == 2:
            # Check if one column is mostly strings and one is numeric
            col1_numeric = df.iloc[:, 0].dtype in ['int64', 'float64']
            col2_numeric = df.iloc[:, 1].dtype in ['int64', 'float64']
            if (col1_numeric and not col2_numeric) or (not col1_numeric and col2_numeric):
                return 'pie'
        
        # Check for geographic/heatmap data
        # Has district/location + multiple metrics
        geo_indicators = ['district', 'location', 'region', 'area', 'electoral']
        if any(indicator in ' '.join(columns) for indicator in geo_indicators):
            if len(numeric_cols) >= 2:
                return 'heatmap'
        
        # Check for bar chart data
        # Has category/label column + one or more numeric value columns
        category_indicators = ['category', 'group', 'name', 'label', 'service level']
        has_category = any(indicator in col for col in columns for indicator in category_indicators)
        
        if has_category and len(numeric_cols) >= 1:
            # If only one numeric column, it's a bar chart
            if len(numeric_cols) == 1:
                return 'bar'
            # If multiple numeric columns but not time-based, still bar chart
            elif not has_time_col:
                return 'bar'
        
        # Default to table for complex or unknown structures
        return 'table'
    
    def _generate_top10_volume_chart(self, df: pd.DataFrame, doc_width: float) -> List:
        """Generate a clean, professional table for top10 volume data."""
        story = []
        
        # Filter for Volume (Last 30 Days) ranking
        volume_data = df[df['ranking_type'] == 'Volume (Last 30 Days)'].head(10)
        
        if volume_data.empty:
            return story
        
        # Create a clean, professional table
        table_data = [['Rank', 'Category', 'Volume', '% of Total']]
        
        for idx, row in volume_data.iterrows():
            rank = int(row['rank'])
            category = str(row['category'])  # Keep full category name
            volume = int(row['primary_metric']) if pd.notna(row['primary_metric']) else 0
            pct = f"{row['secondary_metric']:.1f}%" if pd.notna(row['secondary_metric']) else "N/A"
            table_data.append([str(rank), category, f"{volume:,}", pct])
        
        # Create table with better proportions
        col_widths = [doc_width * 0.08, doc_width * 0.52, doc_width * 0.20, doc_width * 0.20]
        table = Table(table_data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1f2937')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
            ('TOPPADDING', (0, 0), (-1, 0), 14),
            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#111827')),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Rank centered
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),     # Category left-aligned
            ('ALIGN', (2, 0), (3, -1), 'RIGHT'),    # Numbers right-aligned
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            # Grid and borders
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, HexColor('#111827')),
            # Alternating row colors for better readability
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f9fafb')]),
        ]))
        
        story.append(table)
        return story
    
    def _generate_line_chart(self, df: pd.DataFrame, doc_width: float) -> List:
        """Generate line chart visualization for time series data."""
        story = []
        
        if df.empty:
            return story
        
        # Find time column
        time_col = None
        time_indicators = ['time', 'date', 'period', 'month', 'year', 'week']
        for col in df.columns:
            if any(indicator in col.lower() for indicator in time_indicators):
                time_col = col
                break
        
        if not time_col:
            # Use first column as time if no time column found
            time_col = df.columns[0]
        
        # Get numeric columns (excluding time column)
        numeric_cols = [col for col in df.columns 
                       if col != time_col and df[col].dtype in ['int64', 'float64']]
        
        if not numeric_cols:
            return story
        
        # Limit to top 5 categories for readability
        numeric_cols = numeric_cols[:5]
        
        # Create a table showing time series data
        table_data = [[time_col] + [col[:25] for col in numeric_cols]]
        
        # Show last 10-15 rows (most recent data)
        display_df = df.tail(15)
        for idx, row in display_df.iterrows():
            time_val = str(row[time_col])[:15]
            row_data = [time_val]
            for col in numeric_cols:
                val = row[col]
                if pd.notna(val):
                    if isinstance(val, (int, float)):
                        row_data.append(f"{val:,.0f}")
                    else:
                        row_data.append(str(val)[:20])
                else:
                    row_data.append("N/A")
            table_data.append(row_data)
        
        # Create table
        col_widths = [doc_width * 0.2] + [doc_width * 0.8 / len(numeric_cols)] * len(numeric_cols)
        table = Table(table_data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#111827')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, HexColor('#d1d5db')),
        ]))
        
        story.append(table)
        return story
    
    def _generate_scatter_chart(self, df: pd.DataFrame, doc_width: float) -> List:
        """Generate scatter chart visualization for multi-dimensional data."""
        story = []
        
        if df.empty:
            return story
        
        # Find key columns for scatter plot
        x_col = None
        y_col = None
        size_col = None
        
        # Look for common scatter plot column names
        for col in df.columns:
            col_lower = col.lower()
            if 'time_to_close' in col_lower or 'x' in col_lower:
                x_col = col
            elif 'request_count' in col_lower or 'volume' in col_lower or 'y' in col_lower:
                y_col = col
            elif 'bubble_size' in col_lower or 'size' in col_lower or 'open_count' in col_lower:
                size_col = col
        
        # Fallback: use first two numeric columns
        numeric_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
        if not x_col and len(numeric_cols) >= 1:
            x_col = numeric_cols[0]
        if not y_col and len(numeric_cols) >= 2:
            y_col = numeric_cols[1]
        if not size_col and len(numeric_cols) >= 3:
            size_col = numeric_cols[2]
        
        # Find label/group column
        label_col = None
        for col in df.columns:
            if col not in [x_col, y_col, size_col]:
                if df[col].dtype == 'object' or 'group' in col.lower() or 'category' in col.lower() or 'name' in col.lower():
                    label_col = col
                    break
        
        if not x_col or not y_col:
            return story
        
        # Create table showing scatter plot data
        table_headers = []
        if label_col:
            table_headers.append(label_col[:25])
        table_headers.extend([x_col[:25], y_col[:25]])
        if size_col:
            table_headers.append(size_col[:25])
        
        table_data = [table_headers]
        
        # Show top 15-20 rows
        display_df = df.head(20)
        for idx, row in display_df.iterrows():
            row_data = []
            if label_col:
                row_data.append(str(row[label_col])[:30])
            
            x_val = row[x_col] if pd.notna(row[x_col]) else 0
            y_val = row[y_col] if pd.notna(row[y_col]) else 0
            
            if isinstance(x_val, (int, float)):
                row_data.append(f"{x_val:,.1f}")
            else:
                row_data.append(str(x_val)[:15])
            
            if isinstance(y_val, (int, float)):
                row_data.append(f"{y_val:,.0f}")
            else:
                row_data.append(str(y_val)[:15])
            
            if size_col:
                size_val = row[size_col] if pd.notna(row[size_col]) else 0
                if isinstance(size_val, (int, float)):
                    row_data.append(f"{size_val:,.0f}")
                else:
                    row_data.append(str(size_val)[:15])
            
            table_data.append(row_data)
        
        # Create table
        num_cols = len(table_headers)
        if label_col:
            col_widths = [doc_width * 0.4] + [doc_width * 0.6 / (num_cols - 1)] * (num_cols - 1)
        else:
            col_widths = [doc_width / num_cols] * num_cols
        
        table = Table(table_data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#111827')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1 if label_col else 0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, HexColor('#d1d5db')),
        ]))
        
        story.append(table)
        return story
    
    def _generate_pie_chart(self, df: pd.DataFrame, doc_width: float) -> List:
        """Generate pie chart visualization for distribution data."""
        story = []
        
        if df.empty or len(df.columns) < 2:
            return story
        
        # Identify name and value columns
        name_col = None
        value_col = None
        
        # Check which column is numeric
        col1_numeric = df.iloc[:, 0].dtype in ['int64', 'float64']
        col2_numeric = df.iloc[:, 1].dtype in ['int64', 'float64']
        
        if col1_numeric and not col2_numeric:
            value_col = df.columns[0]
            name_col = df.columns[1]
        elif not col1_numeric and col2_numeric:
            name_col = df.columns[0]
            value_col = df.columns[1]
        else:
            # Default: first is name, second is value
            name_col = df.columns[0]
            value_col = df.columns[1]
        
        # Sort by value descending and take top items
        display_df = df.sort_values(value_col, ascending=False).head(15)
        
        # Create bar charts showing distribution
        max_value = display_df[value_col].max() if not display_df.empty else 1
        total_value = display_df[value_col].sum()
        
        # Calculate width per bar (bars side by side)
        num_bars = len(display_df)
        if num_bars > 0:
            # Ensure bars fit within page width with some margin
            max_bar_width = 45  # Max width per bar to prevent overlap
            total_width_needed = num_bars * max_bar_width
            if total_width_needed > int(doc_width) * 0.95:
                # Too many bars, reduce width
                bar_width = (int(doc_width) * 0.95) / num_bars
            else:
                bar_width = min(int(doc_width) / num_bars, max_bar_width)
            
            chart_items = []
            for idx, row in display_df.iterrows():
                name = str(row[name_col])[:20]  # Shorter for vertical bars
                value = float(row[value_col]) if pd.notna(row[value_col]) else 0
                pct = (value / total_value * 100) if total_value > 0 else 0
                
                chart = BarChartFlowable(
                    label=f"{name} ({pct:.1f}%)",
                    value=value,
                    max_value=max_value,
                    width=int(bar_width),
                    height=100,  # Height for vertical bars
                    color=HexColor('#3b82f6'),
                    unit=''
                )
                chart_items.append(chart)
            
            # Use Table to arrange bars side by side
            col_widths = [int(bar_width)] * num_bars
            bar_table = Table([chart_items], colWidths=col_widths)
            bar_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            story.append(bar_table)
        story.append(Spacer(1, 12))
        
        # Add note about chart type
        note = Paragraph(
            "<i>Note: Distribution data showing proportions. Consider using a pie chart visualization for better visual representation.</i>",
            ParagraphStyle('Note', parent=getSampleStyleSheet()['Normal'], fontSize=9, textColor=HexColor('#6b7280'))
        )
        story.append(note)
        
        return story
    
    def _generate_heatmap_table(self, df: pd.DataFrame, doc_width: float) -> List:
        """Generate heatmap/table visualization for geographic or multi-metric data."""
        story = []
        
        if df.empty:
            return story
        
        # Find location/district column
        location_col = None
        geo_indicators = ['district', 'location', 'region', 'area', 'electoral']
        for col in df.columns:
            if any(indicator in col.lower() for indicator in geo_indicators):
                location_col = col
                break
        
        if not location_col:
            # Use first non-numeric column as location
            for col in df.columns:
                if df[col].dtype == 'object':
                    location_col = col
                    break
        
        if not location_col:
            location_col = df.columns[0]
        
        # Get numeric columns (metrics)
        numeric_cols = [col for col in df.columns 
                       if col != location_col and df[col].dtype in ['int64', 'float64']]
        
        if not numeric_cols:
            return story
        
        # Sort by first numeric column descending
        if numeric_cols:
            display_df = df.sort_values(numeric_cols[0], ascending=False).head(15)
        else:
            display_df = df.head(15)
        
        # Create table
        table_headers = [location_col[:25]] + [col[:20] for col in numeric_cols]
        table_data = [table_headers]
        
        for idx, row in display_df.iterrows():
            row_data = [str(row[location_col])[:30]]
            for col in numeric_cols:
                val = row[col]
                if pd.notna(val):
                    if isinstance(val, (int, float)):
                        row_data.append(f"{val:,.1f}")
                    else:
                        row_data.append(str(val)[:15])
                else:
                    row_data.append("N/A")
            table_data.append(row_data)
        
        # Create table with heatmap-style coloring for numeric columns
        num_cols = len(table_headers)
        col_widths = [doc_width * 0.3] + [doc_width * 0.7 / len(numeric_cols)] * len(numeric_cols)
        table = Table(table_data, colWidths=col_widths)
        
        # Calculate color ranges for heatmap
        styles = [
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#111827')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, HexColor('#d1d5db')),
        ]
        
        # Add heatmap coloring for numeric columns (optional - can be resource intensive)
        # For now, just use standard table
        
        table.setStyle(TableStyle(styles))
        
        story.append(table)
        return story
    
    def _generate_backlog_table(self, df: pd.DataFrame, doc_width: float) -> List:
        """Generate horizontal bar chart for backlog ranked list data."""
        story = []
        
        # Sort by unresolved_count descending, then by avg_age_days descending
        sorted_df = df.sort_values(['unresolved_count', 'avg_age_days'], ascending=[False, False]).head(15)
        
        if sorted_df.empty:
            return story
        
        # Extract data for horizontal bar charts - use Service Level 1 only
        # Group by Level 1 to reduce variance
        level1_data = {}
        for idx, row in sorted_df.iterrows():
            level1 = str(row['Service Level 1']) if pd.notna(row['Service Level 1']) else "Unknown"
            unresolved = int(row['unresolved_count']) if pd.notna(row['unresolved_count']) else 0
            
            # Sum unresolved counts for each Level 1 category
            if level1 in level1_data:
                level1_data[level1] += unresolved
            else:
                level1_data[level1] = unresolved
        
        # Sort by unresolved count descending
        sorted_level1 = sorted(level1_data.items(), key=lambda x: x[1], reverse=True)[:15]
        
        labels = [item[0] for item in sorted_level1]
        unresolved_counts = [item[1] for item in sorted_level1]
        
        # Generate horizontal bar charts for unresolved counts
        if unresolved_counts:
            max_unresolved = max(unresolved_counts) if unresolved_counts else 100
            
            # Create charts with border wrapper
            chart_height = 28
            spacer_height = 8
            padding = 4
            num_charts = len(labels)
            
            # Calculate total height for border
            total_height = (num_charts * chart_height) + ((num_charts - 1) * spacer_height) + (padding * 2)
            
            # Create a custom flowable that draws border and contains charts
            class BorderedChartContainer(Flowable):
                def __init__(self, charts_data, width, height, padding):
                    Flowable.__init__(self)
                    self.charts_data = charts_data  # List of (label, value) tuples
                    self.width = width
                    self.height = height
                    self.padding = padding
                    self.max_value = max_unresolved
                
                def wrap(self, *args):
                    return (self.width, self.height)
                
                def draw(self):
                    canvas = self.canv
                    
                    # Draw border rectangle
                    canvas.setStrokeColor(HexColor('#d1d5db'))
                    canvas.setLineWidth(1)
                    canvas.rect(0, 0, self.width, self.height, fill=0, stroke=1)
                    
                    # Draw all charts inside the border
                    y_offset = self.height - self.padding  # Start from top
                    chart_width = self.width - (self.padding * 2) - 2
                    
                    for label, count in self.charts_data:
                        # Create chart flowable
                        chart = HorizontalBarChartFlowable(
                            label=label,
                            value=count,
                            max_value=self.max_value,
                            width=int(chart_width),
                            height=chart_height,
                            color=HexColor('#ef4444'),
                            unit='unresolved'
                        )
                        
                        # Set up chart canvas and dimensions
                        chart.canv = canvas
                        chart.width = chart_width
                        chart.height = chart_height
                        
                        # Draw chart at current position
                        canvas.saveState()
                        canvas.translate(self.padding, y_offset - chart_height)
                        chart.draw()
                        canvas.restoreState()
                        
                        # Move down for next chart
                        y_offset -= (chart_height + spacer_height)
            
            # Create bordered container with all chart data
            bordered_container = BorderedChartContainer(
                list(zip(labels, unresolved_counts)),
                int(doc_width),
                total_height,
                padding
            )
            
            story.append(bordered_container)
        
        return story
    
    def _generate_product_visualization(self, product_name: str, why: str, doc_width: float) -> List:
        """Generate visualization (chart/table) for a product based on detected chart type."""
        story = []
        
        df = self._load_product_data(product_name)
        if df is None or df.empty:
            return story
        
        # Auto-detect chart type and generate appropriate visualization
        chart_type = self._detect_chart_type(df)
        
        if chart_type == 'line':
            story.extend(self._generate_line_chart(df, doc_width))
        elif chart_type == 'scatter':
            story.extend(self._generate_scatter_chart(df, doc_width))
        elif chart_type == 'pie':
            story.extend(self._generate_pie_chart(df, doc_width))
        elif chart_type == 'heatmap':
            story.extend(self._generate_heatmap_table(df, doc_width))
        elif chart_type == 'bar':
            # Check if this is backlog data (has unresolved_count) - use horizontal bar chart
            if 'unresolved_count' in df.columns:
                story.extend(self._generate_backlog_table(df, doc_width))
            # Check if this is top10 data (has ranking_type) - use table
            elif 'ranking_type' in df.columns:
                story.extend(self._generate_top10_volume_chart(df, doc_width))
            else:
                # Use generic bar chart generator
                story.extend(self._generate_bar_chart_generic(df, doc_width))
        else:
            # Fallback to generic table
            story.extend(self._generate_generic_table(df, doc_width))
        
        return story
    
    def _generate_bar_chart_generic(self, df: pd.DataFrame, doc_width: float) -> List:
        """Generate generic bar chart for category + value data."""
        story = []
        
        if df.empty:
            return story
        
        # Find category and value columns
        category_col = None
        value_col = None
        
        # Look for category indicators
        for col in df.columns:
            col_lower = col.lower()
            if any(indicator in col_lower for indicator in ['category', 'group', 'name', 'label', 'service level']):
                category_col = col
                break
        
        # Find numeric value column
        numeric_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
        if numeric_cols:
            value_col = numeric_cols[0]
        
        if not category_col:
            # Use first non-numeric column
            for col in df.columns:
                if col != value_col and df[col].dtype == 'object':
                    category_col = col
                    break
        
        if not category_col or not value_col:
            return self._generate_generic_table(df, doc_width)
        
        # Sort by value descending
        display_df = df.sort_values(value_col, ascending=False).head(15)
        
        # Generate bar charts
        max_value = display_df[value_col].max() if not display_df.empty else 1
        
        # Calculate width per bar (bars side by side)
        num_bars = len(display_df)
        if num_bars > 0:
            # Ensure bars fit within page width with some margin
            max_bar_width = 45  # Max width per bar to prevent overlap
            total_width_needed = num_bars * max_bar_width
            if total_width_needed > int(doc_width) * 0.95:
                # Too many bars, reduce width
                bar_width = (int(doc_width) * 0.95) / num_bars
            else:
                bar_width = min(int(doc_width) / num_bars, max_bar_width)
            
            chart_items = []
            for idx, row in display_df.iterrows():
                category = str(row[category_col])[:25]  # Shorter for vertical bars
                value = float(row[value_col]) if pd.notna(row[value_col]) else 0
                
                chart = BarChartFlowable(
                    label=category,
                    value=value,
                    max_value=max_value,
                    width=int(bar_width),
                    height=100,  # Height for vertical bars
                    color=HexColor('#3b82f6'),
                    unit=''
                )
                chart_items.append(chart)
            
            # Use Table to arrange bars side by side
            col_widths = [int(bar_width)] * num_bars
            bar_table = Table([chart_items], colWidths=col_widths)
            bar_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            story.append(bar_table)
        story.append(Spacer(1, 12))
        
        return story
    
    def _generate_generic_table(self, df: pd.DataFrame, doc_width: float) -> List:
        """Generate generic table for any data structure."""
        story = []
        
        if df.empty or len(df.columns) == 0:
            return story
        
        # Create table with all columns
        table_data = [[col[:25] for col in df.columns]]
        
        # Show first 15 rows
        display_df = df.head(15)
        for idx, row in display_df.iterrows():
            row_data = []
            for val in row.values:
                if pd.notna(val):
                    if isinstance(val, (int, float)):
                        row_data.append(f"{val:,.1f}")
                    else:
                        row_data.append(str(val)[:30])
                else:
                    row_data.append("N/A")
            table_data.append(row_data)
        
        # Create table
        num_cols = len(df.columns)
        col_widths = [doc_width / num_cols] * num_cols
        table = Table(table_data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#111827')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, HexColor('#d1d5db')),
        ]))
        
        story.append(table)
        return story
    
    def _generate_recommendations(self, insights: List[str], metrics: List[str], parsed_metrics: List = None) -> List[Dict[str, str]]:
        """Generate recommendations based on insights and metrics."""
        recommendations = []
        
        if self.use_gemini and self.gemini_api_key:
            try:
                import google.generativeai as genai
                import re
                import json
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Build richer context with parsed metrics
                metrics_context = "\n".join(f'- {metric}' for metric in metrics)
                if parsed_metrics:
                    high_growth = [m for m in parsed_metrics if m.metric_type == 'growth' and m.value and abs(m.value) > 50]
                    high_volume = [m for m in parsed_metrics if m.metric_type == 'volume' and m.value and m.value > 500]
                    if high_growth:
                        metrics_context += "\n\nHigh Growth Categories:\n" + "\n".join([f'- {m.category or m.label}: {m.value:+.1f}%' for m in high_growth[:3]])
                    if high_volume:
                        metrics_context += "\n\nHigh Volume Categories:\n" + "\n".join([f'- {m.category or m.label}: {m.value:,.0f} requests' for m in high_volume[:3]])
                
                prompt = f"""Based on these insights from CRM service request analysis:
{chr(10).join(f'- {insight}' for insight in insights)}

And these metrics:
{metrics_context}

Generate 4-6 specific, actionable recommendations for city management. For each recommendation, provide:
1. Priority (HIGH, MEDIUM, or LOW) - base on growth rates, volume, and impact
2. Brief description (2-3 sentences explaining what action to take)
3. Expected impact (1 sentence describing the benefit)

Format as JSON array with keys: priority, description, impact

Make recommendations specific to the categories and trends mentioned, not generic."""
                
                response = model.generate_content(prompt)
                json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group())
            except Exception as e:
                print(f"Warning: Could not generate recommendations with Gemini: {e}")
        
        if not recommendations:
            # Generate fallback recommendations based on actual data
            for i, insight in enumerate(insights[:4]):
                insight_lower = insight.lower()
                if 'growth' in insight_lower or 'increase' in insight_lower:
                    # Extract category name if possible
                    category_match = None
                    for cat in ['recreation', 'trees', 'roads', 'engineering', 'building', 'city general']:
                        if cat in insight_lower:
                            category_match = cat.title()
                            break
                    
                    category = category_match or "high-growth categories"
                    recommendations.append({
                        'priority': 'HIGH' if i == 0 else 'MEDIUM',
                        'description': f'Increase resource allocation and staffing for {category} to handle the growing demand and maintain service quality.',
                        'impact': 'Will help prevent service delays and maintain citizen satisfaction as demand increases'
                    })
                elif 'volume' in insight_lower or 'requests' in insight_lower:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'description': 'Review and optimize resource allocation for high-volume service categories to improve response times.',
                        'impact': 'Will improve operational efficiency and reduce wait times for citizens'
                    })
        
        return recommendations[:6]
    
    def generate_pdf(self, data: Dict) -> bytes:
        """Generate a professional PDF report using ReportLab."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install it with: pip install reportlab"
            )
        
        answer = data.get('answer', '')
        rationale = data.get('rationale', [])
        key_metrics = data.get('key_metrics', [])
        
        # Parse metrics for better visualization
        parsed_metrics = self.metric_parser.parse_all(key_metrics) if key_metrics else []
        
        # Validate parsed metrics - ensure we have real data
        valid_parsed_metrics = [m for m in parsed_metrics if m.value is not None]
        if len(valid_parsed_metrics) < len(parsed_metrics):
            print(f"Warning: {len(parsed_metrics) - len(valid_parsed_metrics)} metrics could not be parsed")
        
        # Extract key takeaways
        key_takeaways = self._extract_key_takeaways(answer, rationale)
        
        # Generate recommendations with parsed metrics context
        recommendations = self._generate_recommendations(rationale, key_metrics, valid_parsed_metrics)
        
        # Generate introduction, executive summary, and conclusion
        introduction = self._generate_introduction(answer, rationale, key_metrics)
        executive_summary = self._generate_executive_summary(answer, rationale, valid_parsed_metrics)
        conclusion = self._generate_conclusion(answer, rationale, recommendations)
        
        # Create PDF buffer
        pdf_buffer = BytesIO()
        
        # Create document with margins
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Professional color palette
        colors = {
            'primary': HexColor('#1e40af'),      # Deep blue
            'primary_light': HexColor('#3b82f6'), # Medium blue
            'accent': HexColor('#059669'),       # Green
            'accent_warm': HexColor('#dc2626'),  # Red
            'text_primary': HexColor('#111827'), # Dark gray
            'text_secondary': HexColor('#4b5563'), # Medium gray
            'text_tertiary': HexColor('#6b7280'), # Light gray
            'bg_light': HexColor('#f9fafb'),     # Very light gray
            'bg_medium': HexColor('#f3f4f6'),    # Light gray
            'border': HexColor('#e5e7eb'),       # Border gray
            'success': HexColor('#10b981'),      # Success green
            'warning': HexColor('#f59e0b'),      # Warning orange
            'error': HexColor('#ef4444'),        # Error red
        }
        
        # Custom styles - Professional typography
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors['text_primary'],
            spaceAfter=8,
            fontName='Helvetica-Bold',
            leading=34
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors['text_secondary'],
            spaceAfter=24,
            fontName='Times-Roman',
            leading=14
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors['text_primary'],
            spaceBefore=28,
            spaceAfter=14,
            fontName='Times-Bold',
            leading=22
        )
        
        summary_style = ParagraphStyle(
            'SummaryStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors['text_primary'],
            leftIndent=0,
            rightIndent=0,
            spaceBefore=0,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman',
            leading=20
        )
        
        insight_style = ParagraphStyle(
            'InsightStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors['text_primary'],
            leftIndent=0,
            rightIndent=0,
            spaceBefore=8,
            spaceAfter=8,
            fontName='Times-Roman',
            leading=16
        )
        
        metric_label_style = ParagraphStyle(
            'MetricLabel',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors['text_secondary'],
            leftIndent=0,
            spaceBefore=0,
            spaceAfter=2,
            fontName='Times-Roman'
        )
        
        metric_value_style = ParagraphStyle(
            'MetricValue',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors['text_primary'],
            leftIndent=0,
            spaceBefore=0,
            spaceAfter=0,
            fontName='Times-Bold'
        )
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors['text_tertiary'],
            alignment=TA_CENTER,
            spaceBefore=40,
            fontName='Times-Roman'
        )
        
        takeaways_style = ParagraphStyle(
            'TakeawaysStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors['text_primary'],
            leftIndent=0,
            spaceBefore=6,
            spaceAfter=6,
            fontName='Times-Roman',
            leading=18
        )
        
        recommendation_style = ParagraphStyle(
            'RecommendationStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors['text_primary'],
            leftIndent=0,
            spaceBefore=0,
            spaceAfter=0,
            fontName='Times-Roman',
            leading=18
        )
        
        priority_style = ParagraphStyle(
            'PriorityStyle',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Times-Bold',
            spaceAfter=6
        )
        
        methodology_style = ParagraphStyle(
            'MethodologyStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors['text_secondary'],
            leftIndent=0,
            spaceBefore=6,
            spaceAfter=6,
            fontName='Times-Roman',
            leading=16
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph(self.title, title_style))
        story.append(Spacer(1, 4))
        
        # Subtitle
        story.append(Paragraph(self.subtitle, subtitle_style))
        
        # Divider line
        divider = Table(
            [[Paragraph("", ParagraphStyle('Divider', parent=styles['Normal'], fontSize=1))]],
            colWidths=[doc.width],
            style=TableStyle([
                ('LINEBELOW', (0, 0), (-1, -1), 1, colors['border']),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ])
        )
        story.append(divider)
        story.append(Spacer(1, 20))
        
        # Introduction section - no colored background
        story.append(KeepTogether([
            Paragraph("Introduction", heading_style),
            Paragraph(introduction, summary_style),
            Spacer(1, 20)
        ]))
        
        # Executive Summary section - no colored background, use generated summary
        story.append(KeepTogether([
            Paragraph("Executive Summary", heading_style),
            Paragraph(executive_summary, summary_style),
            Spacer(1, 20)
        ]))
        
        # Key Takeaways section - pure text, no boxes
        if key_takeaways:
            takeaways_content = [Paragraph("Key Takeaways", heading_style)]
            for i, takeaway in enumerate(key_takeaways):
                takeaway_text = f"<b>{i+1}.</b> {takeaway}"
                takeaways_content.append(Paragraph(takeaway_text, takeaways_style))
                takeaways_content.append(Spacer(1, 8))
            takeaways_content.append(Spacer(1, 12))
            story.append(KeepTogether(takeaways_content))
        
        # Enhanced Metrics Dashboard section with dual bar charts
        if parsed_metrics:
            story.append(Paragraph("Metrics Analysis", heading_style))
            
            # Group metrics by category and extract different types
            growth_metrics = [m for m in parsed_metrics if m.metric_type == 'growth' and m.value is not None and m.category]
            volume_metrics = [m for m in parsed_metrics if m.metric_type == 'volume' and m.value is not None and m.category]
            
            # Also look for "increase" and "recent" metrics in the original key_metrics
            increase_metrics = []
            recent_volume_metrics = []
            
            # Parse original metrics to find increases and recent volumes
            for metric_text in key_metrics:
                parsed = self.metric_parser.parse(metric_text)
                if parsed.category:
                    metric_lower = metric_text.lower()
                    # Check if it's an increase metric
                    if 'increase' in metric_lower and parsed.value is not None:
                        increase_metrics.append(parsed)
                    # Check if it's a recent volume metric
                    elif 'recent' in metric_lower and parsed.value is not None:
                        recent_volume_metrics.append(parsed)
            
            # Also check parsed volume_metrics for recent volumes and increases (in case they were parsed as volume type)
            for metric in volume_metrics:
                metric_text_lower = metric.original_text.lower()
                # Check if it's a recent volume metric
                if 'recent' in metric_text_lower:
                    if metric.category and metric.value is not None:
                        # Check if we already have this category
                        found = False
                        for rv in recent_volume_metrics:
                            if rv.category == metric.category:
                                found = True
                                break
                        if not found:
                            recent_volume_metrics.append(metric)
                # Check if it's an increase metric
                elif 'increase' in metric_text_lower or 'decrease' in metric_text_lower:
                    if metric.category and metric.value is not None:
                        # Check if we already have this category
                        found = False
                        for inc in increase_metrics:
                            if inc.category == metric.category:
                                found = True
                                break
                        if not found:
                            increase_metrics.append(metric)
            
            # Combine metrics by category
            category_metrics = {}
            
            # Add growth metrics
            for metric in growth_metrics:
                if metric.category:
                    if metric.category not in category_metrics:
                        category_metrics[metric.category] = {'growth': None, 'increase': None, 'recent_volume': None, 'original_value': None}
                    category_metrics[metric.category]['growth'] = metric.value
            
            # Add increase metrics
            for metric in increase_metrics:
                if metric.category:
                    if metric.category not in category_metrics:
                        category_metrics[metric.category] = {'growth': None, 'increase': None, 'recent_volume': None, 'original_value': None}
                    category_metrics[metric.category]['increase'] = metric.value
            
            # Add recent volume metrics
            for metric in recent_volume_metrics:
                if metric.category:
                    if metric.category not in category_metrics:
                        category_metrics[metric.category] = {'growth': None, 'increase': None, 'recent_volume': None, 'original_value': None}
                    category_metrics[metric.category]['recent_volume'] = metric.value
            
            # Calculate original values and ensure we have growth percentages
            for category, metrics_data in category_metrics.items():
                # Calculate original value from recent volume and increase
                if metrics_data['recent_volume'] is not None and metrics_data['increase'] is not None:
                    metrics_data['original_value'] = metrics_data['recent_volume'] - metrics_data['increase']
                # Calculate original value from recent volume and growth percentage
                elif metrics_data['recent_volume'] is not None and metrics_data['growth'] is not None:
                    if metrics_data['growth'] != 0:
                        metrics_data['original_value'] = metrics_data['recent_volume'] / (1 + metrics_data['growth'] / 100)
                    else:
                        metrics_data['original_value'] = metrics_data['recent_volume']
                # If we have increase and original but no growth, calculate growth
                elif metrics_data['increase'] is not None and metrics_data['original_value'] is not None and metrics_data['growth'] is None:
                    if metrics_data['original_value'] > 0:
                        metrics_data['growth'] = (metrics_data['increase'] / metrics_data['original_value']) * 100
                # If we have increase and growth but no original, calculate original
                elif metrics_data['increase'] is not None and metrics_data['growth'] is not None and metrics_data['original_value'] is None:
                    if metrics_data['growth'] != 0:
                        metrics_data['original_value'] = metrics_data['increase'] / (metrics_data['growth'] / 100)
                    else:
                        metrics_data['original_value'] = 0
            
            # Filter to only categories that have both original value and growth percentage
            valid_categories = {
                cat: data for cat, data in category_metrics.items()
                if data['original_value'] is not None and data['growth'] is not None
            }
            
            # Sort categories by growth rate
            sorted_categories = sorted(valid_categories.items(), 
                                     key=lambda x: abs(x[1]['growth']) if x[1]['growth'] else 0, 
                                     reverse=True)[:10]
            
            # Calculate max original value for scaling bars
            max_original = max([data['original_value'] for data in valid_categories.values() if data['original_value'] is not None], default=1000)
            
            # Calculate max percent increase for scaling increase bars
            max_percent = max([abs(data['growth']) for data in valid_categories.values() if data['growth'] is not None], default=100)
            # Ensure minimum of 100% for better visualization
            max_percent = max(max_percent, 100)
            
            # Display metrics with dual bar charts
            metric_charts = []
            
            # First, try to display dual bar charts for categories with complete data
            if sorted_categories:
                for category, metrics_data in sorted_categories:
                    # Create dual bar chart
                    chart = DualBarChartFlowable(
                        label=category,
                        original_value=metrics_data['original_value'],
                        percent_increase=metrics_data['growth'],
                        max_original_value=max_original,
                        max_percent_increase=max_percent,
                        width=int(doc.width),
                        height=50
                    )
                    metric_charts.append(chart)
                    metric_charts.append(Spacer(1, 10))
            
            # Also add simple bar charts for categories with just growth or volume data
            # This ensures we always show some visualizations even if we don't have complete data
            if len(metric_charts) == 0:
                # Create charts from growth metrics
                if growth_metrics:
                    max_growth = max([abs(m.value) for m in growth_metrics if m.value is not None], default=100)
                    for metric in sorted(growth_metrics, key=lambda x: abs(x.value) if x.value else 0, reverse=True)[:10]:
                        if metric.category and metric.value is not None:
                            chart = BarChartFlowable(
                                label=metric.category,
                                value=metric.value,
                                max_value=max_growth,
                                width=int(doc.width),
                                height=30,
                                color=HexColor('#10b981') if metric.value > 0 else HexColor('#ef4444'),
                                unit='%'
                            )
                            metric_charts.append(chart)
                            metric_charts.append(Spacer(1, 8))
                
                # Create charts from volume metrics
                if volume_metrics and len(metric_charts) < 5:
                    max_volume = max([m.value for m in volume_metrics if m.value is not None], default=1000)
                    for metric in sorted(volume_metrics, key=lambda x: x.value if x.value else 0, reverse=True)[:10]:
                        if metric.category and metric.value is not None:
                            # Skip if we already have this category
                            already_added = any(
                                hasattr(chart, 'label') and chart.label == metric.category 
                                for chart in metric_charts if isinstance(chart, BarChartFlowable)
                            )
                            if not already_added:
                                chart = BarChartFlowable(
                                    label=metric.category,
                                    value=metric.value,
                                    max_value=max_volume,
                                    width=int(doc.width),
                                    height=30,
                                    color=HexColor('#3b82f6'),
                                    unit='requests'
                                )
                                metric_charts.append(chart)
                                metric_charts.append(Spacer(1, 8))
            
            # Display all charts
            if metric_charts:
                story.append(KeepTogether(metric_charts))
                story.append(Spacer(1, 12))
        elif key_metrics:
            # Fallback to simple metrics display
            story.append(Paragraph("Key Metrics", heading_style))
            for metric_text in key_metrics:
                metric_table = Table(
                    [[Paragraph(metric_text, metric_label_style)]],
                    colWidths=[doc.width],
                    style=TableStyle([
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors['border']),
                    ])
                )
                story.append(metric_table)
            story.append(Spacer(1, 20))
        
        # Detailed Insights section - generate unique insights
        detailed_insights = self._generate_detailed_insights(rationale, valid_parsed_metrics)
        if detailed_insights:
            insights_content = [Paragraph("Detailed Insights", heading_style)]
            for i, insight in enumerate(detailed_insights):
                insight_text = f"<b>{i+1}.</b> {insight}"
                insights_content.append(Paragraph(insight_text, insight_style))
                insights_content.append(Spacer(1, 8))
            insights_content.append(Spacer(1, 12))
            story.append(KeepTogether(insights_content))
        
        # Recommendations section - subtle color accents for priority
        if recommendations:
            recs_content = [Paragraph("Recommendations", heading_style)]
            
            # Priority color mapping (hex values for Paragraph XML)
            priority_colors = {
                'HIGH': '#ef4444',  # Red
                'MEDIUM': '#f59e0b',  # Orange
                'LOW': '#10b981'  # Green
            }
            priority_border_colors = {
                'HIGH': colors['error'],
                'MEDIUM': colors['warning'],
                'LOW': colors['success']
            }
            
            for i, rec in enumerate(recommendations):
                priority = rec.get('priority', 'MEDIUM')
                description = rec.get('description', '')
                impact = rec.get('impact', '')
                
                priority_color_hex = priority_colors.get(priority, '#6b7280')
                priority_border_color = priority_border_colors.get(priority, colors['text_secondary'])
                
                # Format recommendation with subtle color accent
                # Use colored priority badge
                rec_text = f"<b>{i+1}.</b> <font color='{priority_color_hex}'><b>[{priority}]</b></font> {description}"
                if impact:
                    rec_text += f"<br/><i>Expected Impact:</i> {impact}"
                
                # Create a table with subtle left border accent
                rec_table = Table(
                    [[Paragraph(rec_text, recommendation_style)]],
                    colWidths=[doc.width],
                    style=TableStyle([
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('LINELEFT', (0, 0), (0, -1), 2, priority_border_color),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ])
                )
                recs_content.append(rec_table)
                recs_content.append(Spacer(1, 10))
            
            recs_content.append(Spacer(1, 8))
            story.append(KeepTogether(recs_content))
        
        # Product-based visualizations section - "Supporting Data Analysis"
        products = data.get('products', [])
        if products:
            # Create content list starting with heading to keep together with first chart
            charts_section_content = []
            charts_section_content.append(Spacer(1, 20))
            charts_section_content.append(Paragraph("Supporting Data Analysis", heading_style))
            charts_section_content.append(Spacer(1, 12))
            
            first_chart_added = False
            for idx, product_item in enumerate(products):
                product_name = product_item.get('product', '')
                why = product_item.get('why', '')
                
                if product_name:
                    products_content = []
                    
                    # Create appropriate section title based on product type
                    title_mapping = {
                        'top10_volume_30d': "Top 10 Categories by Volume (Last 30 Days)",
                        'backlog_ranked_list': "Backlog Analysis - Urgent Unresolved Items",
                        'frequency_over_time': "Frequency Over Time - Request Trends",
                        'priority_quadrant': "Priority Quadrant Analysis",
                        'geographic_hot_spots': "Geographic Hot Spots Analysis",
                        'time_to_close': "Time to Close Analysis",
                        'seasonality_heatmap': "Seasonality Heatmap",
                        'backlog_distribution': "Backlog Distribution Analysis",
                    }
                    
                    section_title = title_mapping.get(product_name)
                    if not section_title:
                        # Try to generate a meaningful title from product name
                        section_title = product_name.replace('_', ' ').title()
                        # Add "Analysis" if not already present
                        if 'analysis' not in section_title.lower():
                            section_title += " Analysis"
                    
                    products_content.append(Paragraph(section_title, heading_style))
                    products_content.append(Spacer(1, 12))  # Padding between title and chart
                    
                    # Generate visualization (includes charts and tables)
                    viz_items = self._generate_product_visualization(product_name, why, doc.width)
                    if viz_items:
                        products_content.extend(viz_items)
                        products_content.append(Spacer(1, 20))
                    
                    if len(products_content) > 1:  # More than just the heading
                        # Add first chart to the section content to keep heading with first chart
                        if not first_chart_added:
                            charts_section_content.extend(products_content)
                            first_chart_added = True
                            # Keep heading with first chart
                            story.append(KeepTogether(charts_section_content))
                        else:
                            # Subsequent charts can be separate
                            story.append(KeepTogether(products_content))
        
        # Conclusion section - no colored background
        story.append(KeepTogether([
            Paragraph("Conclusion", heading_style),
            Paragraph(conclusion, summary_style),
            Spacer(1, 20)
        ]))
        
        # Methodology section
        methodology_content = [Paragraph("Methodology", heading_style)]
        
        # Build methodology items based on actual data
        methodology_items = [
            "<b>Data Sources:</b> CRM Service Requests database",
            "<b>Analysis Period:</b> Based on the specified date range in the report subtitle",
            "<b>Metrics Calculation:</b> Quantitative analysis of request volumes, growth rates, and category distributions"
        ]
        
        # Add specific metrics info if available
        if parsed_metrics:
            growth_count = len([m for m in parsed_metrics if m.metric_type == 'growth'])
            volume_count = len([m for m in parsed_metrics if m.metric_type == 'volume'])
            if growth_count > 0 or volume_count > 0:
                metric_types = []
                if growth_count > 0:
                    metric_types.append(f"{growth_count} growth rate metric{'s' if growth_count > 1 else ''}")
                if volume_count > 0:
                    metric_types.append(f"{volume_count} volume metric{'s' if volume_count > 1 else ''}")
                methodology_items.append(f"<b>Metrics Analyzed:</b> {', '.join(metric_types)}")
        
        methodology_items.append("<b>Insights Generation:</b> Pattern recognition and statistical analysis of trends")
        
        for item in methodology_items:
            methodology_table = Table(
                [[Paragraph(item, methodology_style)]],
                colWidths=[doc.width],
                style=TableStyle([
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors['border']),
                ])
            )
            methodology_content.append(methodology_table)
        
        story.append(KeepTogether(methodology_content))
        
        # Footer
        story.append(Spacer(1, 20))
        story.append(Paragraph("Report generated by CRM Analytics System", footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        return pdf_bytes
    
    def generate(self, data: Dict) -> bytes:
        """Generate a PDF report."""
        return self.generate_pdf(data)
    
    def save_report(self, data: Dict, output_path: str):
        """Generate and save a PDF report to a file."""
        report = self.generate_pdf(data)
        with open(output_path, 'wb') as f:
            f.write(report)


def generate_report_from_json(json_data: Dict, title: Optional[str] = None, 
                              output_path: Optional[str] = None) -> bytes:
    """Convenience function to generate a PDF report from JSON data."""
    generator = ReportGenerator(title=title) if title else ReportGenerator()
    report = generator.generate_pdf(json_data)
    
    if output_path:
        generator.save_report(json_data, output_path)
    
    return report
