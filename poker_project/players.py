from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import random
import pandas as pd

# Helper Functions
def encode_card(card):
    if card is None: return 0
    ranks = '23456789TJQKA'
    suits = 'SCDH'
    rank = ranks.find(card[1]) + 2
    suit = suits.find(card[0]) + 1
    return suit * 100 + rank

def preprocess_state(hole_card, round_state):
    features_dict = {}
    features_dict['hole_card_1'] = encode_card(hole_card[0] if len(hole_card) > 0 else None)
    features_dict['hole_card_2'] = encode_card(hole_card[1] if len(hole_card) > 1 else None)
    community_cards = round_state['community_card']
    for i in range(5):
        features_dict[f'community_card_{i+1}'] = encode_card(community_cards[i] if i < len(community_cards) else None)
    features_dict['pot.main.amount'] = round_state['pot']['main']['amount']
    features_dict['round_count'] = round_state['round_count']
    feature_names = [
        'hole_card_1', 'hole_card_2', 'community_card_1', 'community_card_2',
        'community_card_3', 'community_card_4', 'community_card_5',
        'pot.main.amount', 'round_count'
    ]
    return pd.DataFrame([features_dict], columns=feature_names)

# Player Classes
class FishPlayer(BasePokerPlayer):
    def __init__(self, data_logger=None):
        self.data_logger = data_logger
    def declare_action(self, valid_actions, hole_card, round_state):
        call_action_info = valid_actions[1]
        action, amount = call_action_info["action"], call_action_info["amount"]
        if self.data_logger: self.data_logger.log_action(hole_card, round_state, action, amount)
        return action, amount
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

class FoldPlayer(BasePokerPlayer):
    def __init__(self, data_logger=None):
        self.data_logger = data_logger
    def declare_action(self, valid_actions, hole_card, round_state):
        fold_action_info = valid_actions[0]
        action, amount = fold_action_info["action"], fold_action_info["amount"]
        if self.data_logger: self.data_logger.log_action(hole_card, round_state, action, amount)
        return action, amount
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

class RaisePlayer(BasePokerPlayer):
    def __init__(self, data_logger=None):
        self.data_logger = data_logger
    def declare_action(self, valid_actions, hole_card, round_state):
        raise_action_info = valid_actions[2]
        action, amount = raise_action_info["action"], raise_action_info["amount"]["max"]
        if self.data_logger: self.data_logger.log_action(hole_card, round_state, action, amount)
        return action, amount
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

class RandomPlayer(BasePokerPlayer):
    def __init__(self, data_logger=None):
        self.data_logger = data_logger
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
        if self.data_logger: self.data_logger.log_action(hole_card, round_state, action, amount)
        return action, amount
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

class ModelPlayer(BasePokerPlayer):
    def __init__(self, model, le):
        self.model = model
        self.le = le
    def declare_action(self, valid_actions, hole_card, round_state):
        features = preprocess_state(hole_card, round_state)
        action_encoded = self.model.predict(features)[0]
        action_str = self.le.inverse_transform([action_encoded])[0]
        for valid_action in valid_actions:
            if valid_action['action'] == action_str:
                if action_str == 'raise':
                    min_raise = valid_action['amount']['min']
                    max_raise = valid_action['amount']['max']
                    if min_raise == -1: return valid_actions[1]['action'], valid_actions[1]['amount']
                    amount = random.randint(min_raise, max_raise)
                    return valid_action['action'], amount
                else:
                    return valid_action['action'], valid_action['amount']
        return valid_actions[1]['action'], valid_actions[1]['amount']
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

class HumanPlayer(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        print("---------- Your Turn ----------")
        print(f"Hole card: {hole_card}")
        print(f"Community card: {round_state['community_card']}")
        print(f"Pot: {round_state['pot']['main']['amount']}")
        print("---------------------------------")
        for i, action_info in enumerate(valid_actions):
            action = action_info["action"]
            if action == "raise":
                min_amount = action_info["amount"]["min"]
                max_amount = action_info["amount"]["max"]
                print(f"{i}: {action} (min: {min_amount}, max: {max_amount})")
            else:
                print(f"{i}: {action}")
        while True:
            try:
                action_index = int(input("Choose an action index: "))
                chosen_action = valid_actions[action_index]
                action = chosen_action["action"]
                if action == "raise":
                    amount = int(input(f"Enter raise amount ({chosen_action['amount']['min']} - {chosen_action['amount']['max']}): "))
                    if chosen_action['amount']['min'] <= amount <= chosen_action['amount']['max']:
                        return action, amount
                    else:
                        print("Invalid raise amount.")
                else:
                    return action, chosen_action["amount"]
            except (ValueError, IndexError):
                print("Invalid input. Please enter a valid action index.")
    def receive_game_start_message(self, game_info):
        print("----- Game Start -----")
        for player in game_info['seats']:
            print(f"{player['name']}: stack {player['stack']}")
        print("----------------------")
    def receive_round_start_message(self, round_count, hole_card, seats):
        print(f"\n----- Round {round_count} Start -----")
        print(f"Your hole card is {hole_card}")
        print("---------------------------")
    def receive_street_start_message(self, street, round_state):
        print(f"\n--- Street '{street}' Start ---")
        print(f"Community card: {round_state['community_card']}")
        print("-----------------------------")
    def receive_game_update_message(self, action, round_state):
        player_uuid = action['player_uuid']
        player_name = "Unknown"
        for player in round_state['seats']:
            if player['uuid'] == player_uuid:
                player_name = player['name']
                break
        print(f"\n>> {player_name} declared {action['action']}({action.get('amount', '')})")
    def receive_round_result_message(self, winners, hand_info, round_state):
        print("\n----- Round Result -----")
        for winner_info in winners:
            print(f"{winner_info['name']} won {winner_info['stack']}")
        print("------------------------")

class SharkPlayer(BasePokerPlayer):
    def __init__(self, data_logger=None):
        self.data_logger = data_logger

    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state['community_card']
        win_rate = estimate_hole_card_win_rate(
                nb_simulation=20,
                nb_player=len(round_state['seats']),
                hole_card=gen_cards(hole_card),
                community_card=gen_cards(community_card)
                )

        if win_rate >= 0.7:
            action, amount = valid_actions[2]['action'], valid_actions[2]['amount']['max'] # Raise max
        elif win_rate >= 0.4:
            action, amount = valid_actions[1]['action'], valid_actions[1]['amount'] # Call
        else:
            action, amount = valid_actions[0]['action'], valid_actions[0]['amount'] # Fold

        # Fallback if action is not possible (e.g. cannot raise)
        if action == 'raise' and valid_actions[2]['amount']['min'] == -1:
            action, amount = valid_actions[1]['action'], valid_actions[1]['amount'] # Call instead

        if self.data_logger:
            self.data_logger.log_action(hole_card, round_state, action, amount)

        return action, amount

    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass
