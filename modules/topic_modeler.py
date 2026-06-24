import json
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

class TopicModeler:
    def __init__(self, n_topics=3):
        self.n_topics = n_topics
        # Vectorizer to convert documents into word count matrices
        self.vectorizer = CountVectorizer(max_df=0.95, min_df=1, stop_words='english')
        # LDA engine
        self.lda = LatentDirichletAllocation(n_components=n_topics, random_state=42, learning_method='online')

    def fit_predict_topics(self, cleaned_texts_list):
        """
        Learns topics from a collection of cleaned papers 
        and extracts the dominant topic configuration for each.
        """
        if not cleaned_texts_list or len(cleaned_texts_list) == 0:
            return []

        # If user uploaded fewer papers than requested topics, adapt dynamically
        actual_topics = min(self.n_topics, len(cleaned_texts_list))
        if actual_topics != self.lda.n_components:
            self.lda = LatentDirichletAllocation(n_components=actual_topics, random_state=42)

        try:
            dtm = self.vectorizer.fit_transform(cleaned_texts_list)
            lda_matrix = self.lda.fit_transform(dtm)
            feature_names = self.vectorizer.get_feature_names_out()
        except Exception as e:
            print(f"Topic modeling training failed: {str(e)}")
            return [{"dominant_topic": "General Research", "distribution": [1.0]}] * len(cleaned_texts_list)

        # Extract top 5 words that represent each topic
        topic_keywords = {}
        for topic_idx, topic in enumerate(self.lda.components_):
            top_keyword_idx = topic.argsort()[:-6:-1]
            keywords = [feature_names[i] for i in top_keyword_idx]
            # Formulate a descriptive topic label from top words
            topic_keywords[topic_idx] = " & ".join(keywords[:2]).title()

        results = []
        for i in range(len(cleaned_texts_list)):
            distribution = lda_matrix[i].tolist()
            dominant_idx = int(np.argmax(distribution))
            
            results.append({
                "dominant_topic": topic_keywords[dominant_idx],
                "distribution": json.dumps({topic_keywords[idx]: float(val) for idx, val in enumerate(distribution)})
            })
            
        return results