import streamlit as st
import random
import pandas as pd

st.title("🧩 Shiftword Game - Tiles Visible")

# Word bank
WORD_BANK = {
    "Nature": ["RIVER", "STONE", "PLANT", "CLOUD", "OCEAN"],
    "Animals": ["TIGER", "HORSE", "SNAKE", "ZEBRA", "EAGLE"],
    "Space": ["EARTH", "COMET", "ORBIT", "ALIEN", "ROVER"]
}

# Session state initialization
if "initialized" not in st.session_state:
    st.session_state.theme = random.choice(list(WORD_BANK.keys()))
    st.session_state.word = random.choice(WORD_BANK[st.session_state.theme])
    st.session_state.guesses = []
    st.session_state.attempts = 5
    st.session_state.game_over = False
    st.session_state.initialized = True

# Clues
st.subheader("🔎 Clues")
st.write(f"📌 Theme: **{st.session_state.theme}**")
st.write(f"🔤 Number of letters: **{len(st.session_state.word)}**")
st.write(f"Attempts left: {st.session_state.attempts}")
st.write("---")

# Display previous guesses as a table (tiles)
st.subheader("Previous Guesses")
if st.session_state.guesses:
    # Create a list of rows for the table
    table_data = []
    for guess in st.session_state.guesses:
        table_data.append(list(guess))  # each letter is a cell
    st.table(pd.DataFrame(table_data))
else:
    st.write("No guesses yet")

# Input
if not st.session_state.game_over:
    guess = st.text_input("Enter your guess").upper()
    if st.button("Submit Guess"):
        if len(guess) != len(st.session_state.word):
            st.error("Word length does not match!")
        elif not guess.isalpha():
            st.error("Only letters allowed!")
        else:
            # Add guess
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

# Restart
if st.session_state.game_over:
    if st.button("🔄 Play Again"):
        st.session_state.clear()
        st.experimental_rerun()
