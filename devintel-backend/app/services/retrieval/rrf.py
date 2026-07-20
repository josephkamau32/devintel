"""Reciprocal Rank Fusion for combining multiple ranked result lists."""


from app.services.retrieval.bm25_index import ScoredChunk


def reciprocal_rank_fusion(
    ranked_lists: list[list[ScoredChunk]],
    k: int = 60,
) -> list[ScoredChunk]:
    """
    Combine multiple ranked lists using Reciprocal Rank Fusion.

    RRF formula: score(d) = Σ 1 / (k + rank(d, list_i))

    Args:
        ranked_lists: List of ranked result lists (each list already sorted by score)
        k: Constant for rank decay (default 60 per TREC recommendations)

    Returns:
        Fused list sorted by combined score
    """
    # Collect all unique chunks with their fused scores
    scores: dict = {}  # embedding_id -> combined_score
    chunks: dict = {}  # embedding_id -> ScoredChunk (for source tracking)

    for ranked_list in ranked_lists:
        for rank, scored_chunk in enumerate(ranked_list):
            embedding_id = str(scored_chunk.embedding.id)
            rrf_score = 1.0 / (k + rank)

            if embedding_id in scores:
                scores[embedding_id] += rrf_score
            else:
                scores[embedding_id] = rrf_score
                chunks[embedding_id] = scored_chunk

    # Create fused results sorted by score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    results = []

    for embedding_id in sorted_ids:
        scored = chunks[embedding_id]
        # Create a new ScoredChunk with fused score
        fused = ScoredChunk(scored.embedding, scores[embedding_id], "rrf")
        results.append(fused)

    return results
