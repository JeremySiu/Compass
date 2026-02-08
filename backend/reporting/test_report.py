"""
Test script to demonstrate the PDF report generator with example data.
"""

import os
from dotenv import load_dotenv
from report_generator import ReportGenerator

# Load environment variables
load_dotenv()

# Example data matching the structure provided
example_data = {
    "answer": "The top trending service requests for this year are led by 'Recreation and leisure', 'Trees', and 'Roads, traffic and sidewalks', all showing substantial increases in volume. 'Recreation and leisure' has the highest absolute increase in requests, while 'Trees' demonstrates the most significant growth rate.",
    "rationale": [
        "'Recreation and leisure' is the top trending category with an absolute increase of 280 requests and a 73.1% growth rate, reaching a recent volume of 663 requests.",
        "'Trees' shows the highest growth rate at 108.9%, correlating to an absolute increase of 172 requests and a recent volume of 330 requests.",
        "'Roads, traffic and sidewalks' is also trending significantly upward with an increase of 99 requests (21.4% growth rate) and a recent volume of 562 requests.",
        "'Engineering, infrastructure and construction' also exhibits a high growth rate of 102.4%, with an absolute increase of 43 requests, suggesting rapid growth from a smaller base (recent volume of 85 requests).",
        "Other notable trending categories include 'Building' with an increase of 78 requests (22.7% growth, 422 recent volume) and 'City General' with an increase of 79 requests (71.8% growth, 189 recent volume)."
    ],
    "key_metrics": [
        "280 requests increase in Recreation and leisure",
        "73.1% growth in Recreation and leisure",
        "663 recent requests in Recreation and leisure",
        "108.9% growth in Trees",
        "172 requests increase in Trees",
        "99 requests increase in Roads, traffic and sidewalks",
        "102.4% growth in Engineering, infrastructure and construction"
    ],
    "products": [
        {
            "product": "top10_volume_30d",
            "why": "Identify highest current demand"
        },
        {
            "product": "backlog_ranked_list",
            "why": "Identify urgent unresolved items"
        }
    ]
}

# Simple volume analysis example
volume_example = {
    "answer": "Recreation and leisure has the highest volume with 663 requests in the last 30 days.",
    "rationale": [
        "Recreation and leisure leads with 663 requests (18.5% of total volume)",
        "Roads, traffic and sidewalks is second with 562 requests (15.68%)",
        "These top 2 categories account for over 34% of all recent requests"
    ],
    "key_metrics": ["663 requests", "18.5%", "562 requests", "15.68%"]
}

def test_pdf():
    """Test PDF report generation."""
    
    print("=" * 80)
    print("Testing PDF Report Generator - Trending Analysis Example")
    print("=" * 80)
    
    # Check for Gemini API key
    gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    use_gemini = bool(gemini_api_key)
    
    if use_gemini:
        print("\n✓ Gemini API key found - will generate professional introduction and conclusion")
    else:
        print("\n⚠ No Gemini API key found - using fallback content")
        print("   Set GEMINI_API_KEY environment variable to enable AI-generated content")
    
    generator = ReportGenerator(
        title="CRM Analytics Report - Trending Categories",
        subtitle="Year-over-Year Growth Analysis",
        use_gemini=use_gemini,
        gemini_api_key=gemini_api_key
    )
    
    # Generate PDF report
    print("\nGenerating PDF report...")
    try:
        generator.save_report(example_data, 'test_report.pdf')
        print("   ✓ Saved to: test_report.pdf")
    except ImportError as e:
        print(f"   ⚠ PDF generation skipped: {e}")
        print("   Install reportlab with: pip install reportlab")
        return
    except Exception as e:
        print(f"   ✗ Error generating report: {e}")
        return
    
    print("\n" + "=" * 80)
    print("PDF report generated successfully!")
    print("=" * 80)
    print("\nReport includes:")
    if use_gemini:
        print("  - AI-generated professional introduction")
        print("  - AI-generated professional conclusion")
        print("  - Enhanced recommendations based on actual data")
    print("  - Metrics analysis with bar charts")
    print("  - Top 10 Categories by Volume (Last 30 Days) - charts and table")
    print("  - Backlog Analysis - Urgent Unresolved Items - charts and table")
    print("\nNote: Product visualizations require CSV files at:")
    print("  - backend/trends/data/top10.csv (for top10_volume_30d)")
    print("  - backend/trends/data/backlog_ranked_list.csv (for backlog_ranked_list)")

if __name__ == "__main__":
    test_pdf()
