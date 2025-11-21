import matplotlib.pyplot as plt
import re

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
    if not re.match(r'^(?!.*(.).*\1)(?:[xgy]{3}|[xgy]{2}/[xgy]|[xgy]/[xgy]{2}|[xgy]/[xgy]/[xgy])$', mode):
        raise ValueError("Invalid pattern")

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


def find_words(word_list, target_word, desired_pattern, modes=["x/gy"]):
    result = {}
    for mode in modes:
        result[mode] = {"candidates": [[]]*6, "ratings": [0]*6}
    
    for word in word_list:
        pattern = compare_words(word, target_word)
        for i in range(6):
            for mode in modes:
                rating = pattern_match_rating(pattern, desired_pattern[i], mode)
                if rating > result[mode]["ratings"][i]:
                    result[mode]["ratings"][i] = rating
                    result[mode]["candidates"][i] = [word]
                elif rating == result[mode]["ratings"][i]:
                    result[mode]["candidates"][i].append(word)
    return result

def display_result(result):
    colors = ""
    letters = ""
    numbers = ""
    for color in result:
        if color == 2:          # Green
            colors += "🟩"
            letters += "G"
            numbers += "2"
        elif color == 1:        # Yellow
            colors += "🟨"
            letters += "Y"
            numbers += "1"
        else:                   # Gray
            colors += "⬜"
            letters += "X"
            numbers += "0"
    return colors, letters, numbers


if __name__ == "__main__":
    with open("valid-wordle-words.txt", "r") as f:
        valid_words = set(word.strip().lower() for word in f.readlines())
    
    target_word = "vowel"
    desired_pattern = [
        [0, 1, 0, 1, 0], 
        [0, 1, 0, 1, 0], 
        [0, 0, 0, 0, 0], 
        [1, 0, 0, 0, 1], 
        [0, 1, 1, 1, 0], 
        [0, 0, 0, 0, 0], 
    ]

    modes = ["x/gy"]
    result = find_words(valid_words, target_word, desired_pattern, modes)
    for mode in modes:
        print(f"Mode: {mode}")
        for i in range(6):
            colors, letters, numbers = display_result(desired_pattern[i])
            candidates = result[mode]["candidates"][i]
            rating = result[mode]["ratings"][i]
            print(f"Pattern {i+1}: {colors} ({letters}, {numbers}) -> Rating: {rating}, Candidates: {candidates}")
        print()