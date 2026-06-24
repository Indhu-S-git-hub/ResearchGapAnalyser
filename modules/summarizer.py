import re
from collections import Counter
import json

class PaperSummarizer:
    def __init__(self):
        pass

    def _score_sentences(self, sentences, structural_keywords):
        """Scores sentences based on term frequency and matching anchor terms."""
        # Simple word frequency tokenizer
        words = re.findall(r'\w+', " ".join(sentences).lower())
        freq_table = Counter(words)
        max_freq = max(freq_table.values()) if freq_table else 1
        
        # Normalize frequencies
        for word in freq_table:
            freq_table[word] = freq_table[word] / max_freq

        sentence_scores = {}
        for sentence in sentences:
            clean_sentence = sentence.lower()
            # Calculate base frequency score
            score = sum(freq_table[w] for w in re.findall(r'\w+', clean_sentence) if w in freq_table)
            
            # Boost score if sentence contains structural anchors (e.g., "we propose", "dataset")
            for keyword in structural_keywords:
                if keyword in clean_sentence:
                    score += 2.0
            
            sentence_scores[sentence] = score
        return sentence_scores

    def generate_individual_summary(self, raw_text, metadata):
        """Extracts and maps sentences into structured report components."""
        # Clean lines up and chunk into sentences roughly by periods
        sentences = [s.strip() for s in re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', raw_text) if s.strip()]
        
        # Section anchors
        problem_anchors = ["problem", "challenge", "limitation", "existing methods", "however", "motive"]
        method_anchors = ["proposed", "methodology", "framework", "architecture", "algorithm", "we use", "approach"]
        result_anchors = ["results", "accuracy", "performance", "experiment", "evaluation", "shows that", "table"]

        prob_sentences = [s for s in sentences if any(w in s.lower() for w in problem_anchors)]
        method_sentences = [s for s in sentences if any(w in s.lower() for w in method_anchors)]
        result_sentences = [s for s in sentences if any(w in s.lower() for w in result_anchors)]

        # Score and extract top sentences for each section
        prob_scores = self._score_sentences(prob_sentences[:50], problem_anchors) # Look at earlier segments
        method_scores = self._score_sentences(method_sentences, method_anchors)
        result_scores = self._score_sentences(result_sentences, result_anchors)

        summary_dict = {
            "title": metadata.get("title", "Unknown"),
            "problem_statement": " ".join(sorted(prob_scores, key=prob_scores.get, reverse=True)[:2]) or "See Abstract.",
            "methodology": " ".join(sorted(method_scores, key=method_scores.get, reverse=True)[:3]) or "Refer to body text.",
            "dataset_and_algorithms": " ".join([s for s in method_sentences if "data" in s.lower() or "algorithm" in s.lower()][:2]) or "Not explicitly isolated.",
            "results": " ".join(sorted(result_scores, key=result_scores.get, reverse=True)[:2]) or "Refer to performance section.",
            "conclusion": metadata.get("conclusion", "Refer to full paper text.")[:1000]
        }
        
        return json.dumps(summary_dict)

    def generate_combined_summary(self, list_of_summary_jsons):
        """Aggregates individual summaries into a structural overview of the domain."""
        combined = []
        for i, idx_json in enumerate(list_of_summary_jsons):
            try:
                data = json.loads(idx_json)
                combined.append(f"Paper {i+1} [{data.get('title', 'Untitled')}]:\n- Focus: {data.get('problem_statement')}\n- Strategy: {data.get('methodology')}\n")
            except Exception:
                continue
        return "\n".join(combined) if combined else "No valid summaries found."