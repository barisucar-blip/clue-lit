import streamlit as st
import random
from datetime import datetime

# ==============================
# Version
# ==============================
APP_VERSION = "Shiftword v4.4 - Visible Tile Grid - Feb 20 2026"
st.title("🧩 Shiftword Game")
st.caption(APP_VERSION)
st.caption(f"Loaded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==============================
# Game rules
# ==============================
st.markdown("""
### 📜 How to Play
1. Guess the hidden word by typing it.
2. You have **5 attempts**.
3. You only get:
   - The **Theme**
   - The **Number of Letters**
4. Tiles always show letters of previous guesses.
5. Empty tiles are shown as `_`.
""")
st.write("---")

# ==============================
# Word bank
# ==============================
WORD_BANK = {
    "Nature": ["RIVER", "STONE", "PLANT", "CLOUD", "OCEAN"],
    "Animals": ["TIGER", "HORSE", "SNAKE", "ZEBRA", "EAGLE"],
    "Space": ["EARTH", "COMET", "ORBIT", "ALIEN", "ROVER"]
}

# ==============================
# Session state init
# ==============================
if "initialized" not in st.session_state:
    st.session_state.theme = random.choice(list(WORD_BANK.keys()))
    st.session_state.word = random.choice(WORD_BANK[st.session_state.theme])
    st.session_state.guesses = []
    st.session_state.attempts = 5
    st.session_state.game_over = False
    st.session_state.initialized = True

word_length = len(st.session_state.word)

# ==============================
# Clues
# ==============================
st.subheader("🔎 Clues")
st.write(f"📌 Theme: {st.session_state.theme}")
st.write(f"Word length: {word_length}")
st.write(f"Attempts left: {st.session_state.attempts}")
st.write("---")

# ==============================
# Display tile grid
# ==============================
st.subheader("Tile Grid (Previous Guesses)")

# Always show a grid of attempts
for i in range(5):  # max 5 attempts
    if i < len(st.session_state.guesses):
        # Fill with letters of previous guess
        guess = st.session_state.guesses[i]
        st.text(" ".join(guess))
    else:
        # Empty attempt: show underscores
        st.text(" ".join(["_"] * word_length))

st.write("---")

# ==============================
# Input for guessing
# ==============================
if not st.session_state.game_over:
    guess = st.text_input("Enter your guess (letters only)").upper()
    
    if st.button("Submit Guess"):
        if len(guess) != word_length:
            st.error("Word length does not match!")
        elif not guess.isalpha():
            st.error("Only letters allowed!")
        else:
            # Save guess
            st.session_state.guesses.append(guess)
            
            # Check win
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
# Restart button
# ==============================
if st.session_state.game_over:
    if st.button("🔄 Play Again"):
        st.session_state.clear()
        st.experimental_rerun()
