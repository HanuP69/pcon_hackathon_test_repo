# 🎨 CAT & MAZE
**Where Graph Theory meets Pixel Art (and Cats 🐱)**

Catventure Maz is an interactive maze-solving game and algorithm-visualization sandbox that blends **graph algorithms**, **game design**, and **procedural generation**.  
Players navigate mazes as a pixel-art cat while observing how classical pathfinding algorithms behave under real gameplay constraints.

This project turns abstract concepts like **BFS**, **A\***, **state-space expansion**, and **constraint-based shortest paths** into something visual, playable, and intuitive.

---

## 🧠 Algorithms (The Brain)

Every maze is modeled as a **grid graph**:
- Each cell is a node
- Adjacent walkable cells form edges
- Walls, portals, and wall-breaking constraints modify traversal rules

---

### 1️⃣ Breadth-First Search (BFS)

- **Concept:** Level-order exploration (flood fill)
- **Guarantee:** Finds the shortest path in an unweighted graph
- **Usage in Project:**
  - Baseline for optimal path length
  - Map solvability validation
  - Player scoring reference

**In-game:**  
Press **`B`** to visualize BFS shortest path (pink).

---

### 2️⃣ A* Search (A-Star)

- **Concept:** Heuristic-guided shortest path search
- **Heuristic Used:** Manhattan Distance h(x,y) = |x-x_goal| + |y-y_goal|
- **Benefit:** Explores fewer states than BFS in most cases

**In-game:**  
Press **`H`** to visualize A* path (blue).

---

### 3️⃣ The K-Break Problem (Wall Breaking)

- Players can break up to **K walls**
- Each search state becomes: (x,y,used_breaks)
  - This creates a **layered state graph**, where the same cell may be visited multiple times with different remaining resources

Both BFS and A* are adapted to support this constraint.

---

### 4️⃣ Portals

- Up to **10 portal pairs**, each color-coded
- Stepping on a portal teleports the player to its paired location
- Introduces **non-local edges**, converting the maze into a general graph

---

## 🧩 Maze Generation

### Random Maps

Instead of generating perfect mazes, the game uses **constraint-based random generation**:

1. Random placement of walls, empty cells, and portals
2. Random or fixed `K` value
3. BFS validation for solvability
4. Rejection of invalid layouts

This allows:
- Cycles
- Multiple valid solutions
- Strategic wall breaks and portal shortcuts

Every generated map is **guaranteed solvable**.

---

### Editor Mode

Players can design custom mazes using a paint-style editor:

- White → Walkable
- Black → Wall
- **S** → Start (exactly one)
- **G** → Goal (exactly one)
- 10 portal colors (each must appear exactly twice)
- Adjustable **K value**

Publishing a map:
- Runs BFS to verify solvability
- Generates a shareable **seed**

---

## 💾 MS2 Seed Protocol (Serialization)

Custom maps are encoded into a compact, shareable string.

### Encoding Steps

1. Flatten grid into a character stream
2. Apply **Run-Length Encoding (RLE)**
3. Encode with **URL-safe Base64**
4. Attach metadata

### Format
```MS2|20x20|K|<Base64Payload>```

- `MS2` → Protocol version
- `20x20` → Grid size
- `K` → Max wall breaks
- `Payload` → Encoded map data

Seeds can be:
- Copied manually
- Pasted into the loader
- Used as leaderboard identifiers

---

## 🗂️ Architecture

The game uses a **state-driven architecture**:

- `WELCOME`
- `NAME`
- `MODE`
- `PLAY`
- `EDITOR`
- `LOAD`

Each screen manages its own:
- Input handling
- Update logic
- Rendering

This keeps logic isolated and prevents cross-state bugs.

---

## 🏆 Scoring & Leaderboard

For each completed maze:

- **Score Formula** :Score = (BFS_optimal_steps / Player_steps) × 100
  - **Time Taken** is recorded
- Scores are stored locally in JSON
- Leaderboard is grouped by seed and sorted by score

**In-game:**  
Press **`TAB`** to view leaderboard.

---

## 🎨 Visuals

- Pixel-art aesthetic
- Grid-aligned rendering
- Path overlays:
- BFS → Pink
- A* → Blue
- Player → Yellow
- Dynamic scaling for different grid sizes

---

## 🕹️ Controls

| Action | Key |
|------|----|
| Move | `W A S D` / Arrow Keys |
| Break Wall | `SHIFT + Move` |
| Use Portal | `ENTER` |
| Toggle BFS | `B` |
| Toggle A* | `H` |
| Leaderboard | `TAB` |
| Reset Map | `R` |
| Publish (Editor) | `P` |

---

## 🚀 Running the Project

### Web Version (Recommended)

Uses **Pygbag (PyBag)** to run directly in the browser.

```bash
pip install pygame pygbag
pygbag .
http://localhost:8000
```
itch.io link (deployed) : https://tan69.itch.io/maze-game-test




