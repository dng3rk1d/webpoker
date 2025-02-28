# app.py
from flask import Flask, render_template, jsonify, request, send_from_directory
from game_engine import TexasHoldemGame
import os

app = Flask(__name__)

# Create a global game instance.
game = TexasHoldemGame()

@app.route("/")
def index():
    # Render the main game page.
    return render_template("index.html")

@app.route("/api/start", methods=["POST"])
def start_hand():
    # Start a new hand and return the updated state.
    game.start_hand()
    return jsonify({"status": "hand_started", "game_state": game.get_state()})

@app.route("/api/action", methods=["POST"])
def player_action():
    # Process a player action (call, fold, bet, all-in) coming from the frontend.
    data = request.get_json()
    action = data.get("action")
    amount = data.get("amount", 0)
    result = game.process_player_action(action, amount)
    return jsonify({"status": "action_processed", "result": result, "game_state": game.get_state()})

# Optional routes to serve images (if you want to route image access through Flask)
@app.route("/cards/<filename>")
def serve_card(filename):
    return send_from_directory(os.path.join(app.static_folder, "cards"), filename)

@app.route("/chips/<filename>")
def serve_chip(filename):
    return send_from_directory(os.path.join(app.static_folder, "chips"), filename)

if __name__ == "__main__":
    app.run(debug=True)