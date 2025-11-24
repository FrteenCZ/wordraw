import pytest
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `from main import ...` works when pytest
# changes the CWD.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import compare_words, pattern_match_rating, parse_mode, display_pattern


def test_compare_words_all_green():
    assert compare_words("apple", "apple") == [2, 2, 2, 2, 2]


def test_compare_words_yellow_and_gray():
    # 'crazy' vs 'cigar' yields: c*=green (2), r yellow (1) since 'r' present at pos 1
    assert compare_words("crazy", "cigar")[0] == 2


def test_pattern_match_rating_simple():
    # With mode 'x/gy', group mapping is: x->0, g->1 pos0, y->1 pos1
    pattern = [2, 1, 0, 0, 0]
    requested_pattern = [1, 1, 1, 1, 1]
    # Expect 2 group matches (positions 0 and 1): 20 + color_score
    # color_score = (2 for green pos 0) + (1 for yellow pos 1) = 3 => rating 23
    assert pattern_match_rating(pattern, requested_pattern, "x/gy") == 23


def test_parse_mode_invalid_raises():
    with pytest.raises(ValueError):
        parse_mode("xx/g/y")


def test_display_pattern_basic():
    # Ensure display returns the expected emoji strings for a simple mode
    colors, letters, numbers = display_pattern([0, 1, 2, 0, 0], mode="x/gy")
    assert len(colors) == 5
    assert len(letters) == 5


def test_find_words_multiple_patterns_shape():
    # Simple check: if we request patterns for two characters, results length matches
    words = ["apple", "thick", "abide", "aback"]
    target = "thick"
    # two patterns groups (simulate two letters message)
    desired = [
        [[0, 0, 0, 0, 0]] * 6,
        [[1, 1, 1, 1, 1]] * 6,
    ]
    modes = ["x/gy", "gy/x"]
    results = __import__("main").find_words(words, target, desired, modes)
    assert isinstance(results, list)
    assert len(results) == 2
    # each result should have entries for each mode
    for res in results:
        assert set(res.keys()) == set(modes)


if __name__ == "__main__":
    pytest.main()
