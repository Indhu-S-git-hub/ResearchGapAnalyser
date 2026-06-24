import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SimilarityAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))

    def compute_similarity_matrix(self, cleaned_texts_list, filenames):
        """
        Calculates pairwise cosine similarity metrics across all processed vectors.
        """
        if len(cleaned_texts_list) < 2:
            # If only 1 paper exists, similarity analysis is not applicable
            return json.dumps({"matrix": [[1.0]], "labels": filenames, "recommendations": []})

        try:
            tfidf_matrix = self.vectorizer.fit_transform(cleaned_texts_list)
            sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        except Exception as e:
            print(f"Similarity generation crash: {str(e)}")
            return json.dumps({"matrix": [], "labels": filenames, "recommendations": []})

        # Round values for display
        matrix_list = np.round(sim_matrix, 3).tolist()

        # Build recommendations based on document clusters
        recommendations = []
        for i in range(len(filenames)):
            similar_papers = []
            for j in range(len(filenames)):
                if i != j and matrix_list[i][j] > 0.35: # 35% threshold means strong thematic overlap
                    similar_papers.append({
                        "paper": filenames[j],
                        "score": matrix_list[i][j]
                    })
            
            if similar_papers:
                # Sort descending by correlation strength
                similar_papers = sorted(similar_papers, key=lambda x: x['score'], reverse=True)
                recommendations.append({
                    "base_paper": filenames[i],
                    "cross_references": similar_papers,
                    "insight": f"Highly integrated with {len(similar_papers)} other documents. Check for methodology overlap."
                })

        return json.dumps({
            "matrix": matrix_list,
            "labels": filenames,
            "recommendations": recommendations
        })