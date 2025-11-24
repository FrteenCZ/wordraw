# wordraw

A project to automatically find suitable words to enter in Wordle that match a desired visual pattern of gray, yellow, and green squares.

This project uses [this word list](https://gist.github.com/dracos/dd0668f281e685bad51479e5acaadb93). Credits to [dracos](https://gist.github.com/dracos).

This project also uses the 6x5 font used to render character patterns in `font_data.json`. The font is [Monomin 6x5](https://fontstruct.com/fontstructions/show/395434/monomin_6x5) created by [jlong64](https://fontstruct.com/fontstructors/378571/jlong64).

## Usage

Install dependencies (recommended in a virtualenv):

```powershell
python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

Run the script (example):

```powershell
python main.py --target thick --message "hi" --wordlist valid-wordle-words.txt
```

To run tests:

```powershell
pytest -q
```

## Pattern and Mode Explanation

- Each `desired_pattern` is represented as a 6x5 pattern (one row per round).
	Each position in the 5-letter pattern is an integer that refers to a group index
	in the selected `mode` string.

- Modes are strings describing how colors are grouped, examples:
	- `x/y/g` : three groups in order (gray -> yellow -> green)
	- `x/gy`  : two groups where the second group stands for green and yellow (gy)

- When you set `--message` the script maps characters to 6x5 fonts stored in `font_data.json`.

Example: `x/gy` has groups `['x','gy']` and thus a `requested_pattern` entry of `1` selects
the second group (g or y) for that position.

