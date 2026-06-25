import spacy
import string

class TextPreprocessor:
    def __init__(self):
        # Load only the components needed for lemmatization
        self.nlp = spacy.load(
            "en_core_web_sm",
            disable=["parser", "ner", "textcat"]
        )

    def clean_text(self, text):
        """
        Clean and lemmatize text while minimizing memory usage.
        """

        if not text or text == "Not Found":
            return ""

        # Safety limit for Render free instance
        text = text[:20000].lower()

        cleaned_tokens = []

        # Process in small batches to reduce RAM usage
        for doc in self.nlp.pipe([text], batch_size=1):

            for token in doc:

                if (
                    token.is_stop
                    or token.is_punct
                    or token.like_num
                    or token.is_space
                ):
                    continue

                lemma = token.lemma_.translate(
                    str.maketrans("", "", string.punctuation)
                ).strip()

                if len(lemma) > 2:
                    cleaned_tokens.append(lemma)

        return " ".join(cleaned_tokens)