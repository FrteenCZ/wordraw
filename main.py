import matplotlib.pyplot as plt
import numpy as np
import re
import json


def compare_words(guess, target):
    target = list(target)
    guess = list(guess)
    result = [0] * 5
    yellows = []
    for i in range(5):
        if guess[i] == target[i]:
            result[i] = 2
            target[i] = "-"
        elif guess[i] in target:
            yellows.append(i)

    for i in yellows:
        if guess[i] in target:
            result[i] = 1
            target[target.index(guess[i])] = "-"

    return result


def pattern_match_rating(pattern, requested_pattern, mode="x/gy"):
    # decode mode
    # pattern: ccc; cc/c; c/cc; c/c/c
    if not re.match(r'^(?!.*([xgy]).*\1)(?:[xgy]{3}|[xgy]{2}/[xgy]|[xgy]/[xgy]{2}|[xgy]/[xgy]/[xgy])$', mode):
        raise ValueError(f"Invalid pattern: {mode}")

    groups = mode.split('/')
    mode_parsed = [[0, 0, 0],
                   [0, 0, 0]]

    for group_index, group in enumerate(groups):
        for color_index, color in enumerate(group):
            if color == "g":
                mode_parsed[0][2] = group_index
                mode_parsed[1][2] = color_index
            elif color == "y":
                mode_parsed[0][1] = group_index
                mode_parsed[1][1] = color_index
            elif color == "x":
                mode_parsed[0][0] = group_index
                mode_parsed[1][0] = color_index

    # convert pattern
    group_match = 0
    color_match = 0

    for i in range(5):
        p = pattern[i]
        rp = requested_pattern[i]

        if mode_parsed[0][p] == rp:
            group_match += 1
            color_match += 2 - mode_parsed[1][p]

    return group_match * 10 + color_match


def find_words(word_list, target_word, desired_patterns, modes=["x/gy"]):
    results = []
    for i in range(len(desired_patterns)):
        results.append({})
        for mode in modes:
            results[i][mode] = {"candidates": [[]]*6, "ratings": [0]*6}

    for word in word_list:
        pattern = compare_words(word, target_word)
        for i in range(6):
            if word == target_word and i != 5:  # Avoid winning before last round
                continue

            for ipat, desired_pattern in enumerate(desired_patterns):
                for mode in modes:
                    rating = pattern_match_rating(
                        pattern, desired_pattern[i], mode)
                    if rating > results[ipat][mode]["ratings"][i]:
                        results[ipat][mode]["ratings"][i] = rating
                        results[ipat][mode]["candidates"][i] = [word]
                    elif rating == results[ipat][mode]["ratings"][i]:
                        results[ipat][mode]["candidates"][i].append(word)
    return results


def sort_modes(results):
    # sort modes by total ratings descending
    mode_ratings = {}
    for result in results:
        for mode in result.keys():
            mode_ratings[mode] = mode_ratings.get(
                mode, 0) + sum(result[mode]["ratings"])

    sorted_modes = sorted(mode_ratings.items(),
                          key=lambda x: x[1], reverse=True)
    return [mode for mode, rating in sorted_modes], mode_ratings


def display_pattern(pattern, mode="x/y/g"):
    mcolor = {"g": "🟩", "y": "🟨", "x": "⬜"}
    mletters = {"g": "G", "y": "Y", "x": "X"}
    mnumbers = {"g": "2", "y": "1", "x": "0"}

    mode = mode.split('/')

    colors = ""
    letters = ""
    numbers = ""
    for color in pattern:
        if color == 2:              # Green
            colors += mcolor[mode[2][0]]
            letters += mletters[mode[2][0]]
            numbers += mnumbers[mode[2][0]]
        elif color == 1:            # Yellow
            colors += mcolor[mode[1][0]]
            letters += mletters[mode[1][0]]
            numbers += mnumbers[mode[1][0]]
        else:                       # Gray
            colors += mcolor[mode[0][0]]
            letters += mletters[mode[0][0]]
            numbers += mnumbers[mode[0][0]]
    return colors, letters, numbers


def print_result(results, desired_patterns, target_word, modes=["x/gy"], mode_ratings={}, num_of_candidates=1):
    for mode in modes:
        print(f"Mode: {mode} (Total Rating: {mode_ratings.get(mode, 0)})")
        for result, desired_pattern in zip(results, desired_patterns):
            for i in range(6):
                colors, letters, numbers = display_pattern(
                    desired_pattern[i], mode)
                candidates = result[mode]["candidates"][i]
                newcolors, newletters, newnumbers = display_pattern(
                    compare_words(candidates[0], target_word))
                rating = result[mode]["ratings"][i]
                print(
                    f"Pattern {i+1}: {colors} ({letters}, {numbers}) -> {newcolors} ({newletters}, {newnumbers}) Rating: {rating}, Candidates: {candidates[:num_of_candidates]}")
            print()
        print("--------------------------------")


def plot_result(result, target_word, modes=["x/gy"], mode_ratings={}):
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
                candidates = res.get(mode, {}).get("candidates", [[]] * 6)[i]
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
                candidates = res.get(mode, {}).get("candidates", [[]] * 6)[i]
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


def string_to_patterns(s):
    s = s.lower()
    with open("font_data.json", "r") as f:
        font_dict = json.load(f)

    patterns = []
    for char in s:
        if char in font_dict:
            patterns.append(font_dict[char])
        else:
            patterns.append(font_dict["?"])  # Use ? for unknown characters

    return patterns


if __name__ == "__main__":
    with open("valid-wordle-words.txt", "r") as f:
        valid_words = set(word.strip().lower() for word in f.readlines())

    target_word = "thick"
    desired_patterns = [
        [[0, 1, 0, 1, 0],
         [1, 1, 1, 1, 1],
         [1, 1, 1, 1, 1],
         [0, 1, 1, 1, 0],
         [0, 0, 1, 0, 0],
         [0, 0, 0, 0, 0],
         ],
        [[0, 1, 0, 1, 0],
         [1, 1, 1, 1, 1],
         [1, 1, 1, 1, 1],
         [0, 1, 1, 1, 0],
         [0, 0, 1, 0, 0],
         [1, 1, 1, 1, 1],
         ],]
    # modes = ["x/y/g", "x/g/y", "y/x/g", "y/g/x", "g/x/y", "g/y/x"]

    # message = "sex?"
    # desired_patterns = string_to_patterns(message)
    modes = ["x/gy", "gy/x", "y/gx", "x/yg", "yg/x"]
    # modes = ["x/gy", "gy/x"]

    results = find_words(valid_words, target_word, desired_patterns, modes)
    sorted_modes, mode_ratings = sort_modes(results)
    print_result(results, desired_patterns, target_word,
                 sorted_modes, mode_ratings)
    plot_result(results, target_word, sorted_modes, mode_ratings)
