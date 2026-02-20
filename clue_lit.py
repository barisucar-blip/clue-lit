import streamlit as st
import random
import string

BOARD_SIZE = 4
MAX_ATTEMPTS = 5

WORDS = [
    {"word": "STONE", "clue": {"length": 5, "starts_with": "S", "contains": "T", "category": "Nature"}},
    {"word": "PLANET", "clue": {"length": 6, "starts_with": "P", "contains": "N", "category": "Space"}},
    {"word": "TIGER", "clue": {"length": 5, "starts_with": "T", "contains": "G", "category": "Animals"}},
]

# ---------------------------
# Initialize Session State
# ---------------------------
if "game_started" not in st.session_state:
    st.session_state.game_started = False

if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "board" not in st.session_state:
    st.session_state.board = []

if "target_word" not in st.session_state:
    st.session_state.target_word = ""

if "clue" not in st.session_state:
    st.session_state.clue = {}

# ---------------------------
# Board Generator
# ---------------------------
def generate_board(word):
    board = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    r = random.randint(0, BOARD_SIZE - 1)
    c = random.randint(0, BOARD_SIZE - 1)
    board[r][c] = word[0]

    for letter in word[1:]:
        neighbors = [(r+dr, c+dc) for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]
                     if 0<=r+dr<BOARD_SIZE and 0<=c+dc<BOARD_SIZE and board[r+dr][c+dc]==""]

        if neighbors:
            r,c = random.choice(neighbors)
        else:
            empty_cells = [(i,j) for i in range(BOARD_SIZE)
                           for j in range(BOARD_SIZE)
                           if board[i][j]==""] 
            r,c = random.choice(empty_cells)

        board[r][c] = letter

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == "":
                board[i][j] = random.choice(string.ascii_uppercase)

    return board

# ---------------------------
# DFS Check
# ---------------------------
def word_exists(board, word):
    word = word.upper()
    visited = [[False]*BOARD_SIZE for _ in range(BOARD_SIZE)]

    def dfs(r,c,index):
        if index == len(word):
            return True
        if r<0 or r>=BOARD_SIZE or c<0 or c>=BOARD_SIZE:
            return False
        if visited[r][c] or board[r][c] != word[index]:
            return False

        visited[r][c] = True

        for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            if dfs(r+dr,c+dc,index+1):
                return True

        visited[r][c] = False
        return False

    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if dfs(i,j,0):
                return True

    return False

# ---------------------------
# Start Game Button
# ---------------------------
st.title("🔎 Clueless Game")

if st.button("Start New Game"):
    level = random.choice(WORDS)
    st.session_state.target_word = level["word"].upper()
    st.session_state.clue = level["clue"]
    st.session_state.board = generate_board(st.session_state.target_word)
    st.session_state.attempts = 0
    st.session_state.game_started = True

# ---------------------------
# Display Game
# ---------------------------
if st.session_state.game_started:

    st.subheader("Board")

    # Display grid nicely
    for row in st.session_state.board:
        st.markdown(" | ".join(row))

    st.subheader("Clues")
    st.write("Length:", st.session_state.clue["length"])
    st.write("Starts with:", st.session_state.clue["starts_with"])
    st.write("Contains letter:", st.session_state.clue["contains"])
    st.write("Category:", st.session_state.clue["category"])

    guess = st.text_input("Enter your guess:")

    if st.button("Submit Guess"):

        if st.session_state.attempts >= MAX_ATTEMPTS:
            st.error("No attempts left!")
        else:
            st.session_state.attempts += 1
            guess = guess.upper()

            if len(guess) != st.session_state.clue["length"]:
                st.warning("Wrong length.")
            elif not guess.startswith(st.session_state.clue["starts_with"]):
                st.warning("Wrong starting letter.")
            elif st.session_state.clue["contains"] not in guess:
                st.warning("Missing required letter.")
            elif word_exists(st.session_state.board, guess):
                st.success("🎉 Correct! You found the word!")
                st.session_state.game_started = False
            else:
                st.error("Word cannot be formed from board.")

    st.write(f"Attempts: {st.session_state.attempts}/{MAX_ATTEMPTS}")

    if st.session_state.attempts >= MAX_ATTEMPTS:
        st.error("💀 Game Over!")
        st.write("Correct word was:", st.session_state.target_word)
        st.session_state.game_started = False