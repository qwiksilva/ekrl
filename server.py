
import json

from flask import Flask, request, jsonify

from game2 import EKGameV0

if __name__ == "__main__":
    game = EKGameV0("game_config.json", debug=True)
    json.dump(game.gameState, "gameState.json")




    app = Flask(__name__)

    # Initialize the game
    game = EKGameV0("game_config.json", debug=True)

    @app.route('/reset', methods=['POST'])
    def reset():
        game.reset()
        return jsonify({"message": "Game reset", "observation": game.observation.tolist()})

    @app.route('/step', methods=['POST'])
    def step():
        action = request.json.get('action')
        if action is None:
            return jsonify({"error": "Action is required"}), 400

        observation, reward, done, info = game.step(action)
        return jsonify({
            "observation": observation.tolist(),
            "reward": reward,
            "done": done,
            "info": info
        })

    @app.route('/render', methods=['GET'])
    def render():
        game.render()
        return jsonify({"message": "Game rendered in console"})

    if __name__ == '__main__':
        app.run(debug=True)