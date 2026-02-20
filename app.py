import streamlit as st
import random
from datetime import datetime

# Version control
APP_VERSION = "Shiftword v3.7 - Guaranteed Tiles - Feb 20 2026"
st.title("🧩 Shiftword Game")
st.caption(APP_VERSION)
st.caption(f"Loaded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Game rules
st.markdown("""
### 📜 How to Play
1. Guess the hidden word.
2. You have **5 attempts**.
3. You only get:
   - The **Theme**
   - The **Number of Letters**
4. **Tiles must be followed adjacently** (vertical or horizontal only, no diagonal).
5. Enter words with the correct length.
""")
st.write("---")

# Word bank
WORD_BANK = {
    "Nature": ["RIVER", "STONE", "PLANT", "CLOUD", "OCEAN"],
    "Animals": ["TIGER", "HORSE", "SNAKE", "ZEBRA", "EAGLE"],
    "Space": ["EARTH", "COMET", "ORBIT", "ALIEN", "ROVER"]
}

# Session state init
if "initialized" not in st.session_state:
    st.session_state.word = random.choice(random.choice(list(WORD_BANK.values())))
    st.session_state.theme = random.choice(list(WORD_BANK.keys()))
    st.session_state.attempts = 5
    st.session_state.guesses = []
    st.session_state.game_over = False
    st.session_state.initialized = True

# Clues
st.subheader("🔎 Clues")
st.write(f"📌 Theme: **{st.session_state.theme}**")
st.write(f"🔤 Number of Letters: **{len(st.session_state.word)}**")
st.write("---")

# Display all previous guesses (guaranteed to show)
st.subheader("Previous Guesses")
for guess in st.session_state.guesses:
    # Display letters separated by spaces inside a single text line
    st.text(" ".join([f"[{c}]" for c in guess]))

# Input
if not st.session_state.game_over:
    guess = st.text_input("Enter your guess (letters only, follow tile adjacency)").upper()
    if st.button("Submit Guess"):
        if len(guess) != len(st.session_state.word):
            st.error("Word length does not match.")
        elif not guess.isalpha():
            st.error("Only letters allowed.")
        else:
            st.session_state.guesses.append(guess)
            if guess == st.session_state.word:
                st.success("🎉 Correct! You won!")
                st.session_state.game_over = True
            else:
                st.session_state.attempts -= 1
                st.warning(f"❌ Wrong! Attempts left: {st.session_state.attempts}")
                if st.session_state.attempts == 0:
                    st.error(f"Game Over! The word was: {st.session_state.word}")
                    st.session_state.game_over = True

# Restart button
if st.session_state.game_over:
    if st.button("🔄 Play Again"):
        st.session_state.clear()
        st.rerun()
