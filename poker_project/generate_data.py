from pypokerengine.players import BasePokerPlayer
from pypokerengine.api.game import setup_config, start_poker
import random
import json
import pandas as pd
import os

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

data_logger = DataLogger()

class FishPlayer(BasePokerPlayer):  # Always calls
    def declare_action(self, valid_actions, hole_card, round_state):
        call_action_info = valid_actions[1]
        action, amount = call_action_info["action"], call_action_info["amount"]
        data_logger.log_action(hole_card, round_state, action, amount)
        return action, amount

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

class FoldPlayer(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        fold_action_info = valid_actions[0]
        action, amount = fold_action_info["action"], fold_action_info["amount"]
        data_logger.log_action(hole_card, round_state, action, amount)
        return action, amount

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

class RaisePlayer(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        raise_action_info = valid_actions[2]
        action, amount = raise_action_info["action"], raise_action_info["amount"]["max"]
        data_logger.log_action(hole_card, round_state, action, amount)
        return action, amount

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

class RandomPlayer(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        r = random.random()
        if r < 0.33:
            fold_action_info = valid_actions[0]
            action, amount = fold_action_info["action"], fold_action_info["amount"]
        elif r < 0.66:
            call_action_info = valid_actions[1]
            action, amount = call_action_info["action"], call_action_info["amount"]
        else:
            raise_action_info = valid_actions[2]
            if raise_action_info["amount"]["min"] == -1:
                call_action_info = valid_actions[1]
                action, amount = call_action_info["action"], call_action_info["amount"]
            else:
                action, amount = raise_action_info["action"], random.randint(raise_action_info["amount"]["min"], raise_action_info["amount"]["max"])
        data_logger.log_action(hole_card, round_state, action, amount)
        return action, amount

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

def main():
    config = setup_config(max_round=1000, initial_stack=100, small_blind_amount=5)
    config.register_player(name="fish", algorithm=FishPlayer())
    config.register_player(name="folder", algorithm=FoldPlayer())
    config.register_player(name="raiser", algorithm=RaisePlayer())
    config.register_player(name="random", algorithm=RandomPlayer())
    game_result = start_poker(config, verbose=1)
    print(game_result)
    data_logger.save_log()

if __name__ == '__main__':
    main()
