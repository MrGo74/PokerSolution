from pypokerengine.api.game import setup_config, start_poker
import json
import pandas as pd
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from poker_project.players import FishPlayer, FoldPlayer, RaisePlayer, RandomPlayer

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
            df.to_csv(DATA_FILE, index=False, mode='a', header=not os.path.exists(DATA_FILE))

def main():
    data_logger = DataLogger()
    config = setup_config(max_round=1000, initial_stack=100, small_blind_amount=5)
    config.register_player(name="fish", algorithm=FishPlayer(data_logger))
    config.register_player(name="folder", algorithm=FoldPlayer(data_logger))
    config.register_player(name="raiser", algorithm=RaisePlayer(data_logger))
    config.register_player(name="random", algorithm=RandomPlayer(data_logger))
    game_result = start_poker(config, verbose=1)
    print(game_result)
    data_logger.save_log()

if __name__ == '__main__':
    main()
