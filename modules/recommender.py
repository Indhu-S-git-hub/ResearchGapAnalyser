import json

class ProjectRecommender:
    def __init__(self):
        pass

    def generate_recommendations(self, topic_distribution_json, gaps_json):
        """Cross-references identified domain limitations to suggest innovative project structures."""
        try:
            gaps = json.loads(gaps_json)
            topics = json.loads(topic_distribution_json)
        except Exception:
            gaps = {}
            topics = {"General AI": 1.0}

        # Determine dominant topic string for context framing
        dominant_topic = max(topics, key=topics.get) if topics else "Advanced Machine Learning"
        
        recommendations = []

        # Strategy 1: Resolve Lack of Explainability Gaps
        if gaps.get("lack_of_explainability", {}).get("detected"):
            recommendations.append({
                "title": f"Trustworthy Framework for {dominant_topic} using XAI Models",
                "problem_statement": f"Existing models in {dominant_topic} run as black-boxes, making them unsafe for regulated spaces. This project implements SHAP and LIME architectures to provide pixel/token attribution maps.",
                "suggested_datasets": "Open-source domain-specific benchmark repositories (e.g., Kaggle/UCI).",
                "algorithms": "SHAP (Shapley Additive exPlanations), LIME, Integrated Gradients, Random Forest/XGBoost baseline.",
                "required_skills": "Python, Scikit-Learn, InterpretML, Frontend Dashboarding (Flask/Dash).",
                "difficulty_level": "Advanced",
                "expected_outcomes": "An interactive diagnostic dashboard showcasing traditional model decisions supported by real-time mathematical transparency charts."
            })

        # Strategy 2: Resolve Small Dataset Constraints via Synthetic Generation
        if gaps.get("small_dataset_constraints", {}).get("detected"):
            recommendations.append({
                "title": f"Data-Augmented Pipeline for Optimized {dominant_topic} Systems",
                "problem_statement": f"Progress in {dominant_topic} is bounded tightly by data scarcity and overfitting risks. This system constructs conditional generative data structures to safely augment minority classifications.",
                "suggested_datasets": "Any highly imbalanced or restrictive industry tabular/image group.",
                "algorithms": "SMOTE, Conditional GANs (Generative Adversarial Networks), Variational Autoencoders (VAEs).",
                "required_skills": "PyTorch/TensorFlow, Imbalanced-Learn, Evaluation Metric Management.",
                "difficulty_level": "Expert",
                "expected_outcomes": "A generation pipeline demonstrating an explicit lift in baseline classification accuracy after synthetic injection."
            })

        # Strategy 3: Default Fail-safe recommendation if papers are clean
        if not recommendations:
            recommendations.append({
                "title": f"Edge-Optimized Production Framework for {dominant_topic}",
                "problem_statement": "Academic models prioritize raw mathematical precision at the expense of computational performance, complicating actual hardware deployments.",
                "suggested_datasets": "Standard public validation test-beds.",
                "algorithms": "ONNX Runtime Parsing, Quantization, Pruning, Knowledge Distillation.",
                "required_skills": "Python, TensorRT, Model Profiling Instruments.",
                "difficulty_level": "Medium",
                "expected_outcomes": "A compiled system demonstrating up to a 4x reduction in deployment size with minimal loss in model precision."
            })

        return json.dumps(recommendations)