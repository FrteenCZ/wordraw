import matplotlib.pyplot as plt
import re

with open("valid-wordle-words.txt", "r") as f:
    valid_words = set(word.strip().lower() for word in f.readlines())

# for i, word in enumerate(valid_words):
#     print(f"{i}: {word}")


def compare_words(guess, target):
    target = list(target)
    guess = list(guess)
    result = 0
    yellows = []
    for i in range(5):
        if guess[i] == target[i]:
            result += 2 * 3**i
            target[i] = "-"
        elif guess[i] in target:
            yellows.append(i)

    for i in yellows:
        if guess[i] in target:
            result += 1 * 3**i
            target[target.index(guess[i])] = "-"

    return result


def pattern_match_rating(pattern, requested_pattern, mode="gy/x"):
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
        

requested_pattern = [1, 1, 0, 1, 1]
pattern = [2, 2, 0, 2, 2]

print(pattern_match_rating(pattern, requested_pattern, mode="x/gy"))


def display_result(result):
    colors = ""
    letters = ""
    numbers = ""
    for i in range(5):
        digit = result % 3
        if digit == 2:          # Green
            colors += "🟩"
            letters += "G"
            numbers += "2"
        elif digit == 1:        # Yellow
            colors += "🟨"
            letters += "Y"
            numbers += "1"
        else:                   # Gray
            colors += "⬜"
            letters += "X"
            numbers += "0"
        result //= 3
    return colors, letters, numbers


target = "crane"
guess = "ncree"

print(f"target:\t{target}")
print(f"guess:\t{guess}")


result = compare_words(guess, target)
colors, letters, numbers = display_result(result)
print(f"result:\t{display_result(result)} ({result})")
