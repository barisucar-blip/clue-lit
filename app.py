import streamlit as st
import random
import string

# ---------------------------
# Constants
# ---------------------------
BOARD_SIZE   = 4
MAX_ATTEMPTS = 3

# Points awarded based on which attempt the player wins on
SCORE_MAP = {1: 10, 2: 5, 3: 3}

# Session state keys
KEY_STAGE       = "stage"         # "home" | "game" | "result"
KEY_ATTEMPTS    = "attempts"
KEY_BOARD       = "board"
KEY_TARGET_WORD = "target_word"
KEY_CLUE        = "clue"
KEY_HISTORY     = "history"
KEY_GUESS_KEY   = "guess_key"     # incremented to clear text input
KEY_LAST_MSG    = "last_msg"      # ("type", "text") shown on result page
KEY_USED_WORDS  = "used_words"    # tracks words already played this session
KEY_TOTAL_SCORE = "total_score"   # cumulative score across all games

WORDS = [
    {"word": "STONE",  "clue": {"length": 5, "category": "Nature"}},
    {"word": "PLANET", "clue": {"length": 6, "category": "Space"}},
    {"word": "TIGER",  "clue": {"length": 5, "category": "Animals"}},
    {"word": "FLAME",  "clue": {"length": 5, "category": "Nature"}},
    {"word": "ORBIT",  "clue": {"length": 5, "category": "Space"}},
    {"word": "CRANE",  "clue": {"length": 5, "category": "Animals"}},
    {"word": "FROST",  "clue": {"length": 5, "category": "Nature"}},
    {"word": "COMET",  "clue": {"length": 5, "category": "Space"}},
]

# ---------------------------
# Initialize Session State
# ---------------------------
for key, default in [
    (KEY_STAGE,       "home"),
    (KEY_ATTEMPTS,    0),
    (KEY_BOARD,       []),
    (KEY_TARGET_WORD, ""),
    (KEY_CLUE,        {}),
    (KEY_HISTORY,     []),
    (KEY_GUESS_KEY,   0),
    (KEY_LAST_MSG,    None),
    (KEY_USED_WORDS,  []),
    (KEY_TOTAL_SCORE, 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ---------------------------
# Board Generator
# ---------------------------
def generate_board(word: str) -> list[list[str]]:
    """Place word letters on grid preferring adjacent cells; fill rest randomly."""
    board = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    r = random.randint(0, BOARD_SIZE - 1)
    c = random.randint(0, BOARD_SIZE - 1)
    board[r][c] = word[0]

    for letter in word[1:]:
        neighbors = [
            (r + dr, c + dc)
            for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]
            if 0 <= r+dr < BOARD_SIZE and 0 <= c+dc < BOARD_SIZE and board[r+dr][c+dc] == ""
        ]
        if neighbors:
            r, c = random.choice(neighbors)
        else:
            empty_cells = [(i,j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if board[i][j] == ""]
            if not empty_cells:
                break
            r, c = random.choice(empty_cells)
        board[r][c] = letter

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == "":
                board[i][j] = random.choice(string.ascii_uppercase)
    return board


# ---------------------------
# DFS Word Check
# ---------------------------
def word_exists(board: list[list[str]], word: str) -> bool:
    """Return True if word can be traced on board via adjacent non-reused cells."""
    rows, cols = len(board), len(board[0]) if board else 0
    visited = [[False]*cols for _ in range(rows)]

    def dfs(r, c, idx):
        if idx == len(word): return True
        if not (0 <= r < rows and 0 <= c < cols): return False
        if visited[r][c] or board[r][c] != word[idx]: return False
        visited[r][c] = True
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            if dfs(r+dr, c+dc, idx+1):
                visited[r][c] = False
                return True
        visited[r][c] = False
        return False

    return any(dfs(i, j, 0) for i in range(rows) for j in range(cols))


# ---------------------------
# Input Sanitizer
# ---------------------------
def sanitize_guess(raw: str) -> str:
    return "".join(filter(str.isalpha, raw)).upper()


# ---------------------------
# Progressive Clue Helper
# ---------------------------
def get_bonus_clues(target: str, attempts_used: int) -> list[str]:
    """
    Return bonus clues revealed after each failed attempt.
    After attempt 1: starting letter.
    After attempt 2: a random middle letter with its position.
    """
    clues = []
    if attempts_used >= 1:
        clues.append(f"🔡 **Starting letter:** {target[0]}")
    if attempts_used >= 2:
        # Pick a middle letter (not first or last)
        mid_idx = len(target) // 2
        clues.append(f"🔠 **Letter {mid_idx + 1} in the word:** {target[mid_idx]}")
    return clues


# ---------------------------
# Pick a word not yet played
# ---------------------------
def pick_unused_word() -> dict:
    used = st.session_state[KEY_USED_WORDS]
    available = [w for w in WORDS if w["word"] not in used]
    if not available:
        st.session_state[KEY_USED_WORDS] = []
        available = WORDS
    chosen = random.choice(available)
    st.session_state[KEY_USED_WORDS].append(chosen["word"])
    return chosen


# ---------------------------
# Stage Transitions
# ---------------------------
def go_home():
    st.session_state[KEY_STAGE]    = "home"
    st.session_state[KEY_LAST_MSG] = None

def start_new_game():
    level = pick_unused_word()
    st.session_state[KEY_TARGET_WORD] = level["word"].upper()
    st.session_state[KEY_CLUE]        = level["clue"]
    st.session_state[KEY_BOARD]       = generate_board(level["word"].upper())
    st.session_state[KEY_ATTEMPTS]    = 0
    st.session_state[KEY_GUESS_KEY]  += 1
    st.session_state[KEY_LAST_MSG]    = None
    st.session_state[KEY_STAGE]       = "game"

def go_result(msg_type: str, msg_text: str, history_entry: dict):
    st.session_state[KEY_HISTORY].append(history_entry)
    st.session_state[KEY_LAST_MSG] = (msg_type, msg_text)
    st.session_state[KEY_STAGE]    = "result"


# ---------------------------
# Shared CSS
# ---------------------------
st.markdown("""
<style>
    .big-title  { font-size: clamp(28px, 8vw, 48px); font-weight: 800; text-align: center; margin-bottom: 0.2em; }
    .subtitle   { text-align: center; color: #666; margin-bottom: 1.5em; font-size: clamp(14px, 4vw, 18px); }
    .board-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        max-width: 280px;
        width: 100%;
        margin: 0 auto 1.2rem auto;
    }
    .board-cell {
        display: flex; align-items: center; justify-content: center;
        font-size: clamp(18px, 6vw, 28px); font-weight: bold;
        border: 2px solid #ccc; border-radius: 8px;
        background: #f9f9f9; aspect-ratio: 1;
    }
    .clue-box {
        background: #f0f4ff; border-radius: 10px;
        padding: 12px 18px; margin-bottom: 0.6rem;
        font-size: clamp(14px, 4vw, 16px);
    }
    .bonus-clue-box {
        background: #fffbe6; border: 1px solid #f6d860;
        border-radius: 10px; padding: 10px 16px;
        margin-bottom: 0.6rem; font-size: clamp(13px, 3.8vw, 15px);
    }
    .attempt-bar   { text-align: center; font-size: 15px; color: #444; margin-bottom: 0.8rem; }
    .score-badge   {
        display: inline-block; background: #4CAF50; color: white;
        font-weight: bold; border-radius: 20px;
        padding: 4px 14px; font-size: clamp(13px, 4vw, 16px);
        margin-bottom: 0.5rem;
    }
    .history-row   { font-size: clamp(13px, 3.5vw, 15px); padding: 4px 0; }
    .total-score   {
        font-size: clamp(20px, 6vw, 28px); font-weight: 800;
        text-align: center; color: #4CAF50; margin: 0.5rem 0 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ==============================
# STAGE 1 — HOME
# ==============================
if st.session_state[KEY_STAGE] == "home":

    st.markdown('<div class="big-title">Project Clue</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">A word tracing puzzle game</div>', unsafe_allow_html=True)

    st.markdown("### How to play")
    st.markdown(
        f"1. You'll see a **4×4 grid** of letters.\n"
        f"2. Use the clues to guess the hidden word.\n"
        f"3. Your word must be traceable by moving to **adjacent cells** "
        f"(up, down, left, right) — you cannot reuse the same cell.\n"
        f"4. You have **{MAX_ATTEMPTS} attempts** per round.\n"
        f"5. **Bonus clues unlock as you fail:**\n"
        f"   - ❌ After attempt 1: the **starting letter** is revealed.\n"
        f"   - ❌ After attempt 2: a **middle letter** and its position are revealed.\n"
        f"6. **Scoring:** Guess on attempt 1 = **10 pts** · attempt 2 = **5 pts** · attempt 3 = **3 pts**.\n"
        f"7. Try to score as high as possible!"
    )

    st.write("")
    if st.button("▶️ Start New Game", use_container_width=True):
        start_new_game()
        st.rerun()

    if st.session_state[KEY_HISTORY]:
        st.divider()
        wins  = sum(1 for h in st.session_state[KEY_HISTORY] if h["result"] == "win")
        total = len(st.session_state[KEY_HISTORY])
        st.markdown(f"**Your record this session:** {wins}W / {total - wins}L")
        st.markdown(f'<div class="total-score">🏆 Total Score: {st.session_state[KEY_TOTAL_SCORE]} pts</div>', unsafe_allow_html=True)


# ==============================
# STAGE 2 — GAME
# ==============================
elif st.session_state[KEY_STAGE] == "game":

    st.markdown('<div class="big-title">Project Clue</div>', unsafe_allow_html=True)

    # Board
    cell_html = "".join(
        f'<div class="board-cell">{letter}</div>'
        for row in st.session_state[KEY_BOARD]
        for letter in row
    )
    st.markdown(f'<div class="board-grid">{cell_html}</div>', unsafe_allow_html=True)

    # Base clues
    clue     = st.session_state[KEY_CLUE]
    attempts = st.session_state[KEY_ATTEMPTS]
    target   = st.session_state[KEY_TARGET_WORD]

    st.markdown(
        f'<div class="clue-box">'
        f'🔤 <b>Length:</b> {clue["length"]} letters &nbsp;|&nbsp; '
        f'📂 <b>Category:</b> {clue["category"]}'
        f'</div>',
        unsafe_allow_html=True
    )

    # Progressive bonus clues (shown after each failed attempt)
    bonus_clues = get_bonus_clues(target, attempts)
    if bonus_clues:
        for bc in bonus_clues:
            st.markdown(f'<div class="bonus-clue-box">{bc}</div>', unsafe_allow_html=True)

    # Attempts indicator + points preview
    remaining = MAX_ATTEMPTS - attempts
    circles   = "🟢" * remaining + "🔴" * attempts
    pts_next  = SCORE_MAP.get(attempts + 1, 0)
    st.markdown(
        f'<div class="attempt-bar">{circles} &nbsp; {attempts}/{MAX_ATTEMPTS} used'
        f' &nbsp;|&nbsp; Next correct guess = <b>{pts_next} pts</b></div>',
        unsafe_allow_html=True
    )

    # Guess input
    guess_input = st.text_input(
        "Enter your guess:",
        key=f"guess_input_{st.session_state[KEY_GUESS_KEY]}"
    )

    if st.button("Submit Guess ➜", use_container_width=True):
        if attempts >= MAX_ATTEMPTS:
            st.error("No attempts left!")
        else:
            guess = sanitize_guess(guess_input)

            if not guess:
                st.warning("Please enter a word.")
            elif len(guess) != clue["length"]:
                st.warning(f"Wrong length — expected {clue['length']} letters.")
            else:
                st.session_state[KEY_ATTEMPTS] += 1
                st.session_state[KEY_GUESS_KEY] += 1
                attempt_number = st.session_state[KEY_ATTEMPTS]

                if guess == target and word_exists(st.session_state[KEY_BOARD], guess):
                    pts = SCORE_MAP.get(attempt_number, 0)
                    st.session_state[KEY_TOTAL_SCORE] += pts
                    go_result(
                        "win",
                        f"🎉 Correct! You found **{target}** on attempt {attempt_number} — **+{pts} points!**",
                        {"word": target, "result": "win", "attempts": attempt_number, "points": pts}
                    )
                    st.rerun()

                elif attempt_number >= MAX_ATTEMPTS:
                    go_result(
                        "loss",
                        f"💀 Out of attempts! The word was **{target}**. No points this round.",
                        {"word": target, "result": "loss", "attempts": attempt_number, "points": 0}
                    )
                    st.rerun()

                elif word_exists(st.session_state[KEY_BOARD], guess):
                    st.error("That word exists on the board but isn't the answer. Try again!")
                else:
                    st.error("Word cannot be formed from the board. Try again!")

    if st.button("🏠 Back to Home", use_container_width=True):
        go_home()
        st.rerun()


# ==============================
# STAGE 3 — RESULT
# ==============================
elif st.session_state[KEY_STAGE] == "result":

    st.markdown('<div class="big-title">Project Clue</div>', unsafe_allow_html=True)

    # Win/loss message
    msg = st.session_state[KEY_LAST_MSG]
    if msg:
        if msg[0] == "win":
            st.success(msg[1])
        else:
            st.error(msg[1])

    # Total score display
    st.markdown(
        f'<div class="total-score">🏆 Total Score: {st.session_state[KEY_TOTAL_SCORE]} pts</div>',
        unsafe_allow_html=True
    )

    # Play again / go home
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Play Again", use_container_width=True):
            start_new_game()
            st.rerun()
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            go_home()
            st.rerun()

    # Session History
    st.divider()
    st.markdown("### 📊 Session History")
    history = st.session_state[KEY_HISTORY]
    wins    = sum(1 for h in history if h["result"] == "win")
    total   = len(history)
    st.markdown(f"**Record: {wins} wins / {total - wins} losses** out of {total} games")

    st.write("")
    for i, h in enumerate(reversed(history), 1):
        icon = "✅" if h["result"] == "win" else "❌"
        pts  = h.get("points", 0)
        pts_label = f" · **+{pts} pts**" if pts > 0 else " · *0 pts*"
        st.markdown(
            f'<div class="history-row">{icon} Game {total - i + 1}: '
            f'<code>{h["word"]}</code> — attempt {h["attempts"]}{pts_label}</div>',
            unsafe_allow_html=True
        )
