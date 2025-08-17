from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.players import BasePokerPlayer
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key'
socketio = SocketIO(app)

# --- Game State & Player Management ---
game_thread = None
human_player_action = None
human_player_uuid = "human_player_uuid"

class HumanPlayerInterface(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        global human_player_action
        human_player_action = None
        socketio.emit('human_action_required', {'valid_actions': valid_actions, 'round_state': round_state})
        while human_player_action is None:
            socketio.sleep(0.1)
        return human_player_action['action'], human_player_action['amount']

    def receive_game_start_message(self, game_info):
        socketio.emit('game_state_update', {'event': 'game_start', 'data': game_info})

    def receive_round_start_message(self, round_count, hole_card, seats):
        socketio.emit('game_state_update', {'event': 'round_start', 'data': {'hole_card': hole_card, 'seats': seats}})
        socketio.emit('log_message', {'message': f"--- Début de la main #{round_count} ---"})

    def receive_street_start_message(self, street, round_state):
        socketio.emit('game_state_update', {'event': 'street_start', 'data': {'street': street, 'round_state': round_state}})
        if street != 'preflop':
            socketio.emit('log_message', {'message': f"--- {street.capitalize()} ---"})

    def receive_game_update_message(self, action, round_state):
        socketio.emit('game_state_update', {'event': 'game_update', 'data': {'action': action, 'round_state': round_state}})
        player_name = "Joueur Inconnu"
        for p in round_state['seats']:
            if p['uuid'] == action['player_uuid']:
                player_name = p['name']
                break

        log_msg = f"{player_name} : {action['action']}"
        if action['action'].lower() in ['raise', 'call', 'bet']:
            log_msg += f" ({action['amount']})"
        socketio.emit('log_message', {'message': log_msg})

    def receive_round_result_message(self, winners, hand_info, round_state):
        socketio.emit('game_state_update', {'event': 'round_result', 'data': {'winners': winners, 'hand_info': hand_info, 'round_state': round_state}})
        winner_names = [w['name'] for w in winners]
        log_msg = f"--- Fin de la main. Gagnant(s) : {', '.join(winner_names)} ---"
        socketio.emit('log_message', {'message': log_msg})

def _calculate_preflop_strength(hole_card):
    rank_map = { '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14 }
    c1, c2 = hole_card[0], hole_card[1]
    v1, v2 = rank_map[c1[1]], rank_map[c2[1]]
    score = (v1 + v2) / 2
    if v1 == v2: score += 10
    if c1[0] == c2[0]: score += 4
    if abs(v1 - v2) == 1 or abs(v1-v2) == 12: score += 2
    return score

class TightAggressiveAI(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        strength = _calculate_preflop_strength(hole_card)
        call_action = valid_actions[1]
        fold_action = valid_actions[0]
        raise_action = valid_actions[2] if len(valid_actions) > 2 else None
        if strength > 18 and raise_action:
            return raise_action['action'], max(raise_action['amount']['min'], round_state['pot']['main']['amount'])
        if strength > 14:
             return call_action['action'], call_action['amount']
        return fold_action['action'], 0
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

class LoosePassiveAI(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        strength = _calculate_preflop_strength(hole_card)
        call_action = valid_actions[1]
        fold_action = valid_actions[0]
        if strength > 9 and call_action['amount'] < (round_state['pot']['main']['amount'] / 2):
            return call_action['action'], call_action['amount']
        if call_action['amount'] == 0:
            return call_action['action'], 0
        return fold_action['action'], 0
    def receive_game_start_message(self, game_info): pass
    def receive_round_start_message(self, round_count, hole_card, seats): pass
    def receive_street_start_message(self, street, round_state): pass
    def receive_game_update_message(self, action, round_state): pass
    def receive_round_result_message(self, winners, hand_info, round_state): pass

def run_poker_game():
    config = setup_config(max_round=10, initial_stack=1000, small_blind_amount=10)
    config.register_player(name="Le Requin", algorithm=TightAggressiveAI())
    config.register_player(name="La Station", algorithm=LoosePassiveAI())
    config.register_player(name="Le Requin 2", algorithm=TightAggressiveAI())
    config.register_player(name="La Station 2", algorithm=LoosePassiveAI())
    config.register_player(name="Le Requin 3", algorithm=TightAggressiveAI())
    config.register_player(name="Vous", algorithm=HumanPlayerInterface())
    game_result = start_poker(config, verbose=0)
    socketio.emit('game_over', game_result)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('response', {'data': 'Connected to Poker Server'})

@socketio.on('start_game')
def handle_start_game():
    global game_thread
    if game_thread is None or not game_thread.is_alive():
        print("Starting new poker game thread.")
        game_thread = threading.Thread(target=run_poker_game)
        game_thread.start()
    else:
        print("Game already in progress.")

@socketio.on('player_action')
def handle_player_action(data):
    global human_player_action
    print(f"Received player action: {data}")
    human_player_action = {'action': data.get('action'), 'amount': data.get('amount')}

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
