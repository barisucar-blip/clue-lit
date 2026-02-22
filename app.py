import streamlit as st
import random
import string

# ---------------------------
# Constants
# ---------------------------
BOARD_SIZE = 4
MAX_ATTEMPTS = 5

KEY_GAME_STARTED = "game_started"
KEY_ATTEMPTS = "attempts"
KEY_BOARD = "board"
KEY_TARGET_WORD = "target_word"
KEY_CLUE = "clue"
KEY_HISTORY = "history"

WORDS = [
    {"word": "STONE", "clue": {"length": 5, "starts_with": "S", "contains": "T", "category": "Nature"}},
    {"word": "PLANET", "clue": {"length": 6, "starts_with": "P", "contains": "N", "category": "Space"}},
    {"word": "TIGER", "clue": {"length": 5, "starts_with": "T", "contains": "G", "category": "Animals"}},
]

# ---------------------------
# Initialize Session State
# ---------------------------
for key, default in [
    (KEY_GAME_STARTED, False),
    (KEY_ATTEMPTS, 0),
    (KEY_BOARD, []),
    (KEY_TARGET_WORD, ""),
    (KEY_CLUE, {}),
    (KEY_HISTORY, []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------
# Board Generator
# ---------------------------
def generate_board(word: str) -> list[list[str]]:
    """
    Place each letter of `word` on a BOARD_SIZE x BOARD_SIZE grid,
    preferring adjacent cells. Remaining cells are filled with random letters.
    Returns a 2D list of uppercase characters.
    """
    board = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    r = random.randint(0, BOARD_SIZE - 1)
    c = random.randint(0, BOARD_SIZE - 1)
    board[r][c] = word[0]

    for letter in word[1:]:
        neighbors = [
            (r + dr, c + dc)
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]
            if 0 <= r + dr < BOARD_SIZE and 0 <= c + dc < BOARD_SIZE and board[r + dr][c + dc] == ""
        ]

        if neighbors:
            r, c = random.choice(neighbors)
        else:
            empty_cells = [
                (i, j)
                for i in range(BOARD_SIZE)
                for j in range(BOARD_SIZE)
                if board[i][j] == ""
            ]
            if not empty_cells:
                break  # Board full — word too long for grid
            r, c = random.choice(empty_cells)

        board[r][c] = letter

    # Fill remaining empty cells with random letters
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == "":
                board[i][j] = random.choice(string.ascii_uppercase)

    return board


# ---------------------------
# DFS Check
# ---------------------------
def word_exists(board: list[list[str]], word: str) -> bool:
    """
    Returns True if `word` can be traced on `board` by moving to
    adjacent (up/down/left/right) cells without reusing any cell.
    Derives board dimensions from the board itself for flexibility.
    """
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0
    visited = [[False] * cols for _ in range(rows)]

    def dfs(r, c, index):
        if index == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if visited[r][c] or board[r][c] != word[index]:
            return False

        visited[r][c] = True
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if dfs(r + dr, c + dc, index + 1):
                visited[r][c] = False
                return True
        visited[r][c] = False
        return False

    for i in range(rows):
        for j in range(cols):
            if dfs(i, j, 0):
                return True
    return False


# ---------------------------
# Input Sanitizer
# ---------------------------
def sanitize_guess(raw: str) -> str:
    """Strip non-alpha characters and uppercase the result."""
    return "".join(filter(str.isalpha, raw)).upper()


# ---------------------------
# UI
# ---------------------------
st.title("🔎 Clueless Game")

if st.button("Start New Game"):
    level = random.choice(WORDS)
    st.session_state[KEY_TARGET_WORD] = level["word"].upper()
    st.session_state[KEY_CLUE] = level["clue"]
    st.session_state[KEY_BOARD] = generate_board(st.session_state[KEY_TARGET_WORD])
    st.session_state[KEY_ATTEMPTS] = 0
    st.session_state[KEY_GAME_STARTED] = True

# ---------------------------
# Display Game
# ---------------------------
if st.session_state[KEY_GAME_STARTED]:

    st.subheader("Board")
    cols = st.columns(BOARD_SIZE)
    for row in st.session_state[KEY_BOARD]:
        for col_widget, letter in zip(cols, row):
            col_widget.markdown(
                f"<div style='text-align:center; font-size:24px; font-weight:bold; "
                f"padding:10px; border:1px solid #ccc; border-radius:6px;'>{letter}</div>",
                unsafe_allow_html=True,
            )

    st.subheader("Clues")
    clue = st.session_state[KEY_CLUE]
    st.write("Length:", clue["length"])
    st.write("Starts with:", clue["starts_with"])
    st.write("Contains letter:", clue["contains"])
    st.write("Category:", clue["category"])

    st.write(f"**Attempts:** {st.session_state[KEY_ATTEMPTS]}/{MAX_ATTEMPTS}")

    guess_input = st.text_input("Enter your guess:")

    if st.button("Submit Guess"):
        # Block submission if out of attempts
        if st.session_state[KEY_ATTEMPTS] >= MAX_ATTEMPTS:
            st.error("No attempts left! Start a new game.")
        else:
            guess = sanitize_guess(guess_input)

            # --- Format checks (don't cost an attempt) ---
            if not guess:
                st.warning("Please enter a word.")
            elif len(guess) != clue["length"]:
                st.warning(f"Wrong length — expected {clue['length']} letters.")
            elif not guess.startswith(clue["starts_with"]):
                st.warning(f"Word must start with '{clue['starts_with']}'.")
            elif clue["contains"] not in guess:
                st.warning(f"Word must contain the letter '{clue['contains']}'.")
            else:
                # Only increment attempts for a properly formatted guess
                st.session_state[KEY_ATTEMPTS] += 1

                target = st.session_state[KEY_TARGET_WORD]

                if guess == target and word_exists(st.session_state[KEY_BOARD], guess):
                    st.success("🎉 Correct! You found the word!")
                    st.session_state[KEY_HISTORY].append({"word": target, "result": "win", "attempts": st.session_state[KEY_ATTEMPTS]})
                    st.session_state[KEY_GAME_STARTED] = False
                elif word_exists(st.session_state[KEY_BOARD], guess):
                    st.error("That word exists on the board but isn't the answer. Try again!")
                else:
                    st.error("Word cannot be formed from the board.")

                # Check game over after incrementing
                if st.session_state[KEY_ATTEMPTS] >= MAX_ATTEMPTS and st.session_state[KEY_GAME_STARTED]:
                    st.error(f"💀 Game Over! The word was: **{target}**")
                    st.session_state[KEY_HISTORY].append({"word": target, "result": "loss", "attempts": st.session_state[KEY_ATTEMPTS]})
                    st.session_state[KEY_GAME_STARTED] = False

# ---------------------------
# History / Score Tracker
# ---------------------------
if st.session_state[KEY_HISTORY]:
    st.divider()
    st.subheader("📊 Session History")
    wins = sum(1 for h in st.session_state[KEY_HISTORY] if h["result"] == "win")
    total = len(st.session_state[KEY_HISTORY])
    st.write(f"Record: **{wins} wins / {total - wins} losses** out of {total} games")
    for i, h in enumerate(reversed(st.session_state[KEY_HISTORY]), 1):
        icon = "✅" if h["result"] == "win" else "❌"
        st.write(f"{icon} Game {total - i + 1}: `{h['word']}` — {h['attempts']} attempt(s)")
