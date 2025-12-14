import json
import time

STORAGE_KEY = "maze_leaderboard"

def load_leaderboard():
    try:
        import js
        raw = js.window.localStorage.getItem(STORAGE_KEY)
        return json.loads(raw) if raw else {}
    except:
        try:
            with open("leaderboard.json", "r") as f:
                return json.load(f)
        except:
            return {}

def save_leaderboard(data):
    try:
        import js
        js.window.localStorage.setItem(STORAGE_KEY, json.dumps(data))
    except ImportError:
        try:
            with open("leaderboard.json", "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Save failed: {e}")

def add_score(seed, name, score, time_taken):
    data = load_leaderboard()

    entry = {
        "name": name,
        "score": round(score, 2),
        "time": round(time_taken, 2),
        "timestamp": int(time.time())
    }

    data.setdefault(seed, []).append(entry)

    data[seed].sort(
        key=lambda x: (-x["score"], x["time"])
    )

    save_leaderboard(data)

def get_scores(seed):
    data = load_leaderboard()
    return data.get(seed, [])
