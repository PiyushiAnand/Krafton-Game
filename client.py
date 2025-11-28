import asyncio
import websockets
import json
import pygame
import sys

WIDTH, HEIGHT = 800, 600
PLAYER_SIZE = 20
COIN_SIZE = 10
SERVER_URL = "ws://localhost:8765"

# Convert world coords (-10..10) to screen coords
def world_to_screen(x, y):
    return int(WIDTH/2 + x * 30), int(HEIGHT/2 - y * 30)

player_id = None
player_shape = "square"  # default shape
game_started = False
players = {}
scores = {}
coins = {}
player_shapes = {}  # store all players' shapes

# ---------- SELECT SHAPE ----------
def choose_shape():
    print("Choose your shape:")
    print("1: Square")
    print("2: Circle")
    print("3: Triangle")
    choice = input("Enter 1, 2, or 3: ").strip()
    if choice == "1":
        return "square"
    elif choice == "2":
        return "circle"
    elif choice == "3":
        return "triangle"
    else:
        print("Invalid choice, defaulting to square.")
        return "square"

# ---------- CLIENT ----------
async def game_client():
    global player_id, game_started, players, scores, coins, player_shape, player_shapes

    player_shape = choose_shape()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Multiplayer Game Client")

    clock = pygame.time.Clock()

    print("Connecting to server...")
    ws = await websockets.connect(SERVER_URL)
    print("Connected!")

    # Send chosen shape to server
    await ws.send(json.dumps({"type": "choose_shape", "shape": player_shape}))

    async def sender():
        """Send key input to server."""
        while True:
            await asyncio.sleep(0.03)  # 30 FPS input sending

            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                await ws.send(json.dumps({"type": "input", "input": "move_left"}))
            if keys[pygame.K_RIGHT]:
                await ws.send(json.dumps({"type": "input", "input": "move_right"}))
            if keys[pygame.K_UP]:
                await ws.send(json.dumps({"type": "input", "input": "move_up"}))
            if keys[pygame.K_DOWN]:
                await ws.send(json.dumps({"type": "input", "input": "move_down"}))

    asyncio.create_task(sender())

    font = pygame.font.SysFont(None, 30)

    while True:
        # Handle pygame quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                await ws.close()
                sys.exit()

        # Receive server updates
        try:
            message = await asyncio.wait_for(ws.recv(), timeout=0.01)
            data = json.loads(message)

            if data["type"] == "game_start":
                print("Game started!")
                game_started = True

            elif data["type"] == "state_update":
                players = data["players"]
                scores = data["scores"]
                coins = data["coins"]
                # optional: get shapes if server sends them
                if "shapes" in data:
                    player_shapes = data["shapes"]

        except asyncio.TimeoutError:
            pass  # Continue rendering even if no message

        # ---------- RENDER ----------
        screen.fill((20, 20, 20))

        # Draw coins
        for c in coins:
            sx, sy = world_to_screen(c["x"], c["y"])
            pygame.draw.circle(screen, (255, 215, 0), (sx, sy), COIN_SIZE)

        # Draw players
        for pid, pos in players.items():
            sx, sy = world_to_screen(pos["x"], pos["y"])
            # Get this player's shape
            shape = player_shapes.get(str(pid), "square") if player_shapes else "square"
            color = (0, 200, 255) if str(pid) == str(player_id) else (255, 80, 80)

            if shape == "square":
                pygame.draw.rect(screen, color, (sx, sy, PLAYER_SIZE, PLAYER_SIZE))
            elif shape == "circle":
                pygame.draw.circle(screen, color, (sx + PLAYER_SIZE//2, sy + PLAYER_SIZE//2), PLAYER_SIZE//2)
            elif shape == "triangle":
                points = [
                    (sx + PLAYER_SIZE//2, sy),
                    (sx, sy + PLAYER_SIZE),
                    (sx + PLAYER_SIZE, sy + PLAYER_SIZE)
                ]
                pygame.draw.polygon(screen, color, points)

        # Draw scoreboard
        y_offset = 10
        for pid, sc in scores.items():
            t = font.render(f"Player {pid}: {sc}", True, (255, 255, 255))
            screen.blit(t, (10, y_offset))
            y_offset += 25

        # Draw your coordinates
        my_pos = players.get(str(player_id), {"x":0,"y":0})
        coord_text = font.render(f"Your position: x={my_pos['x']:.2f}, y={my_pos['y']:.2f}", True, (255,255,255))
        screen.blit(coord_text, (10, HEIGHT - 30))

        pygame.display.flip()
        clock.tick(60)

# Run client
asyncio.run(game_client())
