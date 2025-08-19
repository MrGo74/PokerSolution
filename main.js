document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const calculateBtn = document.getElementById('calculate-btn');
    const hand1Input = document.getElementById('hand1');
    const hand2Input = document.getElementById('hand2');
    const player1EquityDisplay = document.getElementById('player1-equity');
    const player2EquityDisplay = document.getElementById('player2-equity');
    const tieEquityDisplay = document.getElementById('tie-equity');

    // --- Card & Deck Logic ---
    const RANKS = '23456789TJQKA';
    const SUITS = 'shdc';

    function createDeck() {
        const deck = [];
        for (const suit of SUITS) {
            for (const rank of RANKS) {
                deck.push(rank + suit);
            }
        }
        return deck;
    }

    // --- Simulation Logic ---
    function runEquitySimulation(hand1, hand2, iterations = 10000) {
        const deck = createDeck();

        const knownCards = hand1.concat(hand2);
        const remainingDeck = deck.filter(card => !knownCards.includes(card));

        let stats = {
            player1Wins: 0,
            player2Wins: 0,
            ties: 0
        };

        for (let i = 0; i < iterations; i++) {
            // Fisher-Yates shuffle
            for (let j = remainingDeck.length - 1; j > 0; j--) {
                const k = Math.floor(Math.random() * (j + 1));
                [remainingDeck[j], remainingDeck[k]] = [remainingDeck[k], remainingDeck[j]];
            }

            const board = remainingDeck.slice(0, 5);

            const p1Cards = hand1.concat(board);
            const p2Cards = hand2.concat(board);

            // Use PokerSolver to evaluate hands
            const p1Hand = Hand.solve(p1Cards);
            const p2Hand = Hand.solve(p2Cards);

            // Use PokerSolver to determine the winner
            const winners = Hand.winners([p1Hand, p2Hand]);

            if (winners.length === 1) {
                // To check which hand won, we can compare the description or card pool.
                // A simpler way is to check if the winning hand's cards include player 1's cards.
                // Note: This is a bit of a hack. A more robust way might be to compare the solved hands directly.
                // Let's compare the solved hands' card arrays.
                if (winners[0] === p1Hand) {
                    stats.player1Wins++;
                } else {
                    stats.player2Wins++;
                }
            } else {
                stats.ties++;
            }
        }

        return {
            player1Equity: ((stats.player1Wins / iterations) * 100).toFixed(2),
            player2Equity: ((stats.player2Wins / iterations) * 100).toFixed(2),
            tiePercentage: ((stats.ties / iterations) * 100).toFixed(2)
        };
    }

    // --- UI Connection ---
    function parseHand(handString) {
        if (!handString || handString.length !== 4) {
            alert("Format de main invalide. Entrez 4 caractères, ex: 'AsKd'.");
            return null;
        }
        const hand = [handString.slice(0, 2), handString.slice(2, 4)];
        const validRanks = new Set(RANKS.split(''));
        const validSuits = new Set(SUITS.split(''));

        for (const card of hand) {
            if (!validRanks.has(card[0].toUpperCase()) || !validSuits.has(card[1].toLowerCase())) {
                 alert(`Carte invalide: ${card}.`);
                 return null;
            }
        }
        // Normalize card format for PokerSolver (e.g., As, Kd)
        return hand.map(c => c[0].toUpperCase() + c[1].toLowerCase());
    }

    calculateBtn.addEventListener('click', () => {
        const hand1Str = hand1Input.value.trim();
        const hand2Str = hand2Input.value.trim();

        const hand1 = parseHand(hand1Str);
        const hand2 = parseHand(hand2Str);

        if (!hand1 || !hand2) return;

        const allCards = hand1.concat(hand2);
        if (new Set(allCards).size !== 4) {
            alert("Les mains ne peuvent pas contenir de cartes identiques.");
            return;
        }

        player1EquityDisplay.textContent = "Calcul en cours...";
        player2EquityDisplay.textContent = "";
        tieEquityDisplay.textContent = "";

        setTimeout(() => {
            const results = runEquitySimulation(hand1, hand2);
            player1EquityDisplay.textContent = `Main 1: ${results.player1Equity}%`;
            player2EquityDisplay.textContent = `Main 2: ${results.player2Equity}%`;
            tieEquityDisplay.textContent = `Égalité: ${results.tiePercentage}%`;
        }, 10);
    });
});
