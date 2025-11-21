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


def find_words(word_list, target_word, desired_pattern, modes=["x/gy"]):
    result = {}
    for mode in modes:
        result[mode] = {"candidates": [[]]*6, "ratings": [0]*6}
    
    for word in word_list:
        pattern = compare_words(word, target_word)
        for i in range(6):
            if word == target_word and i != 5: # Avoid winning before last round
                continue

            for mode in modes:
                rating = pattern_match_rating(pattern, desired_pattern[i], mode)
                if rating > result[mode]["ratings"][i]:
                    result[mode]["ratings"][i] = rating
                    result[mode]["candidates"][i] = [word]
                elif rating == result[mode]["ratings"][i]:
                    result[mode]["candidates"][i].append(word)
    return result

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

    modes = ["x/gy", "xy/g", "gy/x", "x/y/g"]
    result = find_words(valid_words, target_word, desired_pattern, modes)
    for mode in modes:
        print(f"Mode: {mode}")
        for i in range(6):
            colors, letters, numbers = display_pattern(desired_pattern[i], mode)
            candidates = result[mode]["candidates"][i]
            newcolors, newletters, newnumbers = display_pattern(compare_words(candidates[0], target_word))
            rating = result[mode]["ratings"][i]
            print(f"Pattern {i+1}: {colors} ({letters}, {numbers}) -> {newcolors} ({newletters}, {newnumbers}) Rating: {rating}, Candidates: {candidates[0]}")
        print()