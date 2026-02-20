import streamlit as st
import random
from datetime import datetime

st.title("🧩 Shiftword Game - Visible Tiles")

# Word bank
WORD_BANK = {
    "Nature": ["RIVER", "STONE", "PLANT", "CLOUD", "OCEAN"],
    "Animals": ["TIGER", "HORSE", "SNAKE", "ZEBRA", "EAGLE"],
    "Space": ["EARTH", "COMET", "ORBIT", "ALIEN", "ROVER"]
}

# Session state
if "initialized" not in st.session_state:
    st.session_state.theme = random.choice(list(WORD_BANK.keys()))
    st.session_state.word = random.choice(WORD_BANK[st.session_state.theme])
    st.session_state.guesses = []
    st.session_state.attempts = 5
    st.session_state.game_over = False
    st.session_state.initialized = True

# Clues
st.subheader("🔎 Clues")
st.write(f"📌 Theme: {st.session_state.theme}")
st.write(f"Word length: {len(st.session_state.word)}")
st.write(f"Attempts left: {st.session_state.attempts}")
st.write("---")

# Display previous guesses (monospace letters as tiles)
st.subheader("Previous Guesses")
if st.session_state.guesses:
    for guess in st.session_state.guesses:
        st.text(f"{' '.join(guess)}")  # letters separated by spaces
else:
    st.write("No guesses yet")

# Input for guessing
if not st.session_state.game_over:
    guess = st.text_input("Enter your guess").upper()
    if st.button("Submit Guess"):
        if len(guess) != len(st.session_state.word):
            st.error("Word length does not match!")
        elif not guess.isalpha():
            st.error("Only letters allowed!")
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
        st.experimental_rerun()
