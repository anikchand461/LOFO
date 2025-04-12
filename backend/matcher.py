from sentence_transformers import SentenceTransformer, util
from .owner_data import get_owners_from_db

def get_best_match(description: str) -> dict:
    owners = get_owners_from_db()
    if not owners:
        return {"error": "No owners found in database"}
    
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    desc_embeddings = model.encode([description] + [o['desc'] for o in owners])
    
    similarities = util.cos_sim(desc_embeddings[0], desc_embeddings[1:])
    best_index = similarities.argmax()
    
    best_match = owners[best_index]
    best_match['score'] = float(similarities[0][best_index])
    
    if best_match['score'] < 0.7:
        return {"error": "No good match found"}
    
    return best_match