import json

class OpportunityRadar:
    def __init__(self):
        pass

    def generate_opportunities(self, topic_distribution_json, gaps_json, similarity_json):
        try:
            gaps = json.loads(gaps_json)
        except Exception:
            gaps = {}

        try:
            topics = json.loads(topic_distribution_json)
        except Exception:
            topics = {}

        try:
            similarity = json.loads(similarity_json)
        except Exception:
            similarity = {"labels": [], "matrix": []}

        title_topic = "Research Opportunity"
        if topics:
            title_topic = max(topics, key=topics.get)

        opportunities = []

        if gaps.get("lack_of_explainability", {}).get("detected"):
            opportunities.append({
                "title": f"Make {title_topic} Models Explainable",
                "description": "Add interpretability layers, visual explainers, or transparent rule-based components to help researchers and engineers trust results.",
                "category": "Explainability",
                "confidence": "High"
            })

        if gaps.get("small_dataset_constraints", {}).get("detected"):
            opportunities.append({
                "title": f"Build a Data Augmentation Pipeline for {title_topic}",
                "description": "Use synthetic generation or augmentation strategies to strengthen performance on scarce, domain-specific samples.",
                "category": "Data Augmentation",
                "confidence": "High"
            })

        if gaps.get("missing_comparisons", {}).get("detected"):
            opportunities.append({
                "title": f"Benchmark {title_topic} Against Competitive Baselines",
                "description": "Add direct comparisons to recent papers and baselines to highlight where your approach outperforms prior work.",
                "category": "Benchmarking",
                "confidence": "Medium"
            })

        if gaps.get("lack_of_real_world_implementation", {}).get("detected"):
            opportunities.append({
                "title": f"Create a Real-World Prototype for {title_topic}",
                "description": "Move beyond simulation by deploying a demo or pilot on real data and measuring practical impact.",
                "category": "Deployment",
                "confidence": "High"
            })

        if gaps.get("computational_overhead", {}).get("detected"):
            opportunities.append({
                "title": f"Optimize {title_topic} for Efficient Inference",
                "description": "Investigate pruning, quantization, or lightweight architectures to make the system faster and cheaper to run.",
                "category": "Optimization",
                "confidence": "Medium"
            })

        if similarity.get("labels") and similarity.get("matrix"):
            labels = similarity["labels"]
            matrix = similarity["matrix"]
            min_score = 101
            min_pair = None
            for i in range(len(matrix)):
                for j in range(i + 1, len(matrix[i])):
                    score = round(matrix[i][j] * 100)
                    if score < min_score:
                        min_score = score
                        min_pair = (labels[i], labels[j])
            if min_pair and min_score < 40:
                opportunities.append({
                    "title": "Fuse Distinct Perspectives into One Novel System",
                    "description": f"The papers '{min_pair[0]}' and '{min_pair[1]}' have low overlap. Combine their strengths to discover a new hybrid research direction.",
                    "category": "Innovation",
                    "confidence": "Medium"
                })

        if not opportunities:
            opportunities.append({
                "title": f"Expand {title_topic} with a Practical Use Case",
                "description": "Even when gaps are not obvious, a strong contribution is to apply the topic to a new industry need or user workflow.",
                "category": "Opportunity",
                "confidence": "Medium"
            })

        return json.dumps(opportunities)
