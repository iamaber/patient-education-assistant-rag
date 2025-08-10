from src.drug_matching.matcher import DrugMatcher
from src.drug_matching.schemas import MatchResult


def test_matcher():
    matcher = DrugMatcher()
    results = matcher.match("Metformin")
    assert len(results) > 0
    for result in results:
        assert isinstance(result, MatchResult)
        assert result.confidence > 0.6
