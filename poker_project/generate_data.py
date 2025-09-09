from pypokerengine.api.game import setup_config, start_poker
import json
import pandas as pd
import os
import sys
import argparse
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from poker_project.players import SharkPlayer

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
    parser = argparse.ArgumentParser(description="Generate poker game data.")
    parser.add_argument("--num_games", type=int, default=100, help="Number of games to simulate.")
    parser.add_argument("--num_players", type=int, default=4, help="Number of players in each game.")
    args = parser.parse_args()

    data_logger = DataLogger()

    for i in range(args.num_games):
        print(f"--- Starting game {i+1}/{args.num_games} ---")
        config = setup_config(max_round=100, initial_stack=100, small_blind_amount=5)

        for j in range(args.num_players):
            aggression = random.uniform(0.2, 0.8)  # Generate a random aggression level
            config.register_player(name=f"shark_{j+1}", algorithm=SharkPlayer(data_logger, aggression=aggression))

        start_poker(config, verbose=0)

    print("All games finished. Saving data...")
    data_logger.save_log()
    print("Data saved successfully.")

if __name__ == '__main__':
    main()
