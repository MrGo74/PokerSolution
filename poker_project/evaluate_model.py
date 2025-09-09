from pypokerengine.api.game import setup_config, start_poker
import joblib
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from poker_project.players import FishPlayer, FoldPlayer, RaisePlayer, ModelPlayer

def main():
    # Load the trained model and label encoder
    try:
        model_path = os.path.join(os.path.dirname(__file__), 'poker_model.joblib')
        encoder_path = os.path.join(os.path.dirname(__file__), 'label_encoder.joblib')
        model = joblib.load(model_path)
        le = joblib.load(encoder_path)
    except FileNotFoundError:
        print("Model not found. Please run train.py to train and save the model.")
        return

    config = setup_config(max_round=100, initial_stack=100, small_blind_amount=5)
    config.register_player(name="fish", algorithm=FishPlayer())
    config.register_player(name="folder", algorithm=FoldPlayer())
    config.register_player(name="raiser", algorithm=RaisePlayer())
    config.register_player(name="model_player", algorithm=ModelPlayer(model, le))
    game_result = start_poker(config, verbose=1)
    print(game_result)

if __name__ == '__main__':
    main()
