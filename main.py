target = "crane"

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
print(f"result:\t{display_result(result)[0]} ({result})")
