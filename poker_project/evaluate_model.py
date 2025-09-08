from pypokerengine.players import BasePokerPlayer
from pypokerengine.api.game import setup_config, start_poker
import random
import joblib

class FishPlayer(BasePokerPlayer):  # Always calls
    def declare_action(self, valid_actions, hole_card, round_state):
        call_action_info = valid_actions[1]
        action, amount = call_action_info["action"], call_action_info["amount"]
        return action, amount
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

class FoldPlayer(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        fold_action_info = valid_actions[0]
        action, amount = fold_action_info["action"], fold_action_info["amount"]
        return action, amount
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

class RaisePlayer(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        raise_action_info = valid_actions[2]
        action, amount = raise_action_info["action"], raise_action_info["amount"]["max"]
        return action, amount
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

def encode_card(card):
    if card is None:
        return 0
    ranks = '23456789TJQKA'
    suits = 'SCDH'
    rank = ranks.find(card[1]) + 2
    suit = suits.find(card[0]) + 1
    return suit * 100 + rank

def preprocess_state(hole_card, round_state):
    features = []
    h1 = encode_card(hole_card[0] if len(hole_card) > 0 else None)
    h2 = encode_card(hole_card[1] if len(hole_card) > 1 else None)
    features.extend([h1, h2])
    community_cards = round_state['community_card']
    for i in range(5):
        features.append(encode_card(community_cards[i] if i < len(community_cards) else None))
    features.append(round_state['pot']['main']['amount'])
    features.append(round_state['round_count'])
    return [features]

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
                    if min_raise == -1: # Cannot raise
                        return valid_actions[1]['action'], valid_actions[1]['amount']
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

def main():
    # Load the trained model and label encoder
    try:
        model = joblib.load('/app/poker_project/poker_model.joblib')
        le = joblib.load('/app/poker_project/label_encoder.joblib')
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
