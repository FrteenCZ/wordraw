"""wordraw

Utilities to find Wordle guesses that match a visual pattern.

This module contains helpers to compare two 5-letter words using Wordle
coloring rules, rate how closely a guess matches a requested pattern,
search a wordlist for best candidates, and render the results as text or
as a small matplotlib plot.

Improvements made:
- Added typed function signatures and module docstring
- Split complex logic into small, documented helper functions
- Added a small CLI entrypoint for convenience
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Iterable

import json
import re
import matplotlib.pyplot as plt
import numpy as np

def compare_words(guess: str, target: str) -> List[int]:
    """Return Wordle-style pattern comparing a guess to a target.

    The returned list contains five integers:
    - 2: letter is correct and in the correct position (green)
    - 1: letter exists in the target but in another position (yellow)
    - 0: letter does not exist in the target (gray)

    The function follows the Wordle convention where greens are first
    scored and then available letters are used to mark yellows.
    """

    if not (isinstance(guess, str) and isinstance(target, str)):
        raise TypeError("guess and target must be strings")

    guess = list(guess.lower())
    target_chars = list(target.lower())
    if not (len(guess) == len(target_chars) == 5):
        raise ValueError("guess and target must be 5-letter words")

    result: List[int] = [0] * 5
    pending_yellow_indices: List[int] = []

    # First assign greens and remove them from consideration
    for i in range(5):
        if guess[i] == target_chars[i]:
            result[i] = 2
            target_chars[i] = "\0"  # mark used
        elif guess[i] in target_chars:
            # mark as a yellow candidate, finalize later to avoid double-counting
            pending_yellow_indices.append(i)

    # Now finalize yellows based on remaining unconsumed letters in target
    for i in pending_yellow_indices:
        if guess[i] in target_chars:
            result[i] = 1
            target_chars[target_chars.index(guess[i])] = "\0"

    return result


def parse_mode(mode: str) -> Dict[int, Tuple[int, int]]:
    """Parse a short mode string like 'x/gy' and return mapping.

    The returned dict maps color code index (0=x, 1=y, 2=g) to a tuple:
    (group_index, position_in_group).

    For example, 'x/gy' results in:
    - x -> (0, 0)
    - g -> (1, 0)
    - y -> (1, 1)
    """

    # Validate the provided mode string using the same rules as before
    if not re.match(r'^(?!.*([xgy]).*\1)(?:[xgy]{3}|[xgy]{2}/[xgy]|[xgy]/[xgy]{2}|[xgy]/[xgy]/[xgy])$', mode):
        raise ValueError(f"Invalid mode string: {mode!r}")

    groups = mode.split('/')
    mapping: Dict[int, Tuple[int, int]] = {}
    color_to_index = {'x': 0, 'y': 1, 'g': 2}

    for group_index, group in enumerate(groups):
        for color_index, color in enumerate(group):
            mapping[color_to_index[color]] = (group_index, color_index)

    return mapping


def pattern_match_rating(pattern: List[int], requested_pattern: List[int], mode: str = "x/gy") -> int:
    """Rate how well a pattern (0/1/2 values) matches a requested pattern.

    The requested_pattern should be a list of integers (group indices)
    that describe visually in which group a given position should be.
    The rating uses two components:
    - group_match gives 10 points per position where the color group matches
    - color_match adds a small value depending on where the color appears in
      the mode's group ordering so that positions in earlier parts of a group
      score slightly higher.
    """

    parsed = parse_mode(mode)
    if len(pattern) != 5 or len(requested_pattern) != 5:
        raise ValueError("Both pattern and requested_pattern must be of length 5")

    group_score = 0
    color_score = 0
    for p, rp in zip(pattern, requested_pattern):
        if p not in (0, 1, 2):
            raise ValueError("pattern values must be 0/1/2")
        group_index, color_pos = parsed[p]
        if rp not in (0, 1, 2):
            raise ValueError("requested_pattern values must be 0/1/2 indicating group index")
        if group_index == rp:
            group_score += 1
            # color_pos is 0 (best) .. n (worse). We invert this to give
            # higher points for earlier positions in the group.
            color_score += max(0, 2 - color_pos)

    return group_score * 10 + color_score


@dataclass
class ModeResult:
    """Hold search results for a mode across 6 rounds.

    candidates: candidates[i] is the list of best-matching words for round i
    ratings: ratings[i] is the numeric rating assigned for the best candidate(s)
    """

    candidates: List[List[str]]
    ratings: List[int]


def find_words(word_list: Iterable[str], target_word: str, desired_patterns: List[List[List[int]]], modes: List[str] = ["x/gy"]) -> List[Dict[str, ModeResult]]:
    """Search the word_list for suitable candidate words for each desired pattern.

    Args:
        word_list: iterable of lowercase 5-letter words
        target_word: the 5-letter target word to compare against
        desired_patterns: a list of groups, where each group is a list of 6
                          patterns (one per round) with values 0/1/2
        modes: mode strings describing how to interpret pattern groups

    Returns:
        A list (one entry per desired pattern) containing dicts keyed by mode
        and values with a ModeResult holding candidates and ratings for
        rounds 0..5.
    """

    # Create result structure
    results: List[Dict[str, ModeResult]] = []
    for _ in desired_patterns:
        results.append({})
        for mode in modes:
            results[-1][mode] = ModeResult(candidates=[[] for _ in range(6)], ratings=[0] * 6)

    for word in word_list:
        word = word.strip().lower()
        if not word:
            continue
        if len(word) != 5:
            continue

        pattern = compare_words(word, target_word)
        # iterate rounds 0..5
        for round_index in range(6):
            # Avoid winning the game before the last round, i.e. don't suggest the
            # exact target as a candidate for earlier rounds.
            if word == target_word and round_index != 5:
                continue

            for pattern_index, desired_pattern in enumerate(desired_patterns):
                for mode in modes:
                    rating = pattern_match_rating(pattern, desired_pattern[round_index], mode)
                    mode_result = results[pattern_index][mode]
                    if rating > mode_result.ratings[round_index]:
                        mode_result.ratings[round_index] = rating
                        mode_result.candidates[round_index] = [word]
                    elif rating == mode_result.ratings[round_index]:
                        mode_result.candidates[round_index].append(word)

    return results


def sort_modes(results: List[Dict[str, ModeResult]]) -> Tuple[List[str], Dict[str, int]]:
    """Sort modes by the sum of ratings across desired patterns.

    Returns a list of mode strings ordered by score (descending) and a
    mapping of mode->total rating.
    """

    mode_ratings: Dict[str, int] = {}
    for result in results:
        for mode, mode_result in result.items():
            mode_ratings[mode] = mode_ratings.get(mode, 0) + sum(mode_result.ratings)

    sorted_items = sorted(mode_ratings.items(), key=lambda x: x[1], reverse=True)
    return [mode for mode, _ in sorted_items], mode_ratings


def display_pattern(pattern: List[int], mode: str = "x/y/g") -> Tuple[str, str, str]:
    """Return textual representation for a pattern using a mode ordering.

    The return tuple contains three strings (colors, letters, numbers) which
    are used by `print_result` for nice output.
    """

    symbol_by_color = {"g": "🟩", "y": "🟨", "x": "⬜"}
    letter_by_color = {"g": "G", "y": "Y", "x": "X"}
    number_by_color = {"g": "2", "y": "1", "x": "0"}

    # Use parse_mode to safely determine which group defines each color
    groups = mode.split('/')
    parsed = parse_mode(mode)
    colors = []
    letters = []
    numbers = []
    for c in pattern:
        group_idx, pos_in_group = parsed[c]
        group = groups[group_idx]
        # Retrieve the color character from that group's position
        color_char = group[pos_in_group]
        colors.append(symbol_by_color[color_char])
        letters.append(letter_by_color[color_char])
        numbers.append(number_by_color[color_char])

    return "".join(colors), "".join(letters), "".join(numbers)


def print_result(results: List[Dict[str, ModeResult]], desired_patterns: List[List[List[int]]], target_word: str, modes: List[str] = ["x/gy"], mode_ratings: Dict[str, int] = {}, num_of_candidates: int = 1) -> None:
    """Print a textual overview of the best candidates for each mode/round.

    Each desired pattern is printed along with the top candidate for the
    corresponding round; the `num_of_candidates` argument controls how many
    equal-best candidates are shown.
    """

    for mode in modes:
        print(f"Mode: {mode} (Total Rating: {mode_ratings.get(mode, 0)})")
        for result, desired_pattern in zip(results, desired_patterns):
            for round_index in range(6):
                colors, letters, numbers = display_pattern(desired_pattern[round_index], mode)
                candidates = result[mode].candidates[round_index]
                if candidates:
                    newcolors, newletters, newnumbers = display_pattern(compare_words(candidates[0], target_word))
                else:
                    newcolors, newletters, newnumbers = ("", "", "")
                rating = result[mode].ratings[round_index]
                print(f"Pattern {round_index+1}: {colors} ({letters}, {numbers}) -> {newcolors} ({newletters}, {newnumbers}) Rating: {rating}, Candidates: {candidates[:num_of_candidates]}")
            print()
        print("--------------------------------")


def plot_result(result: Dict[str, ModeResult], target_word: str, modes: List[str] = ["x/gy"], mode_ratings: Dict[str, int] = {}) -> None:
    # support both single-dict and list-of-dicts results
    results_list = result if isinstance(result, list) else [result]
    n_patterns = len(results_list)
    n_modes = len(modes)
    if n_modes == 0 or n_patterns == 0:
        return

    fig, axes = plt.subplots(nrows=n_modes, ncols=n_patterns,
                             figsize=(2 * n_patterns + 2, 2 * n_modes))
    # normalize axes to 2D array with shape (n_modes, n_patterns)
    axes = np.atleast_2d(axes)
    axes = axes.reshape((n_modes, n_patterns))

    # leave room at left for the mode labels
    fig.subplots_adjust(left=0.18, right=0.98, top=0.95,
                        bottom=0.03, wspace=0.2, hspace=0.4)

    for r, mode in enumerate(modes):
        for c, res in enumerate(results_list):
            ax = axes[r, c]
            # default everything to gray so empty candidates still show a board
            image = np.zeros((6, 5, 3), dtype=np.uint8)
            image[:] = [63, 63, 64]

            # fill colored squares using best candidate for each round i
            for i in range(6):
                mode_res = res.get(mode)
                if isinstance(mode_res, ModeResult):
                    candidates = mode_res.candidates[i]
                elif isinstance(mode_res, dict):
                    candidates = mode_res.get("candidates", [[] for _ in range(6)])[i]
                else:
                    candidates = []
                if not candidates:
                    continue
                word = candidates[0]
                pattern = compare_words(word, target_word)
                for j in range(5):
                    if pattern[j] == 2:      # Green
                        image[i, j] = [84, 140, 80]
                    elif pattern[j] == 1:    # Yellow
                        image[i, j] = [190, 158, 63]
                    else:                    # Gray
                        image[i, j] = [63, 63, 64]

            ax.imshow(image, interpolation='nearest',
                      origin='upper', aspect='equal')
            ax.set_xticks([])
            ax.set_yticks([])

            # draw letters from chosen candidate on top of colored squares
            for i in range(6):
                mode_res = res.get(mode)
                if isinstance(mode_res, ModeResult):
                    candidates = mode_res.candidates[i]
                elif isinstance(mode_res, dict):
                    candidates = mode_res.get("candidates", [[] for _ in range(6)])[i]
                else:
                    candidates = []
                if not candidates:
                    continue
                word = candidates[0]
                pattern = compare_words(word, target_word)
                for j, ch in enumerate(word):
                    txt_color = 'black' if pattern[j] == 1 else 'white'
                    ax.text(j, i, ch.upper(), ha='center', va='center',
                            fontsize=14, fontweight='bold', color=txt_color)

            # left label only on first column
            if c == 0:
                ax.set_ylabel(f"{mode} ({mode_ratings.get(mode, 0)})", fontsize=12, rotation=0, labelpad=25)
                ax.yaxis.set_label_coords(-0.4, 0.5)

            # top title only on first row
            if r == 0:
                ax.set_title(f"Pattern {c+1}", fontsize=12)

    plt.tight_layout()
    plt.show()


def string_to_patterns(s: str) -> List[List[List[int]]]:
    s = s.lower()
    with open("font_data.json", "r") as f:
        font_dict = json.load(f)

    patterns: List[List[List[int]]] = []
    for char in s:
        if char in font_dict:
            patterns.append(font_dict[char])
        else:
            patterns.append(font_dict["?"])  # Use ? for unknown characters

    return patterns


def load_wordlist(path: str) -> List[str]:
    """Load newline separated 5-letter words from file.

    Returns lowercase words stripped of whitespace.
    """

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Wordlist file not found: {path}")
    with p.open("r", encoding="utf-8") as fh:
        return [w.strip().lower() for w in fh if w.strip()]


def main_cli() -> None:
    """Small CLI wrapper: runs the search and prints/plots results.

    - `--target` : target word
    - `--message` : textual message to use as desired patterns (maps characters into 6x5 font)
    - `--wordlist` : path to valid-wordle-words.txt
    """

    import argparse

    parser = argparse.ArgumentParser(description="Find Wordle candidates that match visual patterns")
    parser.add_argument("--target", default="thick", help="Target 5-letter word to match")
    parser.add_argument("--message", help="Optional message to translate to patterns using `font_data.json`")
    parser.add_argument("--wordlist", default="valid-wordle-words.txt", help="Path to newline-separated 5-letter words list")
    parser.add_argument("--modes", nargs="*", default=["x/gy", "gy/x", "y/gx", "x/yg", "yg/x"], help="Search modes to test")
    parser.add_argument("--top", type=int, default=1, help="How many candidate words to show per slot")

    args = parser.parse_args()

    # Load words
    valid_words = load_wordlist(args.wordlist)

    if args.message:
        desired_patterns = string_to_patterns(args.message)
    else:
        # Default patterns should be provided in the script; keep the original example.
        desired_patterns = [
            [[0, 1, 0, 1, 0], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [0, 1, 1, 1, 0], [0, 0, 1, 0, 0], [0, 0, 0, 0, 0]]
        ]

    results = find_words(valid_words, args.target, desired_patterns, args.modes)
    sorted_modes, mode_ratings = sort_modes(results)
    print_result(results, desired_patterns, args.target, sorted_modes, mode_ratings, args.top)
    # For plotting we pass the (single) results dict and rely on the function to
    # wrap into a list if needed.
    # Plot all available desired patterns as columns
    plot_result(results, args.target, sorted_modes, mode_ratings)


if __name__ == "__main__":
    main_cli()
