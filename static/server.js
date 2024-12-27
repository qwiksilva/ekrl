const express = require('express');
const WebSocket = require('ws');
const http = require('http');

// Set up an Express server
const app = express();
const server = http.createServer(app);

// Serve the static files for the game
app.use(express.static('public'));

// Set up the WebSocket server
const wss = new WebSocket.Server({ server });

// Store connected players
let players = {};

// Store game state
let gameState = {
    deck: [
        'Skip', 'Defuse', 'Attack', 'Shuffle', 'See Future', 'Nope',
        'Skip', 'Defuse', 'Attack', 'Shuffle', 'See Future', 'Nope',
        'Skip', 'Defuse', 'Attack', 'Shuffle', 'See Future', 'Explode',
        'Defuse', 'Defuse', 'Nope'
    ],
    player1Hand: [],
    player2Hand: [],
    currentPlayer: 1 // Player 1 starts first
};

// Broadcast the updated game state to all clients
function broadcastGameState() {
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({ type: 'gameState', gameState }));
        }
    });
}

// Handle WebSocket connections
wss.on('connection', (ws) => {
    // Assign player number
    let playerNumber = Object.keys(players).length + 1;
    if (playerNumber > 2) {
        ws.send(JSON.stringify({ type: 'error', message: 'Game already in progress.' }));
        return ws.close();
    }

    players[playerNumber] = ws;
    ws.send(JSON.stringify({ type: 'assignPlayer', player: playerNumber }));
    console.log(`Player ${playerNumber} connected.`);

    // Send the initial game state to the connected player
    ws.send(JSON.stringify({ type: 'gameState', gameState }));

    // Handle messages from clients
    ws.on('message', (message) => {
        const data = JSON.parse(message);

        switch (data.type) {
            case 'drawCard':
                handleDrawCard(data.player);
                break;
            case 'playCard':
                handlePlayCard(data.player, data.cardIndex);
                break;
            default:
                break;
        }
    });

    ws.on('close', () => {
        console.log(`Player ${playerNumber} disconnected.`);
        delete players[playerNumber];
    });
});

// Handle drawing a card
function handleDrawCard(player) {
    if (gameState.deck.length > 0 && player === gameState.currentPlayer) {
        const card = gameState.deck.pop();
        if (player === 1) {
            gameState.player1Hand.push(card);
        } else {
            gameState.player2Hand.push(card);
        }
        // Switch turn to the other player
        gameState.currentPlayer = player === 1 ? 2 : 1;

        // Broadcast updated game state to all players
        broadcastGameState();
    }
}

// Handle playing a card (you can implement the specific card logic here)
function handlePlayCard(player, cardIndex) {
    let playerHand = player === 1 ? gameState.player1Hand : gameState.player2Hand;

    // Check if it's the correct player's turn
    if (player === gameState.currentPlayer && cardIndex >= 0 && cardIndex < playerHand.length) {
        const card = playerHand.splice(cardIndex, 1)[0];

        // Implement card-specific logic here (Skip, Attack, etc.)
        switch (card) {
            case 'Skip':
                // Skip turns, move to the next player
                gameState.currentPlayer = player === 1 ? 2 : 1;
                break;
            case 'Attack':
                // Attack logic - opponent must take two turns (you can customize this)
                gameState.currentPlayer = player === 1 ? 2 : 1;
                break;
            case 'Shuffle':
                // Shuffle the deck
                gameState.deck.sort(() => Math.random() - 0.5);
                break;
            case 'See Future':
                // Show the top three cards to the player (implement the logic as needed)
                break;
            default:
                break;
        }

        // Broadcast updated game state to all players
        broadcastGameState();
    }
}

// Start the server
server.listen(3000, () => {
    console.log('Server started on http://localhost:3000');
});
