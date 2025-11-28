
1. Lobby: Two clients must connect to a game server. The server can wait for input or
auto-start the game session.
2. Gameplay:
○ Each player controls a basic shape (cube, circle, etc.).
○ Coins spawn at random map positions every few seconds.
○ When a player touches a coin, it disappears and that player’s score increases.
3. Server Authority:
○ The server is authoritative for player positions, coin positions, and scoring.
○ Clients may only send intent or input (e.g., “move left”).
○ The server resolves collisions and validates score events.# Krafton-Game
