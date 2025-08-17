document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const startButton = document.getElementById('start-hand-button');
    const controls = {
        fold: document.getElementById('fold-button'),
        check: document.getElementById('check-button'),
        call: document.getElementById('call-button'),
        bet: document.getElementById('bet-button'),
        raise: document.getElementById('raise-button'),
        betAmount: document.getElementById('bet-amount'),
        panel: document.getElementById('player-controls')
    };
    const gameStatusEl = document.getElementById('game-status');
    const pokerTableEl = document.getElementById('poker-table');
    const potAmountEl = document.getElementById('pot-amount');
    const communityCardsEl = document.getElementById('community-cards');
    const gameLogEl = document.getElementById('game-log');

    let humanPlayerUUID = null;

    // --- Socket Event Handlers ---

    socket.on('connect', () => {
        gameStatusEl.textContent = 'Connecté au serveur !';
    });

    socket.on('game_state_update', (update) => {
        console.log('Game state update received:', update);
        const { event, data } = update;

        if (event === 'game_start') {
            humanPlayerUUID = data.seats.find(p => p.name === 'Vous')?.uuid;
            setupTable(data.seats);
        }

        if (data.round_state) {
            updateUI(data.round_state);
        } else if (event === 'round_start') {
            // Initial setup for the round
            updateUI(data);
        }
    });

    socket.on('human_action_required', (data) => {
        console.log('Action required:', data);
        controls.panel.style.display = 'flex';
        updateActionButtons(data.valid_actions);
    });

    socket.on('game_over', (result) => {
        gameStatusEl.textContent = `La partie est terminée. Résultat : ${JSON.stringify(result)}`;
        controls.panel.style.display = 'none';
    });

    socket.on('log_message', (data) => {
        addLogMessage(data.message);
    });


    // --- UI Rendering Functions ---

    function addLogMessage(message) {
        const logEntry = document.createElement('p');
        logEntry.textContent = message;
        gameLogEl.appendChild(logEntry);
        // Auto-scroll to the bottom
        gameLogEl.scrollTop = gameLogEl.scrollHeight;
    }

    function setupTable(seats) {
        pokerTableEl.querySelectorAll('.player-seat').forEach(el => el.remove()); // Clear old seats
        const positions = [
            { top: '88%', left: '50%' }, { top: '50%', left: '8%' }, { top: '15%', left: '25%' },
            { top: '12%', left: '50%' }, { top: '15%', left: '75%' }, { top: '50%', left: '92%' }
        ];
        seats.forEach((player, index) => {
            const seatEl = document.createElement('div');
            seatEl.className = 'player-seat';
            seatEl.id = `player-${player.uuid}`;
            seatEl.style.top = positions[index].top;
            seatEl.style.left = positions[index].left;
            seatEl.style.transform = 'translate(-50%, -50%)';

            seatEl.innerHTML = `
                <div class="player-info">
                    <span class="player-name">${player.name}</span>
                    <span class="player-stack">${player.stack}</span>
                </div>
                <div class="player-cards card-area"></div>
                <div class="dealer-button">D</div>
            `;
            pokerTableEl.appendChild(seatEl);
        });
    }

    function updateUI(state) {
        // Update Pot
        potAmountEl.textContent = state.pot?.main?.amount || 0;

        // Update Community Cards
        communityCardsEl.innerHTML = ''; // Clear old cards
        state.street?.forEach(cardStr => {
            communityCardsEl.appendChild(createCardElement(cardStr, true));
        });

        // Update Players
        state.seats?.forEach(player => {
            const seatEl = document.getElementById(`player-${player.uuid}`);
            if (!seatEl) return;

            seatEl.querySelector('.player-name').textContent = player.name;
            seatEl.querySelector('.player-stack').textContent = `Tapis: ${player.stack}`;

            const cardsContainer = seatEl.querySelector('.player-cards');
            cardsContainer.innerHTML = '';

            if (player.uuid === humanPlayerUUID && state.hole_card) {
                state.hole_card.forEach(cardStr => {
                    cardsContainer.appendChild(createCardElement(cardStr, true));
                });
            } else {
                 cardsContainer.innerHTML = '<div class="card-placeholder"></div><div class="card-placeholder"></div>';
            }

            seatEl.classList.toggle('active', state.next_player === player.uuid);
            seatEl.classList.toggle('folded', player.state === 'folded');
        });
    }

    function createCardElement(cardStr, isVisible) {
        const cardEl = document.createElement('div');
        if (!isVisible || !cardStr) {
            cardEl.className = 'card-placeholder';
            return cardEl;
        }
        cardEl.className = 'card';
        const suit = cardStr[0];
        const rank = cardStr.substring(1);
        const suitMap = { 'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠' };
        const colorMap = { 'H': 'red', 'D': 'red', 'C': 'black', 'S': 'black' };
        cardEl.textContent = `${rank}${suitMap[suit]}`;
        cardEl.style.color = colorMap[suit];
        return cardEl;
    }

    function updateActionButtons(validActions) {
        // Hide all buttons first
        Object.values(controls).forEach(el => {
            if (el.tagName === 'BUTTON') el.style.display = 'none';
        });

        validActions.forEach(actionInfo => {
            const action = actionInfo.action;
            const button = controls[action];
            if (button) {
                button.style.display = 'inline-block';
                if (action === 'call') {
                    button.textContent = `Suivre ${actionInfo.amount}`;
                }
                if (action === 'raise') {
                    controls.betAmount.min = actionInfo.amount.min;
                    controls.betAmount.value = actionInfo.amount.min;
                }
            }
        });
    }

    // --- Event Listeners for Player Actions ---

    startButton.addEventListener('click', () => {
        gameStatusEl.textContent = 'Démarrage de la partie...';
        gameLogEl.innerHTML = ''; // Vider le journal au début
        socket.emit('start_game');
    });

    controls.fold.addEventListener('click', () => {
        socket.emit('player_action', { action: 'fold', amount: 0 });
        controls.panel.style.display = 'none';
    });

    controls.check.addEventListener('click', () => {
        socket.emit('player_action', { action: 'call', amount: 0 }); // Check is a call of 0
        controls.panel.style.display = 'none';
    });

    controls.call.addEventListener('click', () => {
        const amount = parseInt(event.target.textContent.split(' ')[1], 10) || 0;
        socket.emit('player_action', { action: 'call', amount: amount });
        controls.panel.style.display = 'none';
    });

    controls.bet.addEventListener('click', () => {
        const amount = parseInt(controls.betAmount.value, 10);
        socket.emit('player_action', { action: 'raise', amount: amount }); // Bet is a raise
        controls.panel.style.display = 'none';
    });

    controls.raise.addEventListener('click', () => {
        const amount = parseInt(controls.betAmount.value, 10);
        socket.emit('player_action', { action: 'raise', amount: amount });
        controls.panel.style.display = 'none';
    });

});
