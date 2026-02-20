import streamlit as st
import random
from datetime import datetime

# ==============================
# VERSION CONTROL - 7
# ==============================
APP_VERSION = "Shiftword v3.9 - Guaranteed Tiles - Feb 20 2026"
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
4. **Letter tiles must be chosen following the route of adjacent tiles** (vertical or horizontal only, **not diagonal**).
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
    st.session_state.theme = random.choice(list(WORD_BANK.keys()))
    st.session_state.word = random.choice(WORD_BANK[st.session_state.theme])
    st.session_state.guesses = []
    st.session_state.attempts = 5
    st.session_state.game_over = False
    st.session_state.initialized = True

# ==============================
# DISPLAY CLUES
# ==============================
st.subheader("🔎 Clues")
st.write(f"📌 Theme: **{st.session_state.theme}**")
st.write(f"🔤 Number of letters: **{len(st.session_state.word)}**")
st.write("---")

# ==============================
# DISPLAY PREVIOUS GUESSES AS "TILES"
# ==============================
st.subheader("Previous Guesses")
for guess in st.session_state.guesses:
    # Guaranteed display using brackets for each letter
    st.text(" ".join([f"[{c}]" for c in guess]))

# ==============================
# GAME INPUT
# ==============================
if not st.session_state.game_over:
    guess = st.text_input("Enter your guess (letters only)").upper()
    
    if st.button("Submit Guess"):
        if len(guess) != len(st.session_state.word):
            st.error("Word length does not match!")
        elif not guess.isalpha():
            st.error("Only letters allowed!")
        else:
            # Save the guess
            st.session_state.guesses.append(guess)

            # Check for correct guess
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
        st.experimental_rerun()
