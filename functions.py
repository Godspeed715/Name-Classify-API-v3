import spacy
import pycountry as py
import sys
import os
import logging

logger = logging.getLogger(__name__)

# Global variables for lazy loading
nlp = None
ruler = None

def initialize_spacy_model():
    """
    Initialize spacy model on first use (lazy loading).
    This is necessary for Vercel serverless deployment.
    
    Returns:
        bool: True if model loaded successfully, False if unavailable
    """
    global nlp, ruler
    
    if nlp is not None:
        return True  # Already initialized
    
    try:
        nlp = spacy.load("en_core_web_sm")
        logger.info("✅ Successfully loaded spacy model")
        return True
    except OSError as e:
        logger.warning(
            f"⚠️  Spacy model 'en_core_web_sm' not found: {e}\n"
            "For local development, run: python -m spacy download en_core_web_sm\n"
            "NLP search features will not be available."
        )
        return False
    
    # Add an EntityRuler to the pipeline
    
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    
    
    # Define and add patterns
    patterns = [
        # Equal To (Exact Matches)
        {"label": "AGE_GROUP", "pattern": [{"LOWER": "young"}], "id": "young"},
        {'label': 'AGE_GROUP', 'pattern': [{'LEMMA': 'teenager'}], 'id': 'teen'},
        {'label': 'AGE_GROUP', 'pattern': [{'LEMMA': 'child'}], 'id': 'child'},
        {'label': 'AGE_GROUP', 'pattern': [{'LEMMA': 'adult'}], 'id': 'adult'},
        {'label': 'AGE_GROUP', 'pattern': [{'LEMMA': 'senior'}], 'id': 'senior'},

        {'label': 'YOUNG', 'pattern': [{'LOWER': 'young'}], 'id': 'young'},

        {"label": "GENDER", "pattern": [{"LEMMA": 'male'}], "id": "male"},
        {"label": "GENDER", "pattern": [{"LEMMA": 'female'}], "id": "female"},
        # To handle both males and females
        {
            "label": "TARGET",
            "pattern": [
                {"LEMMA": "male"},
                {"IS_ALPHA": True, "OP": "*"}, # Catches any random words in between
                {"LEMMA": "female"}
            ]
        },

        # Greater Than / Less Than (Ranges)
        {
            "label": "MIN_AGE",
            "pattern": [{"LOWER": {"IN": ["above", "over", "older"]}}, {"LOWER": "than", "OP": "?"}, {"IS_DIGIT": True}]
        },
        {
            "label": "MAX_AGE",
            "pattern": [{"LOWER": {"IN": ["under", "below", "younger"]}}, {"LOWER": "than", "OP": "?"}, {"IS_DIGIT": True}]
        },

        # Sorting & Ordering
        # Note: You can add more "id" values for other columns like "name", "date", etc.
        {"label": "SORT_BY", "pattern": [{"LOWER": "sort"}, {"LOWER": "by", "OP": "?"}, {"LOWER": "age"}], "id": "age"},
        {"label": "ORDER", "pattern": [{"LOWER": {"IN": ["asc", "ascending", "oldest"]}}], "id": "asc"},
        {"label": "ORDER_BY", "pattern": [{"LOWER": {"IN": ["desc", "descending", "newest"]}}], "id": "desc"},

        # Pagination & Limits
        {"label": "LIMIT", "pattern": [{"LOWER": {"IN": ["top", "limit", "max"]}}, {"IS_DIGIT": True}]},
        {"label": "PAGE", "pattern": [{"LOWER": "page"}, {"IS_DIGIT": True}]}
    ]
    
    # Generate rules programmatically using pycountry
    country_patterns = []
    for country in py.countries:
        # Add the official name (e.g., "Nigeria" -> "NG")
        country_patterns.append({
            "label": "COUNTRY_ID",
            "pattern": [{"LEMMA": country.name.lower()}, {'IS_ALPHA': True, 'OP':'*'}],
            "id": country.alpha_2
        })
    
    ruler.add_patterns(patterns)
    ruler.add_patterns(country_patterns)

def extract_query_params(text):
    """Parses natural language and returns a dictionary of parameters.
    
    Returns None if spacy model is not available.
    """
    # Initialize spacy model on first use
    if not initialize_spacy_model():
        logger.warning("Spacy model unavailable, cannot parse natural language query")
        return None
    initialize_spacy_model()
    doc = nlp(text)
    params = {}

    # 4. Iterate through found entities and build the dictionary
    for ent in doc.ents:
        if ent.label_ == 'TARGET':
            pass
        # Only process the labels we explicitly defined
        if ent.label_ in ["AGE_GROUP", "GENDER", "COUNTRY_ID", 'MIN_AGE', 'MAX_AGE','SORT_BY', 'ORDER', 'LIMIT', 'PAGE']:
            # Lowercase the label to create the dictionary key (e.g., COUNTRY_ID -> country_id)
            params[ent.label_.lower()] = ent.ent_id_

        if ent.label_ in ['MIN_AGE', 'MAX_AGE','LIMIT', 'PAGE']:
            for token in ent:
                if token.is_digit:
                    params[ent.label_.lower()] = int(token.text)

        if ent.label_ == 'YOUNG':
            params['min_age'] = 16
            params['max_age'] = 24

    return params


def arrange_response(response):
    data = []
    for profile in response:
        data.append({
            'id': str(profile[0]),
            'name': profile[1],
            'gender': profile[2],
            'gender_probability': float(profile[3]),
            'age': profile[4],
            'age_group': profile[5],
            'country_id': profile[6],
            'country_name': profile[7],
            'country_probability': float(profile[8]),
            'created_at': profile[9]
        })


    return data


