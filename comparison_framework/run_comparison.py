#!/usr/bin/env python3
"""
Main script to run the comparison framework.

Usage:
    python run_comparison.py [--max-circuits N] [--output-dir DIR]
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)

from comparison_runner import ComparisonRunner
from comparison_analyzer import ComparisonAnalyzer


def main():
    parser = argparse.ArgumentParser(description='Run Qiskit vs XMLProgrammer comparison')
    parser.add_argument('--max-circuits', type=int, default=15,
                       help='Maximum number of circuits to test (default: 15)')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory for results (default: comparison_framework/results)')
    parser.add_argument('--analyze-only', type=str, default=None,
                       help='Only analyze existing results file (path to comparison_results.json)')
    
    args = parser.parse_args()
    
    if args.analyze_only:
        # Only analyze existing results
        analyzer = ComparisonAnalyzer(args.analyze_only)
        analysis = analyzer.analyze_all()
        
        results_dir = Path(args.analyze_only).parent
        analyzer.generate_json_report(str(results_dir / "comparison_report.json"))
        analyzer.generate_html_report(str(results_dir / "comparison_report.html"))
        
        print("\n" + "="*60)
        print("Analysis Complete!")
        print("="*60)
        print(f"\nSummary:")
        print(f"  Total Circuits: {analysis['summary']['total_circuits']}")
        print(f"  Both Passed: {analysis['summary']['both_passed']}")
        print(f"  Both Failed: {analysis['summary']['both_failed']}")
        print(f"  Qiskit Only Passed: {analysis['summary']['qiskit_only_passed']}")
        print(f"  XMLProgrammer Only Passed: {analysis['summary']['xmlprogrammer_only_passed']}")
        print(f"  Discrepancies: {analysis['summary']['discrepancies']}")
        print(f"\nReports generated in: {results_dir}")
        return
    
    # Run comparison
    print("="*60)
    print("Qiskit vs XMLProgrammer Comparison Framework")
    print("="*60)
    
    runner = ComparisonRunner()
    
    print(f"\nSelecting subset of circuits (max: {args.max_circuits})...")
    results = runner.run_comparison(max_circuits=args.max_circuits)
    
    # Save raw results
    output_dir = Path(args.output_dir) if args.output_dir else runner.results_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = output_dir / "comparison_results.json"
    runner.save_results(results, str(results_file))
    
    # Analyze results
    print("\nAnalyzing results...")
    analyzer = ComparisonAnalyzer(str(results_file))
    analysis = analyzer.analyze_all()
    
    # Generate reports
    analyzer.generate_json_report(str(output_dir / "comparison_report.json"))
    analyzer.generate_html_report(str(output_dir / "comparison_report.html"))
    
    # Print summary
    print("\n" + "="*60)
    print("Comparison Complete!")
    print("="*60)
    print(f"\nSummary:")
    print(f"  Total Circuits Tested: {analysis['summary']['total_circuits']}")
    print(f"  Both Passed: {analysis['summary']['both_passed']}")
    print(f"  Both Failed: {analysis['summary']['both_failed']}")
    print(f"  Qiskit Only Passed: {analysis['summary']['qiskit_only_passed']}")
    print(f"  XMLProgrammer Only Passed: {analysis['summary']['xmlprogrammer_only_passed']}")
    print(f"  Discrepancies: {analysis['summary']['discrepancies']}")
    print(f"\nStatistics:")
    print(f"  Qiskit Success Rate: {analysis['statistics']['success_rate_qiskit']:.2%}")
    print(f"  XMLProgrammer Success Rate: {analysis['statistics']['success_rate_xmlprogrammer']:.2%}")
    print(f"  Agreement Rate: {analysis['statistics']['agreement_rate']:.2%}")
    print(f"\nReports generated in: {output_dir}")
    print(f"  - comparison_results.json (raw results)")
    print(f"  - comparison_report.json (analysis)")
    print(f"  - comparison_report.html (HTML report)")


if __name__ == "__main__":
    main()











