# server.py
import asyncio
import websockets
import json
import random
import time

LOBBY_SIZE = 2
PLAYER_SPEED = 0.1
MAP_SIZE = 10
COIN_SPAWN_INTERVAL = 3  # seconds

connected_clients = {}
player_positions = {}
player_scores = {}
player_shapes = {}  # store each player's chosen shape
coins = []
game_started = False
last_coin_time = time.time()

# ---------- BROADCAST ----------
async def broadcast(message):
    if connected_clients:
        await asyncio.gather(
            *(ws.send(json.dumps(message)) for ws in connected_clients.values())
        )

# ---------- SPAWN COINS ----------
async def spawn_coin():
    coins.append({
        "x": random.uniform(-MAP_SIZE, MAP_SIZE),
        "y": random.uniform(-MAP_SIZE, MAP_SIZE)
    })

# ---------- GAME LOOP ----------
async def game_loop():
    global last_coin_time
    
    while True:
        await asyncio.sleep(0.05)  # 20 updates per second

        # Spawn coins
        if time.time() - last_coin_time > COIN_SPAWN_INTERVAL:
            await spawn_coin()
            last_coin_time = time.time()

        # Send game state to all players
        state = {
            "type": "state_update",
            "players": player_positions,
            "scores": player_scores,
            "coins": coins,
            "shapes": player_shapes
        }
        await broadcast(state)

# ---------- HANDLE CLIENT ----------
async def handle_client(ws):
    global game_started

    # Assign player id
    player_id = len(connected_clients) + 1
    connected_clients[player_id] = ws
    player_positions[player_id] = {"x": 0.0, "y": 0.0}
    player_scores[player_id] = 0
    player_shapes[player_id] = "square"  # default shape

    print(f"Player {player_id} joined")

    # Lobby: wait until 2 players connected
    if len(connected_clients) == LOBBY_SIZE and not game_started:
        game_started = True
        print("Game started!")
        await broadcast({"type": "game_start"})
        asyncio.create_task(game_loop())

    # Listen for inputs
    try:
        async for msg in ws:
            data = json.loads(msg)

            # ---------- INPUT ----------
            if data["type"] == "input":
                inp = data["input"]

                # Move player
                if inp == "move_left":
                    player_positions[player_id]["x"] -= PLAYER_SPEED
                elif inp == "move_right":
                    player_positions[player_id]["x"] += PLAYER_SPEED
                elif inp == "move_up":
                    player_positions[player_id]["y"] += PLAYER_SPEED
                elif inp == "move_down":
                    player_positions[player_id]["y"] -= PLAYER_SPEED

                # Collision with coins
                to_remove = []
                for i, c in enumerate(coins):
                    if abs(c["x"] - player_positions[player_id]["x"]) < 0.5 and \
                       abs(c["y"] - player_positions[player_id]["y"]) < 0.5:
                        to_remove.append(i)
                        player_scores[player_id] += 1

                for i in sorted(to_remove, reverse=True):
                    coins.pop(i)

            # ---------- SHAPE SELECTION ----------
            elif data["type"] == "choose_shape":
                shape = data.get("shape", "square")
                player_shapes[player_id] = shape
                print(f"Player {player_id} chose shape: {shape}")

    except websockets.ConnectionClosed:
        print(f"Player {player_id} disconnected")

        del connected_clients[player_id]
        del player_positions[player_id]
        del player_scores[player_id]
        del player_shapes[player_id]

# ---------- START SERVER ----------
async def main():
    async with websockets.serve(handle_client, "localhost", 8765):
        print("Server running on ws://localhost:8765")
        await asyncio.Future()  # run forever

asyncio.run(main())
