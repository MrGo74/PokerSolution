from pypokerengine.api.game import setup_config, start_poker
import joblib
import os
import sys
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from poker_project.players import HumanPlayer, ModelPlayer

def main():
    parser = argparse.ArgumentParser(description="Play poker against AI players.")
    parser.add_argument("--num_ai_players", type=int, default=6, help="Number of AI players.")
    args = parser.parse_args()

    try:
        model_path = os.path.join(os.path.dirname(__file__), 'poker_model.joblib')
        encoder_path = os.path.join(os.path.dirname(__file__), 'label_encoder.joblib')
        model = joblib.load(model_path)
        le = joblib.load(encoder_path)
    except FileNotFoundError:
        print("Model not found. Please run train.py to train and save the model.")
        return

    small_blind_amount = 5
    config = setup_config(max_round=100, initial_stack=1000, small_blind_amount=small_blind_amount)
    config.register_player(name="Human", algorithm=HumanPlayer(small_blind_amount=small_blind_amount))
    for i in range(args.num_ai_players):
        config.register_player(name=f"AI_Player_{i+1}", algorithm=ModelPlayer(model, le))

    game_result = start_poker(config, verbose=0)
    print("\n----- Game Over -----")

    winner_name = ""
    max_stack = -1
    for player_info in game_result.get('players', []):
        if player_info['stack'] > max_stack:
            max_stack = player_info['stack']
            winner_name = player_info['name']

    num_rounds = game_result.get('game_information', {}).get('round_count', 'N/A')

    if winner_name:
        print(f"{winner_name} wins in {num_rounds} rounds!")
    else:
        print("Game finished. No clear winner.")

    print("\nFinal Results:")
    print(game_result)

if __name__ == '__main__':
    main()
