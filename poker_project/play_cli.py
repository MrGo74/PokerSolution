from pypokerengine.api.game import setup_config, start_poker
import joblib
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from poker_project.players import HumanPlayer, ModelPlayer

def main():
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
    for i in range(6):
        config.register_player(name=f"AI_Player_{i+1}", algorithm=ModelPlayer(model, le))

    game_result = start_poker(config, verbose=0)
    print("\n----- Game Over -----")
    print(game_result)

if __name__ == '__main__':
    main()
