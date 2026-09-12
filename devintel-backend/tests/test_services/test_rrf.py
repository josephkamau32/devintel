"""Tests for app.services.retrieval.rrf — reciprocal rank fusion, hand-verified.

RRF formula: score(d) = Σ 1/(k + rank)   where rank is 0-indexed in the code.

Hand computation for default k=60:
  rank 0 → 1/60, rank 1 → 1/61, rank 2 → 1/62, ...
"""

import pytest
from types import SimpleNamespace
from uuid import uuid4

from app.services.retrieval.bm25_index import ScoredChunk
from app.services.retrieval.rrf import reciprocal_rank_fusion


def _make_chunk(file_path: str, eid=None) -> ScoredChunk:
    """Create a ScoredChunk with a fake embedding having a unique id."""
    eid = eid or uuid4()
    emb = SimpleNamespace(id=eid, file_path=file_path)
    return ScoredChunk(emb, score=0.0, source="test")


class TestReciprocalRankFusion:
    def test_single_list(self):
        """Single ranked list — RRF scores should be 1/(k+rank) for each item."""
        a = _make_chunk("a.py", eid="id-a")
        b = _make_chunk("b.py", eid="id-b")
        result = reciprocal_rank_fusion([[a, b]], k=60)

        assert len(result) == 2
        # First item: rank 0 → 1/(60+0) = 1/60
        assert result[0].score == pytest.approx(1 / 60)
        assert result[0].embedding.file_path == "a.py"
        # Second item: rank 1 → 1/(60+1) = 1/61
        assert result[1].score == pytest.approx(1 / 61)

    def test_two_lists_shared_item_gets_summed(self):
        """A chunk appearing in both lists gets both scores summed."""
        shared_id = "shared-id"
        a = _make_chunk("a.py", eid=shared_id)
        b = _make_chunk("b.py", eid="id-b")

        # List 1: [a (rank 0), b (rank 1)]
        # List 2: [a (rank 0)]
        a2 = _make_chunk("a.py", eid=shared_id)  # same ID

        result = reciprocal_rank_fusion([[a, b], [a2]], k=60)

        # 'a' appears in both at rank 0 → 1/60 + 1/60 = 2/60
        a_result = [r for r in result if str(r.embedding.id) == shared_id][0]
        assert a_result.score == pytest.approx(2 / 60)

        # 'b' appears in list 1 only at rank 1 → 1/61
        b_result = [r for r in result if str(r.embedding.id) == "id-b"][0]
        assert b_result.score == pytest.approx(1 / 61)

        # 'a' should rank higher than 'b'
        assert result[0].score > result[1].score

    def test_empty_lists(self):
        """Empty input → empty output."""
        assert reciprocal_rank_fusion([], k=60) == []

    def test_all_empty_sublists(self):
        """All sublists empty → empty output."""
        assert reciprocal_rank_fusion([[], []], k=60) == []

    def test_result_source_is_rrf(self):
        """Fused chunks should have source='rrf'."""
        a = _make_chunk("a.py", eid="id-a")
        result = reciprocal_rank_fusion([[a]], k=60)
        assert result[0].source == "rrf"

    def test_custom_k(self):
        """Different k changes the scores."""
        a = _make_chunk("a.py", eid="id-a")
        result = reciprocal_rank_fusion([[a]], k=10)
        # rank 0, k=10 → 1/10
        assert result[0].score == pytest.approx(1 / 10)

    def test_ordering_is_by_score_descending(self):
        """Items that appear in more lists rank higher."""
        shared_id = "shared"
        only_id = "only"

        result = reciprocal_rank_fusion([
            [_make_chunk("shared.py", eid=shared_id), _make_chunk("only.py", eid=only_id)],
            [_make_chunk("shared.py", eid=shared_id)],
        ], k=60)

        assert str(result[0].embedding.id) == shared_id
        assert str(result[1].embedding.id) == only_id
