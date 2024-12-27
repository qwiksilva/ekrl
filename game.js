// Establish WebSocket connection
const socket = new WebSocket('ws://localhost:3001');

// Local variable to track which player this browser instance is
let currentPlayer = null; // Will be set to either 1 or 2 based on server response

// Initial game state (empty until the server sends the real state)
let gameState = {
    deck: [],
    player1Hand: [],
    player2Hand: [],
    currentPlayer: 1
};

// Listen for messages from the server
socket.addEventListener('message', function(event) {
    const message = JSON.parse(event.data);

    switch (message.type) {
        case 'gameState':
            updateGameState(message.gameState);
            break;
        case 'assignPlayer':
            currentPlayer = message.player;
            console.log(`You are Player ${currentPlayer}`);
            break;
        default:
            break;
    }
});

// Update the game state
function updateGameState(newState) {
    gameState = newState;
    renderGame(); // Render the new game state in the browser
}

// Send a message to the server
function sendMessage(type, data) {
    socket.send(JSON.stringify({ type, ...data }));
}

// Draw a card
function drawCard() {
    sendMessage('drawCard', { player: currentPlayer });
}

// Play a card
function playCard(cardIndex) {
    sendMessage('playCard', { player: currentPlayer, cardIndex });
}

// Render the game state in the browser
function renderGame() {
    const deckElement = document.getElementById('deck');
    const deckCountElement = document.getElementById('deck-count');
    const player1HandElement = document.getElementById('player1-hand');
    const player2HandElement = document.getElementById('player2-hand');
    const turnIndicatorElement = document.getElementById('turn-indicator');

    // Update the turn indicator
    turnIndicatorElement.textContent = `Player ${gameState.currentPlayer}'s Turn`;

    // Update the deck count
    deckCountElement.textContent = `Cards left in deck: ${gameState.deck.length}`;

    // Render Player 1's Hand
    player1HandElement.innerHTML = ''; // Clear the current hand
    gameState.player1Hand.forEach((card, index) => {
        const cardDiv = document.createElement('div');
        cardDiv.classList.add('card');
        cardDiv.textContent = card;
        
        // Allow player 1 to play a card if it's their turn
        if (gameState.currentPlayer === 1 && currentPlayer === 1) {
            cardDiv.addEventListener('click', () => playCard(index));
        }

        player1HandElement.appendChild(cardDiv);
    });

    // Render Player 2's Hand
    player2HandElement.innerHTML = ''; // Clear the current hand
    gameState.player2Hand.forEach((card, index) => {
        const cardDiv = document.createElement('div');
        cardDiv.classList.add('card');
        cardDiv.textContent = card;

        // Allow player 2 to play a card if it's their turn
        if (gameState.currentPlayer === 2 && currentPlayer === 2) {
            cardDiv.addEventListener('click', () => playCard(index));
        }

        player2HandElement.appendChild(cardDiv);
    });

    // Enable drawing a card if it's the current player's turn
    if (gameState.currentPlayer === currentPlayer) {
        deckElement.addEventListener('click', drawCard);
    } else {
        deckElement.removeEventListener('click', drawCard);
    }
}

// Event listeners
document.getElementById('deck').addEventListener('click', drawCard);

// No need to render the game immediately, we'll wait for the server to send the initial game state.
