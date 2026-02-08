"""
CLI script to generate reports from JSON analytics output.
"""

import json
import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from report_generator import ReportGenerator, generate_report_from_json

# Load environment variables
load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description='Generate professional reports from JSON analytics output'
    )
    parser.add_argument(
        'input',
        type=str,
        help='Path to JSON file or JSON string'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        required=True,
        help='Output PDF file path (required)'
    )
    parser.add_argument(
        '-t', '--title',
        type=str,
        help='Custom report title'
    )
    parser.add_argument(
        '-s', '--subtitle',
        type=str,
        help='Custom report subtitle'
    )
    
    args = parser.parse_args()
    
    # Load JSON data
    try:
        # Try to parse as JSON string first
        try:
            data = json.loads(args.input)
        except json.JSONDecodeError:
            # If that fails, try to read from file
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"Error: File '{args.input}' not found", file=sys.stderr)
                sys.exit(1)
            
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate data structure
    required_fields = ['answer', 'rationale', 'key_metrics']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        print(f"Error: Missing required fields: {', '.join(missing_fields)}", file=sys.stderr)
        print("Expected structure: {'answer': str, 'rationale': list, 'key_metrics': list}", file=sys.stderr)
        sys.exit(1)
    
    # Check for Gemini API key
    gemini_api_key = args.gemini_api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    use_gemini = args.use_gemini and bool(gemini_api_key)
    
    if args.use_gemini and not gemini_api_key:
        print("Warning: --use-gemini specified but no API key found. Set GEMINI_API_KEY or use --gemini-api-key", file=sys.stderr)
    
    # Generate PDF report
    generator = ReportGenerator(
        title=args.title or "CRM Analytics Report",
        subtitle=args.subtitle,
        use_gemini=use_gemini,
        gemini_api_key=gemini_api_key
    )
    
    generator.save_report(data, args.output)
    print(f"PDF report generated successfully: {args.output}")
    if use_gemini:
        print("✓ Report includes AI-generated professional introduction and conclusion")


if __name__ == "__main__":
    main()
