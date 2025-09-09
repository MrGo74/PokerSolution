from pypokerengine.api.game import setup_config, start_poker
import json
import pandas as pd
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from poker_project.players import FishPlayer, FoldPlayer, RaisePlayer, RandomPlayer, SharkPlayer

DATA_LOG = []
DATA_FILE = os.path.join(os.path.dirname(__file__), 'poker_data.csv')

class DataLogger:
    def log_action(self, hole_card, round_state, action, amount):
        log_entry = {
            'hole_card': str(hole_card),
            'round_state': json.dumps(round_state),
            'action': action,
            'amount': amount
        }
        DATA_LOG.append(log_entry)

    def save_log(self):
        if DATA_LOG:
            df = pd.DataFrame(DATA_LOG)
            df.to_csv(DATA_FILE, index=False, mode='w', header=True)

def main():
    num_games = 100
    data_logger = DataLogger()

    for i in range(num_games):
        print(f"--- Starting game {i+1}/{num_games} ---")
        config = setup_config(max_round=100, initial_stack=100, small_blind_amount=5)
        config.register_player(name="shark_1", algorithm=SharkPlayer(data_logger))
        config.register_player(name="shark_2", algorithm=SharkPlayer(data_logger))
        config.register_player(name="shark_3", algorithm=SharkPlayer(data_logger))
        config.register_player(name="random", algorithm=RandomPlayer(data_logger))
        start_poker(config, verbose=0)

    print("All games finished. Saving data...")
    data_logger.save_log()
    print("Data saved successfully.")

if __name__ == '__main__':
    main()
