import asyncio
import websockets
import json
from aiohttp import web
from dataclasses import asdict
import logging
import argparse
import uuid

from ExplodingKittensSinglePlayerGym import ExplodingKittensSinglePlayerGym
from ExplodingKittensGame import Cards

clients = []
player_numbers = {}
current_player_number = 0

async def connection_handler(websocket, send_logs):
    global current_player_number

    player_number = gym.player_number
    current_player_number += 1

    # Send player assignment message
    await websocket.send(json.dumps({"type": "assignPlayer", "player": player_number, "client_id": player_number}))
    print(f"Player {player_number} connected with client_id {player_number}.")

    logs = []
    if send_logs:
        with open('ek_game_state.log', 'r') as f:
            logs = f.readlines()

    # Send the initial game state to the connected player
    state = json.dumps({"type": "gameState", "gameState": asdict(gym.game.game_state), "logs": logs})
    await websocket.send(state)

    clients.append(websocket)

    await game_handler(websocket, send_logs)

async def game_handler(websocket, send_logs):
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            data = json.loads(message)
            message_type = data.get("type")
            if message_type == "drawCard":
                player = data.get("player")
                action = Cards.num_playable_card_types()
                gym.step(action)
            elif message_type == "playCard":
                player = data.get("player")
                card = data.get("card")
                action = gym.card_to_int_mapping[card]
                gym.step(action)

            logs = []
            if send_logs:
                with open('ek_game_state.log', 'r') as f:
                    logs = f.readlines()
            
            # Broadcast the updated game state to all clients
            state = json.dumps({"type": "gameState", "gameState": asdict(gym.game.game_state), "logs": logs})
            await asyncio.wait([client.send(state) for client in clients])
    finally:
        del clients[websocket]

async def index(_request):
    return web.FileResponse('index.html')

async def init_app():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_static('/static/', path='./static', name='static')
    return app

async def main(send_logs):
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 3000)
    await site.start()

    async with websockets.serve(lambda ws: connection_handler(ws, send_logs), "localhost", 3001):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Exploding Kittens WebSocket server.")
    parser.add_argument('--send-logs', action='store_true', help="Flag to control whether to send logs to the client")
    args = parser.parse_args()

    with open('ek_game_state.log', 'w') as f:
        f.write("")

    logger = logging.getLogger('ExplodingKittensGame')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('ek_game_state.log')
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    gym_logger = logging.getLogger('ExplodingKittensSinglePlayerGym')
    gym_logger.setLevel(logging.DEBUG)
    gym_logger.addHandler(file_handler)
    
    gym = ExplodingKittensSinglePlayerGym(config_file="gym_config_single.json")
    gym.reset()
    asyncio.run(main(args.send_logs))
