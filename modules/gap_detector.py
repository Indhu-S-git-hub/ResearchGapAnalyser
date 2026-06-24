import json
import re

class ResearchGapDetector:
    def __init__(self):
        # Specific heuristic dictionaries to scan for engineering and methodology gaps
        self.gap_indicators = {
            "lack_of_explainability": [
                "black box", "lack of transparency", "explainability", "interpretability", 
                "hard to interpret", "lime", "shap", "opaque"
            ],
            "small_dataset_constraints": [
                "small dataset", "limited samples", "data scarcity", "few-shot", 
                "overfitting risk", "lack of data", "small sample size"
            ],
            "missing_comparisons": [
                "not compared with", "omitted baseline", "future work will compare", 
                "lack of benchmarking", "alternative architectures were not"
            ],
            "computational_overhead": [
                "high latency", "computationally expensive", "resource intensive", 
                "gpu limitation", "training time", "heavy computational"
            ],
            "lack_of_real_world_implementation": [
                "synthetic data", "simulation only", "not deployed", "real-world scenario", 
                "controlled environment", "production deployment"
            ]
        }

    def detect_gaps(self, raw_text, summary_json):
        """Scans raw and summarized text matrices to isolate domain limitations."""
        text_lower = raw_text.lower()
        found_gaps = {}
        
        try:
            summary_data = json.loads(summary_json)
            # Inject summary text directly into scope to increase scanning surface area
            text_lower += " " + summary_data.get("methodology", "").lower()
            text_lower += " " + summary_data.get("conclusion", "").lower()
        except Exception:
            pass

        # Evaluate token footprint weights
        for gap_category, keywords in self.gap_indicators.items():
            matches = []
            for kw in keywords:
                # Use regex to track exact phrase components
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    matches.append(kw)
            
            if matches:
                # Calculate basic confidence score based on indicator saturation
                found_gaps[gap_category] = {
                    "detected": True,
                    "evidence_indicators": matches,
                    "severity": "High" if len(matches) > 1 else "Medium"
                }
            else:
                found_gaps[gap_category] = {
                    "detected": False,
                    "evidence_indicators": [],
                    "severity": "Low"
                }

        return json.dumps(found_gaps)