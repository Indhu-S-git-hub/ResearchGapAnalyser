import spacy
import string

class TextPreprocessor:
    def __init__(self):
        # Load the lightweight spaCy model installed during environment setup
        self.nlp = spacy.load("en_core_web_sm")
        
    def clean_text(self, text):
        """
        Converts text to lowercase, handles lemmatization, and filters out 
        punctuation, numbers, and standard English stop words.
        """
        if not text or text == "Not Found":
            return ""
            
        # Optimize processing overhead by disabling unneeded components
        doc = self.nlp(text.lower(), disable=["ner", "parser"])
        
        cleaned_tokens = []
        for token in doc:
            # Eliminate stop words, punctuations, white space tokens, and numerical values
            if not token.is_stop and not token.is_punct and token.text.strip() and not token.like_num:
                # Use base word form (lemmatization)
                lemma = token.lemma_.strip()
                # Secondary sanitization pass to remove weird stray symbols
                lemma = lemma.translate(str.maketrans('', '', string.punctuation))
                if len(lemma) > 2: # Ignore single/double character junk strings
                    cleaned_tokens.append(lemma)
                    
        return " ".join(cleaned_tokens)