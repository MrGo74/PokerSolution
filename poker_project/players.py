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

def get_position(player_seat, dealer_btn_pos, num_players):
    if num_players == 2:
        return "SB" if player_seat == dealer_btn_pos else "BB"

    positions_map = {
        6: ["SB", "BB", "UTG", "MP", "CO", "BTN"],
        9: ["SB", "BB", "UTG", "UTG+1", "MP1", "MP2", "HJ", "CO", "BTN"]
    }

    if num_players not in positions_map:
        return f"Seat {player_seat}"

    relative_position = (player_seat - dealer_btn_pos - 1 + num_players) % num_players

    # Adjust for standard poker position naming
    # In poker, SB is at dealer_btn_pos + 1, BB is dealer_btn_pos + 2
    if relative_position == 0: # Small Blind
        return positions_map[num_players][0]
    if relative_position == 1: # Big Blind
        return positions_map[num_players][1]

    # Other positions relative to the blinds
    # The player after BB is UTG
    # The player before SB is the Button

    # Let's try a simpler mapping based on offset from dealer
    # This is a bit tricky because the seat indices wrap around.

    # A more direct approach:
    # 1. SB is (dealer_btn + 1) % num_players
    # 2. BB is (dealer_btn + 2) % num_players
    # 3. BTN is dealer_btn

    if player_seat == (dealer_btn_pos + 1) % num_players: return positions_map[num_players][0] # SB
    if player_seat == (dealer_btn_pos + 2) % num_players: return positions_map[num_players][1] # BB
    if player_seat == dealer_btn_pos: return positions_map[num_players][-1] # BTN

    # For other positions, it's more complex. Let's use a simpler logic for now
    # This is a simplification. For a 6-max game:
    # SB, BB, UTG, MP, CO, BTN
    # 0,  1,   2,  3,  4,  5 (relative to SB)

    # Let's find the SB seat index
    sb_seat = (dealer_btn_pos + 1) % num_players

    # Calculate seats relative to the SB
    relative_seat = (player_seat - sb_seat + num_players) % num_players

    if num_players == 6:
        # SB, BB, UTG, MP, CO, BTN
        pos_names = ["SB", "BB", "UTG", "MP", "CO", "BTN"]
        return pos_names[relative_seat]
    if num_players == 9:
        pos_names = ["SB", "BB", "UTG", "UTG+1", "MP1", "MP2", "HJ", "CO", "BTN"]
        return pos_names[relative_seat]

    return f"Seat {player_seat}"

def preprocess_state(hole_card, round_state, my_uuid):
    features_dict = {}

    # Existing features
    features_dict['hole_card_1'] = encode_card(hole_card[0] if len(hole_card) > 0 else None)
    features_dict['hole_card_2'] = encode_card(hole_card[1] if len(hole_card) > 1 else None)
    community_cards = round_state['community_card']
    for i in range(5):
        features_dict[f'community_card_{i+1}'] = encode_card(community_cards[i] if i < len(community_cards) else None)
    features_dict['pot.main.amount'] = round_state['pot']['main']['amount']
    features_dict['round_count'] = round_state['round_count']

    # New features: Position and Action History
    num_players = len(round_state['seats'])
    my_seat = -1
    for i, seat in enumerate(round_state['seats']):
        if seat['uuid'] == my_uuid:
            my_seat = i
            break

    dealer_btn_pos = round_state['dealer_btn']
    position_str = get_position(my_seat, dealer_btn_pos, num_players)

    # One-hot encode position
    position_map = { "SB": 0, "BB": 1, "UTG": 2, "MP": 3, "CO": 4, "BTN": 5, "UTG+1": 6, "MP1": 7, "MP2": 8, "HJ": 9}
    features_dict['position'] = position_map.get(position_str, -1)

    # Action history (last 5 actions)
    action_hist = round_state.get('action_histories', {}).get(round_state.get('street'), [])
    for i in range(5):
        action_name = 'none'
        if i < len(action_hist):
            action_name = action_hist[i].get('action', 'none')

        action_map = {'fold': 1, 'call': 2, 'raise': 3, 'none': 0}
        features_dict[f'action_{i+1}'] = action_map.get(action_name, 0)

    feature_names = [
        'hole_card_1', 'hole_card_2', 'community_card_1', 'community_card_2',
        'community_card_3', 'community_card_4', 'community_card_5',
        'pot.main.amount', 'round_count', 'position',
        'action_1', 'action_2', 'action_3', 'action_4', 'action_5'
    ]

    return pd.DataFrame([features_dict], columns=feature_names)

# Player Classes
class FishPlayer(BasePokerPlayer):
    def __init__(self, data_logger=None):
        self.data_logger = data_logger
    def declare_action(self, valid_actions, hole_card, round_state):
        call_action_info = valid_actions[1]
        action, amount = call_action_info["action"], call_action_info["amount"]
        if self.data_logger: self.data_logger.log_action(hole_card, round_state, action, amount, self.uuid)
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
        if self.data_logger: self.data_logger.log_action(hole_card, round_state, action, amount, self.uuid)
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
        if self.data_logger: self.data_logger.log_action(hole_card, round_state, action, amount, self.uuid)
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
        if self.data_logger: self.data_logger.log_action(hole_card, round_state, action, amount, self.uuid)
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
        features = preprocess_state(hole_card, round_state, self.uuid)
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
    def __init__(self, small_blind_amount=5):
        self.small_blind_amount = small_blind_amount

    def declare_action(self, valid_actions, hole_card, round_state):
        big_blind = self.small_blind_amount * 2
        pot_amount = round_state['pot']['main']['amount']
        pot_bb = pot_amount / big_blind

        num_players = len(round_state['seats'])
        my_seat = [s['name'] for s in round_state['seats']].index('Human')
        dealer_btn_pos = round_state['dealer_btn']
        position = get_position(my_seat, dealer_btn_pos, num_players)

        print(f"---------- Your Turn (Position: {position}) ----------")
        print(f"Hole card: {hole_card}")
        print(f"Community card: {round_state['community_card']}")
        print(f"Pot: {pot_amount} ({pot_bb:.1f}bb)")
        print("---------------------------------")
        for i, action_info in enumerate(valid_actions):
            action = action_info["action"]
            if action == "raise":
                min_amount = action_info["amount"]["min"]
                max_amount = action_info["amount"]["max"]
                min_bb = min_amount / big_blind
                max_bb = max_amount / big_blind
                print(f"{i}: {action} (min: {min_amount} ({min_bb:.1f}bb), max: {max_amount} ({max_bb:.1f}bb))")
            else:
                print(f"{i}: {action}")
        while True:
            try:
                action_index = int(input("Choose an action index: "))
                chosen_action = valid_actions[action_index]
                action = chosen_action["action"]
                if action == "raise":
                    min_raise = chosen_action['amount']['min']
                    max_raise = chosen_action['amount']['max']
                    amount = int(input(f"Enter raise amount ({min_raise} - {max_raise}): "))
                    if min_raise <= amount <= max_raise:
                        return action, amount
                    else:
                        print("Invalid raise amount.")
                else:
                    return action, chosen_action["amount"]
            except (ValueError, IndexError):
                print("Invalid input. Please enter a valid action index.")

    def receive_game_start_message(self, game_info):
        print("----- Game Start -----")
        big_blind = self.small_blind_amount * 2
        for player in game_info['seats']:
            stack_bb = player['stack'] / big_blind
            print(f"{player['name']}: stack {player['stack']} ({stack_bb:.1f}bb)")
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
        player_stack = 0
        for player in round_state['seats']:
            if player['uuid'] == player_uuid:
                player_name = player['name']
                player_stack = player['stack']
                break

        big_blind = self.small_blind_amount * 2
        stack_bb = player_stack / big_blind
        amount = action.get('amount', 0)
        amount_bb = amount / big_blind

        print(f"\n>> {player_name} ({stack_bb:.1f}bb) declared {action['action']}({amount} ({amount_bb:.1f}bb))")

    def receive_round_result_message(self, winners, hand_info, round_state):
        print("\n----- Round Result -----")
        for winner_info in winners:
            print(f"{winner_info['name']} won {winner_info['stack']}")
        print("------------------------")

class SharkPlayer(BasePokerPlayer):
    def __init__(self, data_logger=None, aggression=0.5):
        self.data_logger = data_logger
        self.aggression = aggression

    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state['community_card']
        win_rate = estimate_hole_card_win_rate(
                nb_simulation=20,
                nb_player=len(round_state['seats']),
                hole_card=gen_cards(hole_card),
                community_card=gen_cards(community_card)
                )

        raise_threshold = 0.7 - (self.aggression * 0.2)  # More aggressive => lower raise threshold
        call_threshold = 0.4 - (self.aggression * 0.2)   # More aggressive => lower call threshold

        if win_rate >= raise_threshold:
            action, amount = valid_actions[2]['action'], valid_actions[2]['amount']['max'] # Raise max
        elif win_rate >= call_threshold:
            action, amount = valid_actions[1]['action'], valid_actions[1]['amount'] # Call
        else:
            action, amount = valid_actions[0]['action'], valid_actions[0]['amount'] # Fold

        # Fallback if action is not possible (e.g. cannot raise)
        if action == 'raise' and valid_actions[2]['amount']['min'] == -1:
            action, amount = valid_actions[1]['action'], valid_actions[1]['amount'] # Call instead

        if self.data_logger:
            self.data_logger.log_action(hole_card, round_state, action, amount, self.uuid)

        return action, amount

    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass
