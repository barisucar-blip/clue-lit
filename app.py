import streamlit as st
import random

st.title("Shiftword Grid Tile Game v4.1")

# Word bank and word selection
WORDS = ["RIVER", "STONE", "PLANT", "CLOUD", "OCEAN"]
if "word" not in st.session_state:
    st.session_state.word = random.choice(WORDS)
    st.session_state.guesses = []
    st.session_state.selected = []
    st.session_state.attempts = 5
    st.session_state.game_over = False

st.write(f"Theme: Nature")
st.write(f"Word length: {len(st.session_state.word)}")
st.write(f"Attempts left: {st.session_state.attempts}")
st.write("---")

# Display previous guesses
st.subheader("Previous Guesses")
for guess in st.session_state.guesses:
    st.text(" ".join([f"[{c}]" for c in guess]))

# Grid of clickable tiles
st.subheader("Click Letters to Form Your Guess")
grid_cols = st.columns(len(st.session_state.word))
for i, letter in enumerate(st.session_state.word):
    if grid_cols[i].button(letter):
        st.session_state.selected.append(letter)

st.write("Current selection:", st.session_state.selected)

# Check if full word selected
if len(st.session_state.selected) == len(st.session_state.word):
    guess = "".join(st.session_state.selected)
    st.session_state.guesses.append(guess)

    if guess == st.session_state.word:
        st.success("🎉 Correct! You won!")
        st.session_state.game_over = True
    else:
        st.session_state.attempts -= 1
        st.warning(f"❌ Wrong! Attempts left: {st.session_state.attempts}")
        if st.session_state.attempts == 0:
            st.error(f"Game Over! The word was {st.session_state.word}")
            st.session_state.game_over = True

    st.session_state.selected = []

# Restart button
if st.session_state.game_over:
    if st.button("Play Again"):
        st.session_state.clear()
        st.experimental_rerun()
