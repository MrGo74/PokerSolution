// Fichier principal pour la logique du jeu de Poker

document.addEventListener('DOMContentLoaded', () => {
    console.log("Le DOM est chargé. Démarrage du jeu.");
    startGame();
});


// --- CONSTANTES & CONFIG ---
const SUITS = { '♥': 'red', '♦': 'red', '♣': 'black', '♠': 'black' };
const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
const ROUNDS = { PRE_FLOP: 'pre-flop', FLOP: 'flop', TURN: 'turn', RIVER: 'river', SHOWDOWN: 'showdown' };

const AI_PROFILES = {
    TIGHT_AGGRESSIVE: { type: 'ai', name: 'Le Requin', handStrengthThreshold: 18, aggression: 0.8, bluff: 0.1 },
    LOOSE_PASSIVE: { type: 'ai', name: 'La Station', handStrengthThreshold: 8, aggression: 0.2, bluff: 0.05 },
    TIGHT_PASSIVE: { type: 'ai', name: 'Le Rocher', handStrengthThreshold: 16, aggression: 0.3, bluff: 0.0 },
    LOOSE_AGGRESSIVE: { type: 'ai', name: 'Le Maniaque', handStrengthThreshold: 10, aggression: 0.9, bluff: 0.4 },
    BALANCED: { type: 'ai', name: 'Le Pro', handStrengthThreshold: 14, aggression: 0.6, bluff: 0.15 }
};

// --- CLASSES DE LOGIQUE (Moteur) ---

class Card {
    constructor(suit, rank) { this.suit = suit; this.rank = rank; }
    toString() { return `${this.rank}${this.suit}`; }
}

class Deck {
    constructor() { this.cards = []; }
    reset() { this.cards = []; for (const suit in SUITS) { for (const rank of RANKS) { this.cards.push(new Card(suit, rank)); } } return this; }
    shuffle() { for (let i = this.cards.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1));[this.cards[i], this.cards[j]] = [this.cards[j], this.cards[i]]; } return this; }
    deal() { return this.cards.pop(); }
}

class Player {
    constructor(id, stack, profile) {
        this.id = id;
        this.name = profile.name || 'Vous';
        this.stack = stack;
        this.isHuman = profile.type === 'human';
        this.profile = profile;
        this.resetForNewHand();
    }
    resetForNewHand() { this.hand = []; this.status = 'playing'; this.totalBetInRound = 0; }
    bet(amount) {
        const betAmount = Math.min(amount, this.stack);
        this.stack -= betAmount;
        this.totalBetInRound += betAmount;
        return betAmount;
    }
}

class HandEvaluator { /* ... (code inchangé) ... */
    constructor() { this.rankValues = { '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14 }; }
    evaluate(sevenCards) { const combinations = this._getCombinations(sevenCards, 5); let bestHand = null; for (const hand of combinations) { const currentHand = this._evaluateFiveCardHand(hand); if (!bestHand || currentHand.rank > bestHand.rank || (currentHand.rank === bestHand.rank && this._isCurrentHandBetter(currentHand, bestHand))) { bestHand = currentHand; } } return bestHand; }
    _isCurrentHandBetter(current, best) { for (let i = 0; i < current.values.length; i++) { if (current.values[i] > best.values[i]) return true; if (current.values[i] < best.values[i]) return false; } return false; }
    _evaluateFiveCardHand(hand) { const sortedHand = hand.map(c => ({ ...c, value: this.rankValues[c.rank] })).sort((a, b) => b.value - a.value); const values = sortedHand.map(c => c.value); const suits = sortedHand.map(c => c.suit); const isFlush = suits.every(s => s === suits[0]); const isStraight = values.every((v, i) => i === 0 || v === values[i-1] - 1) || ([14, 5, 4, 3, 2].every(v => values.includes(v))); if (isStraight && isFlush) return { rank: values[0] === 14 ? 9 : 8, name: "Quinte Flush", values }; const counts = values.reduce((acc, val) => { acc[val] = (acc[val] || 0) + 1; return acc; }, {}); const primaryRanks = Object.keys(counts).sort((a,b) => counts[b] - counts[a] || b - a).map(Number); if (Object.values(counts).includes(4)) return { rank: 7, name: "Carré", values: primaryRanks }; if (Object.values(counts).includes(3) && Object.values(counts).includes(2)) return { rank: 6, name: "Full", values: primaryRanks }; if (isFlush) return { rank: 5, name: "Couleur", values }; if (isStraight) return { rank: 4, name: "Quinte", values: values.includes(14) && values.includes(2) ? [5,4,3,2,1] : values }; if (Object.values(counts).includes(3)) return { rank: 3, name: "Brelan", values: primaryRanks }; if (Object.values(counts).filter(v => v === 2).length === 2) return { rank: 2, name: "Double Paire", values: primaryRanks }; if (Object.values(counts).includes(2)) return { rank: 1, name: "Paire", values: primaryRanks }; return { rank: 0, name: "Carte Haute", values }; }
    _getCombinations(arr, k) { const result = []; function combine(current, start) { if (current.length === k) { result.push([...current]); return; } for (let i = start; i < arr.length; i++) { current.push(arr[i]); combine(current, i + 1); current.pop(); } } combine([], 0); return result; }
}

// --- CLASSE DE GESTION DE L'INTERFACE (UI) ---
class GameUI { /* ... (code inchangé, juste s'assurer que player.name est utilisé) ... */
    constructor(game) { this.game = game; this.playerSeats = document.querySelectorAll('.player-seat'); this.potAmountEl = document.getElementById('pot-amount'); this.controls = { fold: document.getElementById('fold-button'), check: document.getElementById('check-button'), call: document.getElementById('call-button'), bet: document.getElementById('bet-button'), raise: document.getElementById('raise-button'), betAmount: document.getElementById('bet-amount') }; this._setupEventListeners(); }
    _setupEventListeners() { this.controls.fold.addEventListener('click', () => this.game.handlePlayerAction('fold')); this.controls.check.addEventListener('click', () => this.game.handlePlayerAction('check')); this.controls.call.addEventListener('click', () => this.game.handlePlayerAction('call')); this.controls.bet.addEventListener('click', () => this.game.handlePlayerAction('bet', parseInt(this.controls.betAmount.value, 10))); this.controls.raise.addEventListener('click', () => this.game.handlePlayerAction('raise', parseInt(this.controls.betAmount.value, 10))); }
    render() { this._renderPlayers(); this._renderCommunityCards(); this._renderPot(); if (this.game.activePlayer && this.game.activePlayer.isHuman) { this._updateActionButtons(); } else { this._hideAllControls(); } }
    _renderPlayers() { this.game.players.forEach((player, index) => { const seat = document.getElementById(player.id); if (!seat) return; seat.querySelector('.player-name').textContent = player.name; seat.querySelector('.player-stack').textContent = `Tapis: ${player.stack}`; seat.querySelector('.dealer-button').style.display = (index === this.game.dealerPosition) ? 'flex' : 'none'; seat.classList.toggle('active', index === this.game.currentPlayerIndex); seat.classList.toggle('folded', player.status === 'folded'); const cardsContainer = seat.querySelector('.player-cards'); cardsContainer.innerHTML = ''; player.hand.forEach(card => cardsContainer.appendChild(this._createCardElement(card, player.isHuman || this.game.currentRound === ROUNDS.SHOWDOWN))); for (let i = player.hand.length; i < 2; i++) { cardsContainer.appendChild(this._createCardElement(null)); } }); }
    _renderCommunityCards() { const communityCardsContainer = document.querySelector('#community-cards'); const placeholders = communityCardsContainer.querySelectorAll('.card-placeholder, .card'); placeholders.forEach((placeholder, index) => { const newCardEl = this._createCardElement(this.game.communityCards[index], true); if (placeholder.parentNode) { placeholder.parentNode.replaceChild(newCardEl, placeholder); } }); }
    _renderPot() { this.potAmountEl.textContent = this.game.pot; }
    _createCardElement(card, isVisible = false) { const cardEl = document.createElement('div'); if (!card) { cardEl.className = 'card-placeholder'; return cardEl; } cardEl.className = isVisible ? 'card' : 'card-placeholder'; if (isVisible) { cardEl.textContent = `${card.rank}${card.suit}`; cardEl.style.color = SUITS[card.suit]; } return cardEl; }
    _updateActionButtons() { const { betToCall, activePlayer, lastRaise, bigBlind } = this.game; const playerBet = activePlayer.totalBetInRound; this.controls.fold.style.display = 'inline-block'; this.controls.call.style.display = (betToCall > playerBet) ? 'inline-block' : 'none'; this.controls.call.textContent = `Suivre ${betToCall - playerBet}`; this.controls.check.style.display = (betToCall === playerBet) ? 'inline-block' : 'none'; const canBet = betToCall === 0; this.controls.bet.style.display = canBet ? 'inline-block' : 'none'; this.controls.raise.style.display = !canBet ? 'inline-block' : 'none'; this.controls.betAmount.style.display = 'inline-block'; const minRaise = betToCall + (betToCall - this.game.lastRaiseAmount); this.controls.betAmount.min = canBet ? bigBlind : minRaise; this.controls.betAmount.value = this.controls.betAmount.min; }
    _hideAllControls() { Object.values(this.controls).forEach(el => el.style.display = 'none'); }
}

// --- CLASSE PRINCIPALE DU JEU (Game) ---
class Game {
    constructor(playerProfiles, startingStack) {
        this.players = playerProfiles.map((profile, i) => new Player(`player-${i+1}`, startingStack, profile));
        this.ui = new GameUI(this);
        this.deck = new Deck();
        this.handEvaluator = new HandEvaluator();
        this.smallBlind = 10; this.bigBlind = 20;
        this.dealerPosition = -1;
        this.resetGame();
    }
    resetGame() { this.pot = 0; this.communityCards = []; this.currentPlayerIndex = -1; this.currentRound = null; this.betToCall = 0; this.lastRaiseAmount = 0; this.actionResolver = null; }
    get activePlayer() { return this.players[this.currentPlayerIndex]; }

    async startNewHand() {
        this.resetGame();
        this.deck.reset().shuffle();
        this.players.forEach(p => p.resetForNewHand());
        this.dealerPosition = (this.dealerPosition + 1) % this.players.length;
        this._dealHoleCards();
        this._postBlinds();

        this.currentRound = ROUNDS.PRE_FLOP;
        await this._runBettingRound((this.dealerPosition + 3) % this.players.length);

        for (const round of [ROUNDS.FLOP, ROUNDS.TURN, ROUNDS.RIVER]) {
            if (this.players.filter(p => p.status === 'playing').length > 1) {
                this.currentRound = round;
                this._dealCommunityCards(round === ROUNDS.FLOP ? 3 : 1);
                this.players.forEach(p => p.totalBetInRound = 0);
                this.betToCall = 0; this.lastRaiseAmount = 0;
                await this._runBettingRound((this.dealerPosition + 1) % this.players.length);
            }
        }

        this.currentRound = ROUNDS.SHOWDOWN;
        this._determineWinner();
    }

    _postBlinds() {
        const sbPlayer = this.players[(this.dealerPosition + 1) % this.players.length];
        const bbPlayer = this.players[(this.dealerPosition + 2) % this.players.length];
        this.pot += sbPlayer.bet(this.smallBlind);
        this.pot += bbPlayer.bet(this.bigBlind);
        this.betToCall = this.bigBlind;
        this.lastRaiseAmount = this.bigBlind;
    }

    _dealHoleCards() { for (let i = 0; i < 2; i++) { for (const player of this.players) { player.hand.push(this.deck.deal()); } } }
    _dealCommunityCards(count) { for (let i = 0; i < count; i++) { this.communityCards.push(this.deck.deal()); } }

    async _runBettingRound(startIndex) {
        let playersInHand = this.players.filter(p => p.status === 'playing');
        if (playersInHand.length < 2) return;

        let actionIndex = startIndex;
        let roundShouldEnd = false;

        while (!roundShouldEnd) {
            this.currentPlayerIndex = actionIndex % this.players.length;
            const player = this.activePlayer;

            if (player.status === 'playing') {
                this.ui.render();
                const action = await this._getPlayerAction(player);
                this.handleAction(player, action);

                if (action.type === 'bet' || action.type === 'raise') {
                    // Action is reopened, everyone else must act again
                }
            }

            actionIndex++;
            // Check if the round is over
            const activePlayers = this.players.filter(p => p.status === 'playing');
            const betsMatched = activePlayers.every(p => p.totalBetInRound === this.betToCall || p.stack === 0);
            const firstActor = this.players[startIndex % this.players.length];
            if (betsMatched && actionIndex > this.players.indexOf(firstActor)) {
                roundShouldEnd = true;
            }
            if (activePlayers.length <= 1) roundShouldEnd = true;
        }
        this.currentPlayerIndex = -1;
        this.ui.render();
    }

    async _getPlayerAction(player) {
        if (player.isHuman) {
            return new Promise(resolve => { this.actionResolver = resolve; });
        }
        // --- NOUVELLE LOGIQUE D'IA BASÉE SUR LES PROFILS ---
        await this._delay(800);
        const { profile } = player;
        const betToCall = this.betToCall - player.totalBetInRound;

        const preFlopStrength = this._calculatePreFlopHandStrength(player.hand);
        let effectiveHandStrength = preFlopStrength;
        if (this.currentRound !== ROUNDS.PRE_FLOP) {
            const postFlopEval = this.handEvaluator.evaluate([...this.communityCards, ...player.hand]);
            effectiveHandStrength = (postFlopEval.rank * 15) + (postFlopEval.values[0] || 0); // Convertir rang post-flop en score comparable
        }

        // Décision de jouer la main ou non (surtout pre-flop)
        if (effectiveHandStrength < profile.handStrengthThreshold && betToCall > 0) {
             if (Math.random() > profile.bluff) return { type: 'fold' };
        }

        // Décision d'être agressif ou passif
        const isAggressive = Math.random() < profile.aggression;

        if (betToCall > 0) { // Face à une mise
            if (isAggressive) {
                const raiseAmount = this.betToCall * 3;
                return { type: 'raise', amount: raiseAmount };
            }
            return { type: 'call' };
        } else { // Pas de mise
            if (isAggressive) {
                const betAmount = Math.floor(this.pot * 0.75);
                return { type: 'bet', amount: betAmount > this.bigBlind ? betAmount : this.bigBlind };
            }
            return { type: 'check' };
        }
    }

    _calculatePreFlopHandStrength(hand) { /* ... (code inchangé) ... */
        const card1 = hand[0], card2 = hand[1];
        const rankValues = { '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14 };
        const value1 = rankValues[card1.rank], value2 = rankValues[card2.rank];
        let score = Math.max(value1, value2);
        if (value1 === value2) score += 10 + value1;
        if (card1.suit === card2.suit) score += 4;
        const diff = Math.abs(value1 - value2);
        if (diff === 1 || diff === 12) score += 3; else if (diff <= 4) score += (4-diff);
        return score;
    }

    handlePlayerAction(type, amount = 0) { if (this.actionResolver && this.activePlayer.isHuman) { this.actionResolver({ type, amount }); this.actionResolver = null; } }
    handleAction(player, action) {
        switch(action.type) {
            case 'fold': player.status = 'folded'; break;
            case 'check': break;
            case 'call': this.pot += player.bet(this.betToCall - player.totalBetInRound); break;
            case 'bet': this.pot += player.bet(action.amount); this.betToCall = action.amount; this.lastRaiseAmount = action.amount; break;
            case 'raise': this.pot += player.bet(action.amount - player.totalBetInRound); this.lastRaiseAmount = action.amount - this.betToCall; this.betToCall = action.amount; break;
        }
    }
    _determineWinner() { this.ui.render(); }
    _delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
}

// --- DÉMARRAGE DU JEU ---
function startGame() {
    const profiles = [
        { type: 'human' },
        AI_PROFILES.LOOSE_PASSIVE,
        AI_PROFILES.TIGHT_AGGRESSIVE,
        AI_PROFILES.TIGHT_PASSIVE,
        AI_PROFILES.LOOSE_AGGRESSIVE,
        AI_PROFILES.BALANCED
    ];
    // Mélanger les profils IA pour des parties variées
    const aiProfiles = profiles.slice(1).sort(() => Math.random() - 0.5);
    const gameProfiles = [profiles[0], ...aiProfiles];

    const game = new Game(gameProfiles, 1000);
    document.getElementById('start-hand-button').addEventListener('click', () => game.startNewHand());
    game.ui.render();
}
