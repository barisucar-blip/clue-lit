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
KEY_GAME_OVER = "game_over"
KEY_PLAY_AGAIN = "play_again_prompt"
KEY_GUESS_KEY = "guess_key"  # used to reset text input

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
    (KEY_GAME_OVER, False),
    (KEY_PLAY_AGAIN, False),
    (KEY_GUESS_KEY, 0),
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
# Start a New Game (helper)
# ---------------------------
def start_new_game():
    level = random.choice(WORDS)
    st.session_state[KEY_TARGET_WORD] = level["word"].upper()
    st.session_state[KEY_CLUE] = level["clue"]
    st.session_state[KEY_BOARD] = generate_board(st.session_state[KEY_TARGET_WORD])
    st.session_state[KEY_ATTEMPTS] = 0
    st.session_state[KEY_GAME_STARTED] = True
    st.session_state[KEY_GAME_OVER] = False
    st.session_state[KEY_PLAY_AGAIN] = False
    st.session_state[KEY_GUESS_KEY] += 1  # resets the text input


# ---------------------------
# UI — Title
# ---------------------------
st.title("Project Clue")

if st.button("Start New Game"):
    start_new_game()

# ---------------------------
# Display Game
# ---------------------------
if st.session_state[KEY_GAME_STARTED]:

    # --- Game Rules ---
    st.info(
        "**How to play:**  \n"
        "1. Look at the letter board below.  \n"
        "2. Use the clues to guess the hidden word.  \n"
        "3. Your word must be traceable on the board by moving to adjacent cells "
        "(up, down, left, right) — no reusing the same cell.  \n"
        f"4. You have **{MAX_ATTEMPTS} attempts**. Good luck!"
    )

    # --- Board ---
    st.subheader("Board")

    # Build the board as a single HTML CSS grid — works reliably on both
    # desktop and mobile without relying on st.columns() which breaks on
    # narrow screens (all cells collapse into one column).
    cell_html = ""
    for row in st.session_state[KEY_BOARD]:
        for letter in row:
            cell_html += (
                f"<div style='"
                f"display:flex; align-items:center; justify-content:center;"
                f"font-size:clamp(16px, 5vw, 26px); font-weight:bold;"
                f"border:2px solid #ccc; border-radius:8px;"
                f"background:#f9f9f9; aspect-ratio:1;'>"
                f"{letter}</div>"
            )

    board_html = f"""
    <div style="
        display: grid;
        grid-template-columns: repeat({BOARD_SIZE}, 1fr);
        gap: 8px;
        max-width: 320px;
        width: 100%;
        margin: 0 auto 1rem auto;
    ">
        {cell_html}
    </div>
    """
    st.markdown(board_html, unsafe_allow_html=True)

    # --- Clues (Length and Category only — Starts With and Contains removed) ---
    st.subheader("Clues")
    clue = st.session_state[KEY_CLUE]
    st.write("Length:", clue["length"])
    st.write("Category:", clue["category"])

    st.write(f"**Attempts:** {st.session_state[KEY_ATTEMPTS]}/{MAX_ATTEMPTS}")

    # --- Guess Input ---
    # The key changes after each valid submission, which forces Streamlit
    # to remount the widget and clear it — no "Upgrade" prompt triggered.
    guess_input = st.text_input(
        "Enter your guess:",
        key=f"guess_input_{st.session_state[KEY_GUESS_KEY]}"
    )

    if st.button("Submit Guess"):
        if st.session_state[KEY_ATTEMPTS] >= MAX_ATTEMPTS:
            st.error("No attempts left! Start a new game.")
        else:
            guess = sanitize_guess(guess_input)

            # --- Format checks (don't cost an attempt) ---
            if not guess:
                st.warning("Please enter a word.")
            elif len(guess) != clue["length"]:
                st.warning(f"Wrong length — expected {clue['length']} letters.")
            else:
                # Increment attempt and clear the input box
                st.session_state[KEY_ATTEMPTS] += 1
                st.session_state[KEY_GUESS_KEY] += 1  # clears input on next render

                target = st.session_state[KEY_TARGET_WORD]

                if guess == target and word_exists(st.session_state[KEY_BOARD], guess):
                    st.success("🎉 Correct! You found the word!")
                    st.session_state[KEY_HISTORY].append({
                        "word": target, "result": "win",
                        "attempts": st.session_state[KEY_ATTEMPTS]
                    })
                    st.session_state[KEY_GAME_STARTED] = False
                    st.session_state[KEY_PLAY_AGAIN] = True

                elif word_exists(st.session_state[KEY_BOARD], guess):
                    st.error("That word exists on the board but isn't the answer. Try again!")

                else:
                    st.error("Word cannot be formed from the board.")

                # Game over — out of attempts
                if st.session_state[KEY_ATTEMPTS] >= MAX_ATTEMPTS and st.session_state[KEY_GAME_STARTED]:
                    st.error(f"💀 Game Over! The word was: **{target}**")
                    st.session_state[KEY_HISTORY].append({
                        "word": target, "result": "loss",
                        "attempts": st.session_state[KEY_ATTEMPTS]
                    })
                    st.session_state[KEY_GAME_STARTED] = False
                    st.session_state[KEY_PLAY_AGAIN] = True

# ---------------------------
# Play Again Prompt
# ---------------------------
if st.session_state[KEY_PLAY_AGAIN]:
    st.divider()
    st.subheader("Would you like to play again?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("✅ Yes, play again!"):
            start_new_game()
            st.rerun()
    with col_no:
        if st.button("❌ No, I'm done"):
            st.session_state[KEY_PLAY_AGAIN] = False
            st.success("Thanks for playing Project Clue! 👋")

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
