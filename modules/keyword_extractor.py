import json
import collections
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy

class KeywordExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def extract_keywords(self, cleaned_text, raw_text, top_n=10):
        """
        Extracts both single keywords and complex keyphrases using 
        a hybrid TF-IDF and Noun-Chunk calculation pipeline.
        """
        if not cleaned_text.strip():
            return json.dumps([])

        # 1. TF-IDF scoring strategy
        vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
        try:
            tfidf_matrix = vectorizer.fit_transform([cleaned_text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            tfidf_keywords = {feature_names[i]: float(scores[i]) for i in range(len(feature_names))}
        except Exception:
            tfidf_keywords = {}

        # 2. Keyphrase structural strategy (pulling technical noun chunks from raw text)
        doc = self.nlp(raw_text[:5000]) # Scan first 15k characters for core context
        noun_chunks = []
        for chunk in doc.noun_chunks:
            clean_chunk = chunk.text.lower().strip()
            # Filter out chunks containing digits, punctuation, or too short
            if len(clean_chunk) > 4 and not chunk.root.is_stop and not any(char.isdigit() for char in clean_chunk):
                noun_chunks.append(clean_chunk)

        chunk_counts = collections.Counter(noun_chunks)
        
        # 3. Combine both strategies
        final_keywords = {}
        # Hydrate base TF-IDF words
        for kw, score in tfidf_keywords.items():
            final_keywords[kw] = score * 10  # Scale multiplier

        # Boost keywords that appear as structural noun chunks
        for chunk, count in chunk_counts.most_common(15):
            if chunk in final_keywords:
                final_keywords[chunk] += count
            else:
                final_keywords[chunk] = float(count * 1.5)

        # Sort and filter out the top requested terms
        sorted_keywords = sorted(final_keywords.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # Format as an array of dictionaries for easy graphing downstream
        output = [{"keyword": kw, "score": round(score, 3)} for kw, score in sorted_keywords]
        return json.dumps(output)