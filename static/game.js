// Establish WebSocket connection
const socket = new WebSocket('ws://localhost:3001');

// Local variable to track which player this browser instance is
let currentPlayer = null; // Will be set to either 1 or 2 based on server response

// Initial game state (empty until the server sends the real state)
let gameState = {
    deck: [],
    player1Hand: [],
    player2Hand: [],
    currentPlayer: 0
};

// Listen for messages from the server
socket.addEventListener('message', function(event) {
    const message = JSON.parse(event.data);

    switch (message.type) {
        case 'gameState':
            updateGameState(message.gameState);
            displayLogs(message.logs);
            break;
        case 'assignPlayer':
            currentPlayer = message.player;
            console.log(`You are Player ${currentPlayer}`);
            break;
        default:
            break;
    }
});

// Display logs from the game server
function displayLogs(logs) {

    // Clear the logs displayed
    const logElement = document.getElementById('logs');
    logElement.innerHTML = '';

    logs.forEach(log => {
        const logDiv = document.createElement('div');
        logDiv.textContent = log;
        logElement.appendChild(logDiv);
    });
}

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
function playCard(card) {
    sendMessage('playCard', { player: currentPlayer, card });
}

// Render the game state in the browser
function renderGame() {
    const currentPlayerElement =  document.getElementById('current-player');
    const deckElement = document.getElementById('deck');
    const deckCountElement = document.getElementById('deck-count');
    const player1HandElement = document.getElementById('player1-hand');
    const player2HandElement = document.getElementById('player2-hand');
    const turnIndicatorElement = document.getElementById('turn-indicator');

    // Update the current player indicator
    currentPlayerElement.textContent = `You are Player ${currentPlayer}`;

    // Update the turn indicator
    turnIndicatorElement.textContent = `Player ${gameState.current_player}'s Turn`;

    // Update the deck count
    deckCountElement.textContent = `Cards left in deck: ${gameState.deck.length}`;

    // Render Player 1's Hand
    player1HandElement.innerHTML = ''; // Clear the current hand
    Object.entries(gameState.player_states[0].hand).forEach(([card, cardCount]) => {
        for (let i = 0; i < cardCount; i++) {
            const cardDiv = document.createElement('div');
            cardDiv.classList.add('card');
            cardDiv.textContent = card;

            // Allow player 1 to play a card if it's their turn
            if (gameState.current_player === 0 && currentPlayer === 0) {
                cardDiv.addEventListener('click', () => playCard(card));
            }

            player1HandElement.appendChild(cardDiv);
        }
    });

    // Render Player 2's Hand
    player2HandElement.innerHTML = ''; // Clear the current hand
    Object.entries(gameState.player_states[1].hand).forEach(([card, cardCount]) => {
        for (let i = 0; i < cardCount; i++) {
            const cardDiv = document.createElement('div');
            cardDiv.classList.add('card');
            cardDiv.textContent = card;

            // Allow player 2 to play a card if it's their turn
            if (gameState.current_player === 1 && currentPlayer === 1) {
                cardDiv.addEventListener('click', () => playCard(card));
            }

            player2HandElement.appendChild(cardDiv);
        }
    });

    // Enable drawing a card if it's the current player's turn
    if (gameState.current_player === currentPlayer) {
        deckElement.addEventListener('click', drawCard);
    } else {
        deckElement.removeEventListener('click', drawCard);
    }

    // Display the discard pile
    const discardPileElement = document.getElementById('discard-pile');
    discardPileElement.innerHTML = '';
    gameState.discard_pile.forEach(card => {
        const cardDiv = document.createElement('div');
        cardDiv.classList.add('card');
        cardDiv.textContent = card.replace('_', '\n');
        discardPileElement.appendChild(cardDiv);
    });

    // Check for a winner
    if (gameState.game_over) {
        
        // Display the winner
        turnIndicatorElement.textContent = `Player ${gameState.winner} wins!`;

        // Remove the event listener for drawing cards
        deckElement.removeEventListener('click', drawCard);

        // Remove the event listeners for playing cards
        player1HandElement.querySelectorAll('.card').forEach(cardDiv => {
            cardDiv.removeEventListener('click', playCard);
        });
        player2HandElement.querySelectorAll('.card').forEach(cardDiv => {
            cardDiv.removeEventListener('click', playCard);
        });

        // Add a play again button that sends a message to the server to start a new game by sending a 'reset' message to the server
        const playAgainButton = document.createElement('button');
        playAgainButton.textContent = 'Play Again';
        playAgainButton.addEventListener('click', () => {
            sendMessage('reset');
            if (playAgainButton) {
                playAgainButton.remove();
            }

            // clear logs displayed
            const logElement = document.getElementById('log');
            logElement.innerHTML = '';

        });
        document.body.appendChild(playAgainButton);

    }

}

// Event listeners
document.getElementById('deck').addEventListener('click', drawCard);

// No need to render the game immediately, we'll wait for the server to send the initial game state.
