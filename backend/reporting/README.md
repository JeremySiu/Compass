# 📊 Report Generator

Professional report generation system for CRM Analytics. Converts JSON analytics output into beautifully formatted reports in multiple formats with enhanced visualizations and actionable insights.

## Features

- ✅ **Multiple Output Formats**: HTML, Markdown, Plain Text, and PDF
- ✅ **Enhanced Visualizations**: Metric cards, progress bars, trend indicators, color-coded sections
- ✅ **Professional Styling**: Modern, print-ready HTML reports with responsive design
- ✅ **PDF Generation**: High-quality PDF reports generated directly with ReportLab
- ✅ **Structured Output**: Organized sections including Executive Summary, Key Takeaways, Metrics Dashboard, Insights, Recommendations, and Methodology
- ✅ **Smart Metric Parsing**: Automatically extracts and visualizes quantitative data from text
- ✅ **Actionable Recommendations**: AI-powered recommendations with priority levels (optional Gemini integration)
- ✅ **Easy Integration**: Simple Python API and CLI tool
- ✅ **Customizable**: Custom titles, subtitles, and styling

## JSON Input Structure

The report generator expects JSON data with the following structure:

```json
{
  "answer": "Main summary answer",
  "rationale": [
    "Detailed insight point 1",
    "Detailed insight point 2",
    "Detailed insight point 3"
  ],
  "key_metrics": [
    "Metric 1",
    "Metric 2",
    "Metric 3"
  ]
}
```

### Example

```json
{
  "answer": "Recreation and leisure has the highest volume with 663 requests in the last 30 days.",
  "rationale": [
    "Recreation and leisure leads with 663 requests (18.5% of total volume)",
    "Roads, traffic and sidewalks is second with 562 requests (15.68%)",
    "These top 2 categories account for over 34% of all recent requests"
  ],
  "key_metrics": ["663 requests", "18.5%", "562 requests", "15.68%"]
}
```

## Usage

### Python API

```python
from reporting import ReportGenerator

# Initialize generator
generator = ReportGenerator(
    title="CRM Analytics Report",
    subtitle="Last 30 Days Analysis"
)

# Your JSON data
data = {
    "answer": "...",
    "rationale": [...],
    "key_metrics": [...]
}

# Generate HTML report
html_report = generator.generate(data, 'html')

# Generate Markdown report
md_report = generator.generate(data, 'markdown')

# Generate Text report
text_report = generator.generate(data, 'text')

# Save to file
generator.save_report(data, 'output.html', 'html')
```

### Convenience Function

```python
from reporting import generate_report_from_json

data = {...}  # Your JSON data

# Generate and optionally save
report = generate_report_from_json(
    json_data=data,
    output_format='html',
    title="Custom Report Title",
    output_path='report.html'
)
```

### CLI Tool

```bash
# From JSON file
python reporting/cli.py input.json -o output.html -f html

# From JSON string
python reporting/cli.py '{"answer": "...", "rationale": [...], "key_metrics": [...]}' -o report.html

# With custom title
python reporting/cli.py input.json -o output.html -t "My Custom Report" -s "Q1 2024"

# Generate Markdown
python reporting/cli.py input.json -o report.md -f markdown

# Generate Text
python reporting/cli.py input.json -o report.txt -f text

# Generate PDF
python reporting/cli.py input.json -o report.pdf -f pdf
```

### Test Script

Run the test script to see examples:

```bash
python reporting/test_report.py
```

This will generate sample reports in all formats using example data.

## Enhanced Report Sections

### 📊 Executive Summary
- High-level overview with gradient background
- Clear, concise summary of findings

### 🎯 Key Takeaways
- Top 3-5 insights extracted automatically
- Visual callout box format

### 📈 Metrics Dashboard
- **Visual Metric Cards**: Large numbers with color-coded borders
  - Growth metrics: Green theme
  - Volume metrics: Blue theme
  - Percentage metrics: Orange theme
- **Trend Indicators**: Up (↗) and Down (↘) arrows
- **Progress Bars**: Visual progress bars for percentages
- **Category Labels**: Automatic category extraction

### 🔍 Detailed Insights
- Bulleted list with checkmarks
- Hover effects for better UX
- Color-coded borders

### 💡 Recommendations
- Actionable recommendations with priority levels
- Color-coded priority badges (HIGH/MEDIUM/LOW)
- Impact descriptions
- Optional Gemini AI integration for intelligent recommendations

### 📋 Methodology
- Data sources documentation
- Analysis approach
- Calculation methods
- Notes and disclaimers

## Output Formats

### HTML
- Professional styling with modern CSS
- Enhanced visualizations (metric cards, progress bars)
- Responsive design
- Print-friendly
- Color-coded sections
- Interactive hover effects

### Markdown
- Clean, readable format
- Includes all enhanced sections
- Grouped metrics by type
- Compatible with GitHub, GitLab, etc.

### Text
- Plain text format
- Includes all sections
- Good for email or simple display

## Integration with FastAPI

You can easily integrate this into your FastAPI endpoints:

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse, Response
from reporting import ReportGenerator

app = FastAPI()

@app.post("/api/report/generate")
async def generate_report(data: dict):
    generator = ReportGenerator(
        title="CRM Analytics Report",
        subtitle="Generated Report"
    )
    
    html_report = generator.generate(data, 'html')
    return HTMLResponse(content=html_report)

@app.post("/api/report/download")
async def download_report(data: dict):
    generator = ReportGenerator()
    generator.save_report(data, 'temp_report.html', 'html')
    return FileResponse('temp_report.html', media_type='text/html')
```

## File Structure

```
reporting/
├── __init__.py              # Module exports
├── report_generator.py      # Main report generator class (enhanced)
├── metric_parser.py          # Metric parsing utility
├── cli.py                   # CLI tool
├── test_report.py          # Test script with examples
├── example_input.json      # Example JSON input
└── README.md               # This file
```

## Requirements

Core functionality uses only Python standard library:
- `json`
- `datetime`
- `typing`
- `pathlib`
- `re` (for metric parsing)
- `dataclasses` (for structured metric data)

For PDF generation, install:
```bash
pip install reportlab
```

For optional Gemini AI recommendations, install:
```bash
pip install google-generativeai
```

Note: `reportlab` is pure Python with no system dependencies, making it easy to install on all platforms including Windows. It provides direct PDF generation with full control over layout and styling, resulting in professional, high-quality reports.

## Examples

See `test_report.py` for complete examples with both trending analysis and volume analysis data.

## Advanced Usage

### Using Metric Parser Directly

```python
from reporting import MetricParser

parser = MetricParser()
metrics = parser.parse_all(["663 requests", "73.1% growth", "280 increase"])

for metric in metrics:
    print(f"{metric.label}: {metric.value} {metric.unit} ({metric.metric_type})")
```

### Generating Recommendations with Gemini

```python
from reporting import ReportGenerator

generator = ReportGenerator(
    title="CRM Analytics Report",
    subtitle="Analysis Report",
    use_gemini=True,
    gemini_api_key="your-api-key-here"
)

# Recommendations will be automatically generated using Gemini
report = generator.generate_html(data)
```

## Notes

- The HTML format includes inline CSS for portability (no external stylesheets needed)
- Reports are UTF-8 encoded
- HTML reports are mobile-responsive
- Metric parsing automatically extracts values, units, categories, and trends from text
- All formats include enhanced sections: Executive Summary → Key Takeaways → Metrics Dashboard → Detailed Insights → Recommendations → Methodology
