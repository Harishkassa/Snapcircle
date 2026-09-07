from src.utils import *

# FILE: src/utils/similarity.py (add this function, keep existing cosine_similarity as-is)

def cosine_similarity(embedding_a: list[float], embedding_b: list[float]) -> float:
    a = np.array(embedding_a)
    b = np.array(embedding_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def find_best_match(
    face_embedding: list[float],
    candidates: list[tuple[UUID, list[float]]],  # [(user_id, embedding), ...]
    threshold: float = 0.5,
) -> UUID | None:
    """
    Compares one detected face embedding against all candidate user embeddings.
    Returns the user_id with the highest similarity score IF it crosses threshold,
    else returns None (no match).
    """
    best_user_id = None
    best_score = -1.0  # cosine similarity range is -1 to 1

    for user_id, candidate_embedding in candidates:
        score = cosine_similarity(face_embedding, candidate_embedding)
        if score > best_score:
            best_score = score
            best_user_id = user_id
    
    if best_score >= threshold:
        return best_user_id
    return None