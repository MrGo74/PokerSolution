// --- Représentation des Cartes et du Paquet ---

const RANKS = '23456789TJQKA';
const SUITS = 'shdc';

// Crée un paquet de 52 cartes
function createDeck() {
    const deck = [];
    for (const suit of SUITS) {
        for (const rank of RANKS) {
            deck.push(rank + suit);
        }
    }
    return deck;
}

// Convertit un rang (T, J, Q, K, A) en sa valeur numérique
function rankToValue(rank) {
    return RANKS.indexOf(rank);
}

// --- Logique d'Évaluation de Main ---

class HandEvaluator {
    constructor(holeCards, board) {
        const allCards = holeCards.concat(board);
        if (allCards.length !== 7) {
            // S'il n'y a pas 7 cartes, on complète avec des cartes vides pour simplifier l'algo
            // Ceci est utile pour les calculs pré-flop, flop, et turn.
            const placeholders = Array(7 - allCards.length).fill(null);
            this.cards = allCards.concat(placeholders);
        } else {
            this.cards = allCards;
        }
        this.handRank = this.evaluate();
    }

    evaluate() {
        const combinations = this.getCombinations(this.cards.filter(c => c), 5);
        let bestHandRank = { value: -1 };

        for (const hand of combinations) {
            const currentHandRank = this.rankHand(hand);
            if (currentHandRank.value > bestHandRank.value) {
                bestHandRank = currentHandRank;
            }
        }
        return bestHandRank;
    }

    getCombinations(array, size) {
        const result = [];
        function p(t, i) {
            if (t.length === size) {
                result.push(t);
                return;
            }
            if (i >= array.length) {
                return;
            }
            p(t.concat(array[i]), i + 1);
            p(t, i + 1);
        }
        p([], 0);
        return result;
    }

    rankHand(hand) {
        const ranks = hand.map(c => c[0]).sort((a, b) => rankToValue(b) - rankToValue(a));
        const suits = hand.map(c => c[1]);
        const rankValues = ranks.map(r => rankToValue(r));

        const isFlush = new Set(suits).size === 1;
        const isStraight = this.isStraight(rankValues);

        const rankCounts = {};
        rankValues.forEach(v => { rankCounts[v] = (rankCounts[v] || 0) + 1; });
        const counts = Object.values(rankCounts).sort((a, b) => b - a);
        const sortedUniqueRanks = Object.keys(rankCounts).map(Number).sort((a, b) => b - a);

        // Réorganiser les rangs pour le score (le plus fréquent en premier)
        const sortedRanksByFreq = Object.keys(rankCounts).map(Number).sort((a, b) => {
            if (rankCounts[a] !== rankCounts[b]) {
                return rankCounts[b] - rankCounts[a];
            }
            return b - a;
        });

        // Calcul du score
        let handType, score;
        const base = 10000000000; // Pour s'assurer que le type de main domine le score

        if (isStraight && isFlush) {
            handType = 8; // Quinte Flush
            score = handType * base + sortedRanksByFreq[0];
            return { name: "Quinte Flush", value: score, hand: hand };
        }
        if (counts[0] === 4) {
            handType = 7; // Carré
            score = handType * base + sortedRanksByFreq[0] * 100 + sortedRanksByFreq[1];
            return { name: "Carré", value: score, hand: hand };
        }
        if (counts[0] === 3 && counts[1] === 2) {
            handType = 6; // Full
            score = handType * base + sortedRanksByFreq[0] * 100 + sortedRanksByFreq[1];
            return { name: "Full", value: score, hand: hand };
        }
        if (isFlush) {
            handType = 5; // Couleur
            score = handType * base + rankValues.reduce((acc, v) => acc * 100 + v, 0);
            return { name: "Couleur", value: score, hand: hand };
        }
        if (isStraight) {
            handType = 4; // Quinte
            score = handType * base + sortedRanksByFreq[0];
            return { name: "Quinte", value: score, hand: hand };
        }
        if (counts[0] === 3) {
            handType = 3; // Brelan
            score = handType * base + sortedRanksByFreq[0] * 10000 + sortedRanksByFreq[1] * 100 + sortedRanksByFreq[2];
            return { name: "Brelan", value: score, hand: hand };
        }
        if (counts[0] === 2 && counts[1] === 2) {
            handType = 2; // Double Paire
            score = handType * base + sortedRanksByFreq[0] * 10000 + sortedRanksByFreq[1] * 100 + sortedRanksByFreq[2];
            return { name: "Double Paire", value: score, hand: hand };
        }
        if (counts[0] === 2) {
            handType = 1; // Paire
            score = handType * base + sortedRanksByFreq[0] * 1000000 + sortedRanksByFreq[1] * 10000 + sortedRanksByFreq[2] * 100 + sortedRanksByFreq[3];
            return { name: "Paire", value: score, hand: hand };
        }

        handType = 0; // Carte Haute
        score = handType * base + rankValues.reduce((acc, v) => acc * 100 + v, 0);
        return { name: "Carte Haute", value: score, hand: hand };
    }

    isStraight(rankValues) {
        const uniqueRanks = Array.from(new Set(rankValues)).sort((a, b) => a - b);
        if (uniqueRanks.length < 5) return false;

        // Cas spécial pour la quinte A-5 (As, 2, 3, 4, 5)
        const isAceLowStraight = JSON.stringify(uniqueRanks.slice(0, 4)) === JSON.stringify([0, 1, 2, 3]) && uniqueRanks.includes(rankToValue('A'));
        if (isAceLowStraight) {
             // Pour le scoring, on traite l'As comme la carte la plus basse.
             // On déplace l'As à la fin pour le tri.
             let ace = rankValues.pop();
             rankValues.unshift(ace);
             return true;
        }

        for (let i = 0; i <= uniqueRanks.length - 5; i++) {
            let isSequence = true;
            for (let j = 1; j < 5; j++) {
                if (uniqueRanks[i + j] !== uniqueRanks[i + j - 1] + 1) {
                    isSequence = false;
                    break;
                }
            }
            if (isSequence) return true;
        }

        return false;
    }
}

// --- Simulateur d'Équité (Monte Carlo) ---

function runEquitySimulation(hand1, hand2, board = [], iterations = 10000) {
    const deck = createDeck();

    // Retirer les cartes des mains et du board du paquet
    const knownCards = hand1.concat(hand2, board);
    const remainingDeck = deck.filter(card => !knownCards.includes(card));

    let stats = {
        player1Wins: 0,
        player2Wins: 0,
        ties: 0
    };

    for (let i = 0; i < iterations; i++) {
        // Mélanger le paquet restant (version simple : Fisher-Yates shuffle)
        for (let j = remainingDeck.length - 1; j > 0; j--) {
            const k = Math.floor(Math.random() * (j + 1));
            [remainingDeck[j], remainingDeck[k]] = [remainingDeck[k], remainingDeck[j]];
        }

        const boardSize = 5 - board.length;
        const randomBoard = remainingDeck.slice(0, boardSize);
        const fullBoard = board.concat(randomBoard);

        const hand1Rank = new HandEvaluator(hand1, fullBoard).handRank;
        const hand2Rank = new HandEvaluator(hand2, fullBoard).handRank;

        if (hand1Rank.value > hand2Rank.value) {
            stats.player1Wins++;
        } else if (hand2Rank.value > hand1Rank.value) {
            stats.player2Wins++;
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

console.log("poker.js chargé avec l'évaluateur de main complet et le simulateur.");

// --- Connexion UI ---

document.addEventListener('DOMContentLoaded', () => {
    const calculateBtn = document.getElementById('calculate-btn');
    const hand1Input = document.getElementById('hand1');
    const hand2Input = document.getElementById('hand2');
    const player1EquityDisplay = document.getElementById('player1-equity');
    const player2EquityDisplay = document.getElementById('player2-equity');
    const tieEquityDisplay = document.getElementById('tie-equity');

    function parseHand(handString) {
        if (!handString || handString.length !== 4) {
            alert("Format de main invalide. Entrez 4 caractères, ex: 'AsKd'.");
            return null;
        }
        // Basic validation to ensure cards are somewhat valid
        const hand = [handString.slice(0, 2), handString.slice(2, 4)];
        const validRanks = new Set(RANKS.split(''));
        const validSuits = new Set(SUITS.split(''));

        for (const card of hand) {
            if (!validRanks.has(card[0]) || !validSuits.has(card[1])) {
                 alert(`Carte invalide: ${card}.`);
                 return null;
            }
        }
        return hand;
    }

    calculateBtn.addEventListener('click', () => {
        const hand1Str = hand1Input.value.trim();
        const hand2Str = hand2Input.value.trim();

        const hand1 = parseHand(hand1Str);
        const hand2 = parseHand(hand2Str);

        if (!hand1 || !hand2) {
            return; // Stop if hands are invalid
        }

        // Basic check for duplicate cards
        const allCards = [hand1[0], hand1[1], hand2[0], hand2[1]];
        if (new Set(allCards).size !== 4) {
            alert("Les mains ne peuvent pas contenir de cartes identiques.");
            return;
        }

        // Mettre à jour l'UI pour montrer que le calcul est en cours
        player1EquityDisplay.textContent = "Calcul en cours...";
        player2EquityDisplay.textContent = "";
        tieEquityDisplay.textContent = "";

        // Utiliser setTimeout pour permettre à l'UI de se mettre à jour avant le calcul bloquant
        setTimeout(() => {
            const results = runEquitySimulation(hand1, hand2);
            player1EquityDisplay.textContent = `Main 1: ${results.player1Equity}%`;
            player2EquityDisplay.textContent = `Main 2: ${results.player2Equity}%`;
            tieEquityDisplay.textContent = `Égalité: ${results.tiePercentage}%`;
        }, 10);
    });
});
