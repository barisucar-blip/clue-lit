import streamlit as st
import random
from datetime import datetime

# ==============================
# VERSION CONTROL - 8
# ==============================
APP_VERSION = "Shiftword v4.0 - Clickable Tiles - Feb 20 2026"
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
4. **Letter tiles must be selected following the route of adjacent tiles** (vertical or horizontal only, **not diagonal**).
5. Click letters in order to form your guess.
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
    # Pick theme and word
    st.session_state.theme = random.choice(list(WORD_BANK.keys()))
    st.session_state.word = random.choice(WORD_BANK[st.session_state.theme])
    st.session_state.attempts = 5
    st.session_state.guesses = []
    st.session_state.selected = []
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
# DISPLAY PREVIOUS GUESSES
# ==============================
st.subheader("Previous Guesses")
for guess in st.session_state.guesses:
    st.text(" ".join([f"[{c}]" for c in guess]))

# ==============================
# DISPLAY CLICKABLE TILES
# ==============================
st.subheader("Click Letters to Form Your Guess")

# Only show if game not over
if not st.session_state.game_over:
    cols = st.columns(len(st.session_state.word))
    for i, letter in enumerate(st.session_state.word):
        if cols[i].button(letter):
            # Add selected letter
            st.session_state.selected.append(letter)
    
    st.write("Your current selection:", st.session_state.selected)

    # Submit guess automatically if full length selected
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
                st.error(f"Game Over! The word was: {st.session_state.word}")
                st.session_state.game_over = True
        # Reset selection
        st.session_state.selected = []

# ==============================
# RESTART BUTTON
# ==============================
if st.session_state.game_over:
    if st.button("🔄 Play Again"):
        st.session_state.clear()
        st.experimental_rerun()
