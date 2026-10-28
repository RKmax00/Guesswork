import os
import random
from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

LEVELS = {
    "easy": {"maximum": 10, "attempt_limit": 2},
    "medium": {"maximum": 50, "attempt_limit": 4},
    "hard": {"maximum": 100, "attempt_limit": 9},
    "hardest": {"maximum": 1000, "attempt_limit": 14},
}

def new_game(difficulty):
    """Create a fresh game using a validated difficulty."""
    config = LEVELS[difficulty]
    session["game"] = {
        "difficulty": difficulty,
        "number": random.randint(1, config["maximum"]),
        "maximum": config["maximum"],
        "attempt_limit": config["attempt_limit"],
        "attempts": 0,
        "history": [],
        "message": "A number is hiding. Make your first guess.",
        "message_type": "neutral",
        "status": "playing",
        "hint_even_odd": False,
        "hint_range": None,
        "new_best": False,
    }

def render_home(status=200, error=None):
    return render_template(
        "index.html",
        game=session.get("game"),
        best=session.get("best"),
        error=error,
    ), status

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        difficulty = request.form.get("difficulty", "").lower().strip()
        if difficulty not in LEVELS:
            return render_template(
                "index.html", game=None, best=session.get("best"),
                error="Choose a valid difficulty.", 
            ), 400
        new_game(difficulty)
        return redirect(url_for("index"), code=303)

    return render_home()

@app.post("/guess")
def guess():
    game = session.get("game")
    if not game or game.get("status") != "playing":
        return redirect(url_for("index"), code=303)

    raw_guess = request.form.get("guess", "").strip()
    try:
        # Reject decimals and other non-integer values rather than silently coercing.
        guess_number = int(raw_guess)
        if str(guess_number) != raw_guess and raw_guess not in (f"+{guess_number}",):
            raise ValueError
    except (TypeError, ValueError):
        game["message"] = "Enter a whole number to make your guess."
        game["message_type"] = "warning"
        session["game"] = game
        return redirect(url_for("index"), code=303)

    if not 1 <= guess_number <= game["maximum"]:
        game["message"] = f"Keep your guess between 1 and {game['maximum']}."
        game["message_type"] = "warning"
        session["game"] = game
        return redirect(url_for("index"), code=303)

    game["attempts"] += 1
    result = "correct" if guess_number == game["number"] else (
        "low" if guess_number < game["number"] else "high"
    )
    game["history"].insert(0, {"guess": guess_number, "result": result})

    if result == "correct":
        game["status"] = "won"
        game["message"] = f"You found it in {game['attempts']} {'attempt' if game['attempts'] == 1 else 'attempts'}."
        game["message_type"] = "win"
        best = session.get("best")
        if best is None or game["attempts"] < best:
            session["best"] = game["attempts"]
            game["new_best"] = True
    else:
        game["message"] = "Too low. Go higher." if result == "low" else "Too high. Come down."
        game["message_type"] = result

        # Hints unlock only when the player reaches these attempt milestones.
        if game["attempts"] == 5:
            game["hint_even_odd"] = True
            game["even_odd_hint"] = "even" if game["number"] % 2 == 0 else "odd"

        if game["attempts"] == 10:
            low = max(1, game["number"] - random.randint(1, 25))
            high = min(game["maximum"], game["number"] + random.randint(1, 25))
            game["hint_range"] = [low, high]

        if game["attempts"] >= game["attempt_limit"]:
            game["status"] = "lost"
            game["message"] = f"Out of attempts. The number was {game['number']}."
            game["message_type"] = "lost"

    session["game"] = game
    return redirect(url_for("index"), code=303)

@app.route("/restart", methods=["GET", "POST"])
def restart():
    """GET support is intentional: the UI's Change Level / Play Again links use anchors."""
    session.pop("game", None)
    return redirect(url_for("index"), code=303)

@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, title="SIGNAL NOT FOUND",
                           message="That page is not part of this game."), 404

@app.errorhandler(405)
def method_not_allowed(_error):
    return render_template("error.html", code=405, title="WRONG INPUT",
                           message="That action cannot be used here. Return to the game and try again."), 405

@app.errorhandler(500)
def server_error(_error):
    return render_template("error.html", code=500, title="SYSTEM ERROR",
                           message="Something unexpected happened. Return to the game and try again."), 500

if __name__ == "__main__":
    # Debug mode is opt-in; do not expose the interactive debugger by default.
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
