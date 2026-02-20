import streamlit as st
import random
from datetime import datetime

# ==============================
# VERSION CONTROL
# ==============================
APP_VERSION = "Shiftword v3.5 - Streamlit Native Tiles - Feb 20 2026"
st.title("🧩 Shiftword Game")
st.caption(APP_VERSION)
st.caption(f"Loaded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==============================
# GAME RULES
# ==============================
st.markdown("""
### 📜 How to Play
1. Guess the hidden word.
2. You have **5 attempts**.
3. You only get:
   - The **Theme**
   - The **Number of Letters**
4. **Letter tiles must be chosen following the route of adjacent tiles** (vertical and horizontal only, **not diagonal**).
5. Enter words with the correct length.
""")

st.write("---")

# ==============================
# WORD BANK
# ==============================
WORD_BANK = {
    "Nature": ["RIVER", "STONE", "PLANT", "CLOUD", "OCEAN"],
    "Animals": ["TIGER", "HORSE", "SNAKE", "ZEBRA", "EAGLE"],
    "Space": ["EARTH", "COMET", "ORBIT", "ALIEN", "ROVER"]
}

# ==============================
# SESSION STATE INIT
# ==============================
if "initialized" not in st.session_state:
    theme = random.choice(list(WORD_BANK.keys()))
    word = random.choice(WORD_BANK[theme])
    st.session_state.word = word
    st.session_state.theme = theme
    st.session_state.attempts = 5
    st.session_state.guesses = []
    st.session_state.game_over = False
    st.session_state.initialized = True

# ==============================
# CLUES
# ==============================
st.subheader("🔎 Clues")
st.write(f"📌 Theme: **{st.session_state.theme}**")
st.write(f"🔤 Number of Letters: **{len(st.session_state.word)}**")
st.write("---")

# ==============================
# TILE DISPLAY USING COLUMNS (Native Streamlit)
# ==============================
def display_tiles(word):
    cols = st.columns(len(word))
    for i, letter in enumerate(word):
        with cols[i]:
            st.text_input("", value=letter, key=f"tile_{letter}_{i}", disabled=True)

# ==============================
# DISPLAY PREVIOUS GUESSES
# ==============================
st.subheader("Previous Guesses")
for guess in st.session_state.guesses:
    display_tiles(guess)

# ==============================
# GAME INPUT- 4
# ==============================
if not st.session_state.game_over:
    guess = st.text_input("Enter your guess (use only adjacent tiles route)").upper()

    if st.button("Submit Guess"):

        if len(guess) != len(st.session_state.word):
            st.error("Word length does not match.")
        elif not guess.isalpha():
            st.error("Only letters allowed.")
        else:
            st.session_state.guesses.append(guess)
            # Display the tiles immediately
            display_tiles(guess)

            if guess == st.session_state.word:
                st.success("🎉 Correct! You won!")
                st.session_state.game_over = True
            else:
                st.session_state.attempts -= 1
                st.warning(f"❌ Wrong! Attempts left: {st.session_state.attempts}")
                if st.session_state.attempts == 0:
                    st.error(f"Game Over! The word was: {st.session_state.word}")
                    st.session_state.game_over = True

# ==============================
# RESTART BUTTON
# ==============================
if st.session_state.game_over:
    if st.button("🔄 Play Again"):
        st.session_state.clear()
        st.rerun()
