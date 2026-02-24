#!/usr/bin/env python3
"""
Comparison Analyzer - Analyzes and compares results from both pipelines.

This module:
1. Compares state vectors (for small circuits)
2. Compares measurement probabilities
3. Identifies discrepancies
4. Generates comparison reports (JSON and HTML)
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime


class ComparisonAnalyzer:
    """Analyzes comparison results and generates reports."""
    
    def __init__(self, results_file: str):
        with open(results_file, 'r') as f:
            self.results = json.load(f)
        self.analysis = {
            "summary": {},
            "detailed_comparisons": [],
            "discrepancies": [],
            "statistics": {}
        }
    
    def compare_state_vectors(self, qiskit_sv: List[complex], xmlprogrammer_state: Dict) -> Dict[str, Any]:
        """
        Compare state vectors from both pipelines.
        
        Note: XMLProgrammer state format is different, so we may need to extract
        what we can from the state representation.
        """
        comparison = {
            "comparable": False,
            "match": False,
            "difference": None,
            "note": None
        }
        
        if qiskit_sv is None or len(qiskit_sv) == 0:
            comparison["note"] = "No Qiskit state vector available"
            return comparison
        
        # XMLProgrammer state is in a different format (register-based)
        # For now, we note that direct comparison is not straightforward
        comparison["comparable"] = True
        comparison["note"] = "State vector comparison requires format conversion"
        comparison["qiskit_statevector_size"] = len(qiskit_sv)
        
        return comparison
    
    def compare_measurement_probabilities(self, qiskit_counts: Dict[str, int], 
                                         qiskit_probs: List[float] = None) -> Dict[str, Any]:
        """Compare measurement probabilities."""
        comparison = {
            "comparable": False,
            "match": False,
            "difference": None,
            "note": None
        }
        
        if qiskit_counts is None:
            comparison["note"] = "No Qiskit measurement counts available"
            return comparison
        
        # For now, we document what's available
        comparison["comparable"] = True
        comparison["qiskit_counts"] = qiskit_counts
        comparison["num_measurements"] = len(qiskit_counts)
        
        if qiskit_probs is not None:
            comparison["qiskit_probabilities"] = qiskit_probs
        
        return comparison
    
    def analyze_single_comparison(self, comparison_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single circuit comparison."""
        qiskit_result = comparison_result.get("qiskit_result", {})
        xmlprogrammer_result = comparison_result.get("xmlprogrammer_result", {})
        
        analysis = {
            "circuit_name": comparison_result["circuit_info"].get("class_name"),
            "qiskit_status": qiskit_result.get("status", "UNKNOWN"),
            "xmlprogrammer_status": xmlprogrammer_result.get("status", "UNKNOWN"),
            "both_passed": False,
            "both_failed": False,
            "discrepancy": False,
            "state_vector_comparison": None,
            "measurement_comparison": None,
            "circuit_properties_match": False,
            "notes": []
        }
        
        # Check if both passed
        qiskit_passed = qiskit_result.get("status") in ["PASSED", "PARTIAL"]
        xmlprogrammer_passed = xmlprogrammer_result.get("status") == "PASSED"
        
        analysis["both_passed"] = qiskit_passed and xmlprogrammer_passed
        analysis["both_failed"] = not qiskit_passed and not xmlprogrammer_passed
        
        # Check for discrepancies
        if qiskit_passed != xmlprogrammer_passed:
            analysis["discrepancy"] = True
            if qiskit_passed and not xmlprogrammer_passed:
                analysis["notes"].append("Qiskit passed but XMLProgrammer failed")
            else:
                analysis["notes"].append("XMLProgrammer passed but Qiskit failed")
        
        # Compare circuit properties
        qiskit_props = qiskit_result.get("circuit_properties", {})
        xmlprogrammer_props = xmlprogrammer_result.get("circuit_properties", {})
        
        if qiskit_props and xmlprogrammer_props:
            props_match = (
                qiskit_props.get("num_qubits") == xmlprogrammer_props.get("num_qubits") and
                qiskit_props.get("num_clbits") == xmlprogrammer_props.get("num_clbits")
            )
            analysis["circuit_properties_match"] = props_match
            if not props_match:
                analysis["notes"].append("Circuit properties mismatch")
        
        # Compare state vectors (if available)
        if analysis["both_passed"]:
            qiskit_sv = qiskit_result.get("statevector_sim", {})
            if qiskit_sv and qiskit_sv.get("success"):
                sv_array = qiskit_sv.get("statevector_array")
                if sv_array:
                    analysis["state_vector_comparison"] = self.compare_state_vectors(
                        sv_array, xmlprogrammer_result.get("simulation", {}).get("state")
                    )
            
            # Compare measurements
            qiskit_meas = qiskit_result.get("measurement_sim", {})
            if qiskit_meas and qiskit_meas.get("success"):
                counts = qiskit_meas.get("counts")
                probs = qiskit_result.get("statevector_sim", {}).get("probabilities")
                analysis["measurement_comparison"] = self.compare_measurement_probabilities(
                    counts, probs
                )
        
        return analysis
    
    def analyze_all(self) -> Dict[str, Any]:
        """Analyze all comparison results."""
        results = self.results.get("results", [])
        
        summary = {
            "total_circuits": len(results),
            "both_passed": 0,
            "both_failed": 0,
            "qiskit_only_passed": 0,
            "xmlprogrammer_only_passed": 0,
            "discrepancies": 0
        }
        
        detailed_comparisons = []
        discrepancies = []
        
        for result in results:
            analysis = self.analyze_single_comparison(result)
            detailed_comparisons.append(analysis)
            
            # Update summary
            if analysis["both_passed"]:
                summary["both_passed"] += 1
            elif analysis["both_failed"]:
                summary["both_failed"] += 1
            elif analysis["qiskit_status"] in ["PASSED", "PARTIAL"]:
                summary["qiskit_only_passed"] += 1
            elif analysis["xmlprogrammer_status"] == "PASSED":
                summary["xmlprogrammer_only_passed"] += 1
            
            if analysis["discrepancy"]:
                summary["discrepancies"] += 1
                discrepancies.append({
                    "circuit": analysis["circuit_name"],
                    "qiskit_status": analysis["qiskit_status"],
                    "xmlprogrammer_status": analysis["xmlprogrammer_status"],
                    "notes": analysis["notes"]
                })
        
        self.analysis["summary"] = summary
        self.analysis["detailed_comparisons"] = detailed_comparisons
        self.analysis["discrepancies"] = discrepancies
        
        # Calculate statistics
        self.analysis["statistics"] = {
            "success_rate_qiskit": (summary["both_passed"] + summary["qiskit_only_passed"]) / summary["total_circuits"] if summary["total_circuits"] > 0 else 0,
            "success_rate_xmlprogrammer": (summary["both_passed"] + summary["xmlprogrammer_only_passed"]) / summary["total_circuits"] if summary["total_circuits"] > 0 else 0,
            "agreement_rate": summary["both_passed"] / summary["total_circuits"] if summary["total_circuits"] > 0 else 0
        }
        
        return self.analysis
    
    def generate_json_report(self, output_file: str):
        """Generate JSON report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.analysis["summary"],
            "statistics": self.analysis["statistics"],
            "discrepancies": self.analysis["discrepancies"],
            "detailed_comparisons": self.analysis["detailed_comparisons"]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
    
    def generate_html_report(self, output_file: str):
        """Generate HTML report."""
        summary = self.analysis["summary"]
        stats = self.analysis["statistics"]
        discrepancies = self.analysis["discrepancies"]
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Qiskit vs XMLProgrammer Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .discrepancy {{ background-color: #ffe7e7; padding: 10px; margin: 10px 0; border-left: 4px solid #ff4444; }}
        .success {{ color: #4CAF50; font-weight: bold; }}
        .failure {{ color: #f44336; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Qiskit vs XMLProgrammer Comparison Report</h1>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Circuits Tested:</strong> {summary['total_circuits']}</p>
        <p><strong>Both Passed:</strong> <span class="success">{summary['both_passed']}</span></p>
        <p><strong>Both Failed:</strong> <span class="failure">{summary['both_failed']}</span></p>
        <p><strong>Qiskit Only Passed:</strong> {summary['qiskit_only_passed']}</p>
        <p><strong>XMLProgrammer Only Passed:</strong> {summary['xmlprogrammer_only_passed']}</p>
        <p><strong>Discrepancies:</strong> <span class="failure">{summary['discrepancies']}</span></p>
    </div>
    
    <div class="summary">
        <h2>Statistics</h2>
        <p><strong>Qiskit Success Rate:</strong> {stats['success_rate_qiskit']:.2%}</p>
        <p><strong>XMLProgrammer Success Rate:</strong> {stats['success_rate_xmlprogrammer']:.2%}</p>
        <p><strong>Agreement Rate:</strong> {stats['agreement_rate']:.2%}</p>
    </div>
    
    <h2>Discrepancies</h2>
"""
        
        if discrepancies:
            for disc in discrepancies:
                html += f"""
    <div class="discrepancy">
        <strong>{disc['circuit']}</strong><br>
        Qiskit: <span class="{'success' if disc['qiskit_status'] in ['PASSED', 'PARTIAL'] else 'failure'}">{disc['qiskit_status']}</span> | 
        XMLProgrammer: <span class="{'success' if disc['xmlprogrammer_status'] == 'PASSED' else 'failure'}">{disc['xmlprogrammer_status']}</span><br>
        Notes: {', '.join(disc['notes'])}
    </div>
"""
        else:
            html += "<p>No discrepancies found.</p>"
        
        html += """
    <h2>Detailed Comparisons</h2>
    <table>
        <tr>
            <th>Circuit</th>
            <th>Qiskit Status</th>
            <th>XMLProgrammer Status</th>
            <th>Both Passed</th>
            <th>Notes</th>
        </tr>
"""
        
        for comp in self.analysis["detailed_comparisons"]:
            qiskit_status_class = "success" if comp["qiskit_status"] in ["PASSED", "PARTIAL"] else "failure"
            xml_status_class = "success" if comp["xmlprogrammer_status"] == "PASSED" else "failure"
            both_passed = "✓" if comp["both_passed"] else "✗"
            
            html += f"""
        <tr>
            <td>{comp['circuit_name']}</td>
            <td class="{qiskit_status_class}">{comp['qiskit_status']}</td>
            <td class="{xml_status_class}">{comp['xmlprogrammer_status']}</td>
            <td>{both_passed}</td>
            <td>{', '.join(comp['notes']) if comp['notes'] else 'None'}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python comparison_analyzer.py <comparison_results.json>")
        sys.exit(1)
    
    analyzer = ComparisonAnalyzer(sys.argv[1])
    analysis = analyzer.analyze_all()
    
    # Generate reports
    results_dir = Path(sys.argv[1]).parent
    analyzer.generate_json_report(str(results_dir / "comparison_report.json"))
    analyzer.generate_html_report(str(results_dir / "comparison_report.html"))
    
    print("Analysis complete!")
    print(f"Summary: {analysis['summary']}")
    print(f"Reports generated in {results_dir}")











