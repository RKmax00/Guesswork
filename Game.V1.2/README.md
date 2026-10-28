# GUESSWORK — Vintage Edition

A vintage phosphor-green number guessing game built with Python, Flask, HTML and CSS.

## Run on Windows

Open CMD in this extracted project folder (the folder containing `app.py`) and run:

```bat
py -m pip install -r requirements.txt
py app.py
```

Open http://127.0.0.1:5000 in your browser. Keep the CMD window open while playing. Press Ctrl+C in CMD to stop the server.

## Test

```bat
py -m unittest -v test_app.py
```

The tests cover the home page, all four difficulty choices, invalid difficulty, high/low guesses, invalid guesses, wins and personal best, losing at the attempt limit, restart links using both GET and POST, guessing without a game, and the custom 404 page.

## Sound

- Short, low-volume synthesized feedback for high/low guesses, wins and losses.
- Optional very quiet ambient terminal hum starts only after the first user gesture, because browsers restrict autoplay.
- The SOUND ON/OFF toggle controls both ambience and effects; the choice is remembered in local storage.
- No external audio files and no looping melody.

## Project structure

- `app.py` — game logic and Flask routes
- `templates/index.html` — main game page
- `templates/error.html` — friendly error page
- `static/style.css` — vintage terminal styling and animations
- `test_app.py` — route and game behavior tests
- `requirements.txt` — Python dependency

## Notes

- Game difficulty ranges and attempt limits are preserved: Easy 1–10 / 2 attempts, Medium 1–50 / 4, Hard 1–100 / 9, Hardest 1–1000 / 14.
- Invalid guesses do not consume an attempt.
- Personal best is stored in the Flask session cookie for this browser profile, not a shared online leaderboard.
- For public deployment, set a long random `SECRET_KEY` environment variable. Do not use the development fallback key.
- Flask debug mode is off by default. Only set `FLASK_DEBUG=1` for local development.
