import streamlit as st
import random
import string
import requests

# ---------------------------
# Constants
# ---------------------------
BOARD_SIZE   = 4
MAX_ATTEMPTS = 3
DEMO_LIMIT   = 3
SCORE_MAP    = {1: 10, 2: 5, 3: 3}

KEY_STAGE        = "stage"
KEY_ATTEMPTS     = "attempts"
KEY_BOARD        = "board"
KEY_TARGET_WORD  = "target_word"
KEY_CLUE         = "clue"
KEY_HISTORY      = "history"
KEY_GUESS_KEY    = "guess_key"
KEY_LAST_MSG     = "last_msg"
KEY_USED_WORDS   = "used_words"
KEY_TOTAL_SCORE  = "total_score"
KEY_FEEDBACK     = "feedback"
KEY_WORDS_PLAYED = "words_played"
KEY_SELECTED     = "selected"    # list of (row, col) in selection order
KEY_BONUS_WORDS  = "bonus_words"  # set of bonus words found this round
KEY_DICT_CACHE   = "dict_cache"   # {word: True/False} to avoid repeat API calls

WORDS = [
    {"word": "STONE",  "clue": {"length": 5, "category": "Nature"}},
    {"word": "PLANET", "clue": {"length": 6, "category": "Space"}},
    {"word": "TIGER",  "clue": {"length": 5, "category": "Animals"}},
    {"word": "FLAME",  "clue": {"length": 5, "category": "Nature"}},
    {"word": "ORBIT",  "clue": {"length": 5, "category": "Space"}},
    {"word": "CRANE",  "clue": {"length": 5, "category": "Animals"}},
    {"word": "FROST",  "clue": {"length": 5, "category": "Nature"}},
    {"word": "COMET",  "clue": {"length": 5, "category": "Space"}},
]

for key, default in [
    (KEY_STAGE,        "home"),
    (KEY_ATTEMPTS,     0),
    (KEY_BOARD,        []),
    (KEY_TARGET_WORD,  ""),
    (KEY_CLUE,         {}),
    (KEY_HISTORY,      []),
    (KEY_GUESS_KEY,    0),
    (KEY_LAST_MSG,     None),
    (KEY_USED_WORDS,   []),
    (KEY_TOTAL_SCORE,  0),
    (KEY_FEEDBACK,     None),
    (KEY_WORDS_PLAYED, 0),
    (KEY_SELECTED,     []),
    (KEY_BONUS_WORDS,  set()),
    (KEY_DICT_CACHE,   {}),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ---------------------------
# Game Logic
# ---------------------------
def generate_board(word):
    board = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    r = random.randint(0, BOARD_SIZE - 1)
    c = random.randint(0, BOARD_SIZE - 1)
    board[r][c] = word[0]
    for letter in word[1:]:
        neighbors = [
            (r+dr, c+dc) for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]
            if 0 <= r+dr < BOARD_SIZE and 0 <= c+dc < BOARD_SIZE and board[r+dr][c+dc] == ""
        ]
        if neighbors:
            r, c = random.choice(neighbors)
        else:
            empty = [(i,j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if board[i][j] == ""]
            if not empty: break
            r, c = random.choice(empty)
        board[r][c] = letter
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == "":
                board[i][j] = random.choice(string.ascii_uppercase)
    return board


def word_exists(board, word):
    rows, cols = len(board), len(board[0]) if board else 0
    visited = [[False]*cols for _ in range(rows)]
    def dfs(r, c, idx):
        if idx == len(word): return True
        if not (0 <= r < rows and 0 <= c < cols): return False
        if visited[r][c] or board[r][c] != word[idx]: return False
        visited[r][c] = True
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            if dfs(r+dr, c+dc, idx+1):
                visited[r][c] = False
                return True
        visited[r][c] = False
        return False
    return any(dfs(i, j, 0) for i in range(rows) for j in range(cols))


def sanitize_guess(raw):
    return "".join(filter(str.isalpha, raw)).upper()


def get_bonus_clues(target, attempts_used):
    clues = []
    if attempts_used >= 1:
        clues.append(f"🔡 **Starting letter:** {target[0]}")
    if attempts_used >= 2:
        mid = len(target) // 2
        clues.append(f"🔠 **Letter {mid+1} in the word:** {target[mid]}")
    return clues


def pick_unused_word():
    used = st.session_state[KEY_USED_WORDS]
    available = [w for w in WORDS if w["word"] not in used]
    if not available:
        st.session_state[KEY_USED_WORDS] = []
        available = WORDS
    chosen = random.choice(available)
    st.session_state[KEY_USED_WORDS].append(chosen["word"])
    return chosen


def is_adjacent(r1, c1, r2, c2):
    return abs(r1-r2) + abs(c1-c2) == 1


def selected_word():
    board = st.session_state[KEY_BOARD]
    return "".join(board[r][c] for r, c in st.session_state[KEY_SELECTED])


# ---------------------------
# Stage Transitions
# ---------------------------
def go_home():
    st.session_state[KEY_STAGE]    = "home"
    st.session_state[KEY_LAST_MSG] = None
    st.session_state[KEY_FEEDBACK] = None
    st.session_state[KEY_SELECTED] = []
    st.session_state[KEY_BONUS_WORDS] = set()


def start_new_game():
    if st.session_state[KEY_WORDS_PLAYED] >= DEMO_LIMIT:
        st.session_state[KEY_STAGE] = "subscribe"
        return
    level = pick_unused_word()
    st.session_state[KEY_TARGET_WORD] = level["word"].upper()
    st.session_state[KEY_CLUE]        = level["clue"]
    st.session_state[KEY_BOARD]       = generate_board(level["word"].upper())
    st.session_state[KEY_ATTEMPTS]    = 0
    st.session_state[KEY_GUESS_KEY]  += 1
    st.session_state[KEY_LAST_MSG]    = None
    st.session_state[KEY_FEEDBACK]    = None
    st.session_state[KEY_SELECTED]    = []
    st.session_state[KEY_BONUS_WORDS]  = set()
    st.session_state[KEY_STAGE]       = "game"


def go_result(msg_type, msg_text, history_entry):
    st.session_state[KEY_HISTORY].append(history_entry)
    st.session_state[KEY_LAST_MSG]     = (msg_type, msg_text)
    st.session_state[KEY_FEEDBACK]     = None
    st.session_state[KEY_WORDS_PLAYED]+= 1
    st.session_state[KEY_SELECTED]     = []
    st.session_state[KEY_STAGE]        = "result"


def is_real_word(word: str) -> bool:
    """Check if word exists in English dictionary via free API. Cached per session."""
    word = word.lower()
    cache = st.session_state[KEY_DICT_CACHE]
    if word in cache:
        return cache[word]
    try:
        resp = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
            timeout=3
        )
        result = resp.status_code == 200
    except Exception:
        # If API unreachable, fail open (treat as real word) so game isn't broken
        result = True
    cache[word] = result
    st.session_state[KEY_DICT_CACHE] = cache
    return result


def evaluate_guess(raw_guess):
    clue        = st.session_state[KEY_CLUE]
    target      = st.session_state[KEY_TARGET_WORD]
    attempts    = st.session_state[KEY_ATTEMPTS]
    bonus_words = st.session_state[KEY_BONUS_WORDS]

    if attempts >= MAX_ATTEMPTS:
        st.session_state[KEY_FEEDBACK] = ("error", "No attempts left!")
        return

    guess = sanitize_guess(raw_guess)
    if not guess:
        st.session_state[KEY_FEEDBACK] = ("warning", "No letters selected.")
        return
    if len(guess) != clue["length"]:
        st.session_state[KEY_FEEDBACK] = ("warning", f"Need {clue['length']} letters, got {len(guess)}.")
        return

    # Always clear the tile selection
    st.session_state[KEY_SELECTED] = []

    board = st.session_state[KEY_BOARD]

    # ── Case 1: correct target word ──
    if guess == target and word_exists(board, guess):
        st.session_state[KEY_ATTEMPTS]  += 1
        st.session_state[KEY_GUESS_KEY] += 1
        attempt_number = st.session_state[KEY_ATTEMPTS]
        pts = SCORE_MAP.get(attempt_number, 0)
        st.session_state[KEY_TOTAL_SCORE] += pts
        go_result("win",
            f"🎉 Correct! You found **{target}** on attempt {attempt_number} — **+{pts} points!**",
            {"word": target, "result": "win", "attempts": attempt_number, "points": pts,
             "bonus_words": len(st.session_state[KEY_BONUS_WORDS])})
        return

    # ── Case 2: already found this bonus word ──
    if guess in bonus_words:
        st.session_state[KEY_FEEDBACK] = ("warning", f"You already found **{guess}** as a bonus word!")
        st.session_state[KEY_GUESS_KEY] += 1
        return

    # ── Case 3: traceable on board + real English word → bonus! ──
    if word_exists(board, guess) and is_real_word(guess):
        bonus_pts = 1
        st.session_state[KEY_TOTAL_SCORE] += bonus_pts
        bonus_words.add(guess)
        st.session_state[KEY_BONUS_WORDS]  = bonus_words
        st.session_state[KEY_GUESS_KEY]   += 1
        st.session_state[KEY_FEEDBACK] = (
            "bonus",
            f"🌟 Bonus word! **{guess}** is a real word on the board — **+{bonus_pts} pt!** "
            f"Keep going to find the target word."
        )
        return

    # ── Case 4: wrong — consume an attempt ──
    st.session_state[KEY_ATTEMPTS]  += 1
    st.session_state[KEY_GUESS_KEY] += 1
    attempt_number = st.session_state[KEY_ATTEMPTS]

    if attempt_number >= MAX_ATTEMPTS:
        go_result("loss",
            f"💀 Out of attempts! The word was **{target}**.",
            {"word": target, "result": "loss", "attempts": attempt_number, "points": 0,
             "bonus_words": len(st.session_state[KEY_BONUS_WORDS])})
    elif word_exists(board, guess):
        st.session_state[KEY_FEEDBACK] = ("error", "That word is traceable but isn't a real English word or isn't the target!")
    else:
        st.session_state[KEY_FEEDBACK] = ("error", "Word can't be traced on the board. Try again!")


# ---------------------------
# Handle tile click actions (runs before render)
# ---------------------------
def handle_tile_click(r, c):
    sel = st.session_state[KEY_SELECTED]

    # If this cell is the last selected → deselect (toggle tip)
    if sel and sel[-1] == (r, c):
        st.session_state[KEY_SELECTED] = sel[:-1]
        st.session_state[KEY_FEEDBACK] = None
        return

    # Already in sequence but not the tip → ignore
    if (r, c) in sel:
        return

    # First cell or adjacent to tip → add
    if not sel or is_adjacent(sel[-1][0], sel[-1][1], r, c):
        new_sel = sel + [(r, c)]
        st.session_state[KEY_SELECTED] = new_sel
        st.session_state[KEY_FEEDBACK] = None

        # Auto-submit when word length reached
        clue_len = st.session_state[KEY_CLUE].get("length", 0)
        if len(new_sel) == clue_len:
            word = "".join(st.session_state[KEY_BOARD][rr][cc] for rr, cc in new_sel)
            evaluate_guess(word)


# ---------------------------
# CSS — tile board styled entirely in Streamlit buttons
# ---------------------------
st.markdown("""
<style>
  .big-title { font-size:clamp(28px,8vw,48px); font-weight:800; text-align:center; margin-bottom:0.2em; }
  .clue-box  { background:#f0f4ff; border-radius:10px; padding:12px 18px; margin-bottom:0.6rem; font-size:clamp(14px,4vw,16px); }
  .bonus-clue-box { background:#fffbe6; border:1px solid #f6d860; border-radius:10px; padding:10px 16px; margin-bottom:0.6rem; font-size:clamp(13px,3.8vw,15px); }
  .attempt-bar { text-align:center; font-size:15px; color:#444; margin-bottom:0.4rem; }
  .total-score { font-size:clamp(20px,6vw,28px); font-weight:800; text-align:center; color:#4CAF50; margin:0.5rem 0 1rem 0; }
  .history-row { font-size:clamp(13px,3.5vw,15px); padding:4px 0; }
  .word-display { text-align:center; font-size:clamp(20px,6vw,26px); font-weight:800;
                  letter-spacing:8px; min-height:38px; margin-bottom:6px; }

  /* Board wrapper — constrains total grid width */
  .board-wrapper {
    max-width: 240px;
    margin: 0 auto 6px auto;
  }

  /* Tile button overrides — normal cell */
  .board-wrapper div[data-testid="stButton"] > button {
    width: 100% !important;
    aspect-ratio: 1 / 1 !important;
    font-size: 20px !important;
    font-weight: 800 !important;
    border-radius: 8px !important;
    border: 2px solid #ddd !important;
    background: #f9f9f9 !important;
    color: #222 !important;
    padding: 0 !important;
    transition: background 0.12s, border-color 0.12s, transform 0.1s !important;
    line-height: 1 !important;
    min-height: unset !important;
  }
  .board-wrapper div[data-testid="stButton"] > button:hover {
    border-color: #999 !important;
    transform: scale(1.05) !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.10) !important;
  }

  /* Selected tile */
  .board-wrapper div[data-testid="stButton"].tile-selected > button {
    background: #4f86f7 !important;
    border-color: #1a56db !important;
    color: white !important;
  }

  /* Tip tile (last selected) */
  .board-wrapper div[data-testid="stButton"].tile-tip > button {
    background: #1a56db !important;
    border-color: #0d3b9e !important;
    color: white !important;
    transform: scale(1.09) !important;
  }

  /* Blocked tile */
  .board-wrapper div[data-testid="stButton"].tile-blocked > button {
    opacity: 0.3 !important;
    cursor: not-allowed !important;
    pointer-events: none !important;
  }
</style>
""", unsafe_allow_html=True)


# ==============================
# STAGE 1 — HOME
# ==============================
if st.session_state[KEY_STAGE] == "home":

    st.markdown('<div class="big-title">Project Clue</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;color:#666;margin-bottom:1.5em;font-size:clamp(14px,4vw,18px);">A word tracing puzzle game</div>', unsafe_allow_html=True)

    st.markdown("### How to play")
    st.markdown(
        f"1. A **4×4 grid** of letters appears — **tap letters** to build your word.\n"
        f"2. Each letter must be **adjacent** to the previous (up/down/left/right). No reusing cells.\n"
        f"3. **Tap the last selected letter again** to deselect it.\n"
        f"4. The word **auto-submits** when you reach the correct letter count.\n"
        f"5. You have **{MAX_ATTEMPTS} attempts** per word.\n"
        f"6. **Bonus clues appear automatically after each wrong guess:**\n"
        f"   - ❌ After attempt 1 → **starting letter** revealed.\n"
        f"   - ❌ After attempt 2 → **a middle letter & position** revealed.\n"
        f"7. **Scoring:** Attempt 1 = **10 pts** · Attempt 2 = **5 pts** · Attempt 3 = **3 pts**.\n"
        f"8. This demo includes **{DEMO_LIMIT} words**. Subscribe to keep playing!"
    )

    st.write("")
    if st.button("▶️ Start Game", use_container_width=True):
        start_new_game()
        st.rerun()

    if st.session_state[KEY_HISTORY]:
        st.divider()
        wins  = sum(1 for h in st.session_state[KEY_HISTORY] if h["result"] == "win")
        total = len(st.session_state[KEY_HISTORY])
        st.markdown(f"**Session record:** {wins}W / {total-wins}L")
        st.markdown(f'<div class="total-score">🏆 {st.session_state[KEY_TOTAL_SCORE]} pts</div>', unsafe_allow_html=True)


# ==============================
# STAGE 2 — GAME
# ==============================
elif st.session_state[KEY_STAGE] == "game":

    clue     = st.session_state[KEY_CLUE]
    attempts = st.session_state[KEY_ATTEMPTS]
    target   = st.session_state[KEY_TARGET_WORD]
    board    = st.session_state[KEY_BOARD]
    played   = st.session_state[KEY_WORDS_PLAYED]
    sel      = st.session_state[KEY_SELECTED]

    st.markdown('<div class="big-title">Project Clue</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="text-align:center;color:#888;font-size:13px;margin-bottom:0.4rem;">'
        f'Word {played+1} of {DEMO_LIMIT}</div>',
        unsafe_allow_html=True
    )

    # Clues
    st.markdown(
        f'<div class="clue-box">🔤 <b>Length:</b> {clue["length"]} &nbsp;|&nbsp; 📂 <b>Category:</b> {clue["category"]}</div>',
        unsafe_allow_html=True
    )
    for bc in get_bonus_clues(target, attempts):
        st.markdown(f'<div class="bonus-clue-box">{bc}</div>', unsafe_allow_html=True)

    remaining = MAX_ATTEMPTS - attempts
    circles   = "🟢" * remaining + "🔴" * attempts
    pts_next  = SCORE_MAP.get(attempts + 1, 0)
    st.markdown(
        f'<div class="attempt-bar">{circles} &nbsp; {attempts}/{MAX_ATTEMPTS} used'
        f' &nbsp;|&nbsp; Next correct = <b>{pts_next} pts</b></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div style="text-align:center;color:#4CAF50;font-weight:700;margin-bottom:0.2rem;">'
        f'🏆 Score: {st.session_state[KEY_TOTAL_SCORE]} pts</div>',
        unsafe_allow_html=True
    )

    # Feedback
    fb = st.session_state[KEY_FEEDBACK]
    if fb:
        if fb[0] == "warning":   st.warning(fb[1])
        elif fb[0] == "bonus":   st.success(fb[1])
        else:                    st.error(fb[1])

    # Show bonus words found this round
    bonus_words = st.session_state[KEY_BONUS_WORDS]
    if bonus_words:
        bw_list = "  ·  ".join(sorted(bonus_words))
        st.markdown(
            f'<div style="text-align:center;font-size:13px;color:#7c3aed;margin-bottom:0.3rem;">'
            f'🌟 Bonus words found: <b>{bw_list}</b></div>',
            unsafe_allow_html=True
        )

    # ── Word being built display ──
    if sel:
        w = "".join(board[r][c] for r, c in sel)
        color = "#16a34a" if len(sel) == clue["length"] else "#1a56db"
    else:
        w = ""
        color = "#bbb"
    st.markdown(
        f'<div class="word-display" style="color:{color};">'
        f'{" · ".join(list(w)) if w else "· · ·"}</div>',
        unsafe_allow_html=True
    )

    # ── Tile board using st.columns + st.button ──
    # Each cell is a native Streamlit button — no iframe, no bridge needed.
    # We inject a JS snippet AFTER rendering to add CSS classes to selected/tip/blocked buttons.
    st.markdown('<div class="board-wrapper">', unsafe_allow_html=True)
    for row_idx in range(BOARD_SIZE):
        cols = st.columns(BOARD_SIZE)
        for col_idx in range(BOARD_SIZE):
            cell_letter = board[row_idx][col_idx]
            pos_in_sel  = sel.index((row_idx, col_idx)) if (row_idx, col_idx) in sel else -1
            is_in_sel   = pos_in_sel != -1
            is_tip      = sel and sel[-1] == (row_idx, col_idx)
            adj_to_tip  = sel and is_adjacent(sel[-1][0], sel[-1][1], row_idx, col_idx)
            can_add     = not is_in_sel and (not sel or adj_to_tip)

            # Build label: letter + small seq number superscript for selected cells
            if is_tip:
                label = f"{cell_letter}"
            elif is_in_sel:
                label = f"{cell_letter}"
            else:
                label = cell_letter

            with cols[col_idx]:
                btn_key = f"tile_{row_idx}_{col_idx}_{st.session_state[KEY_GUESS_KEY]}"
                clicked = st.button(label, key=btn_key, use_container_width=True)

            if clicked:
                handle_tile_click(row_idx, col_idx)
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── CSS class injection via JS to style selected/tip/blocked tiles ──
    # We mark each button by its position so JS can find and style it.
    sel_indices = [(r * BOARD_SIZE + c) for r, c in sel]
    tip_index   = (sel[-1][0] * BOARD_SIZE + sel[-1][1]) if sel else -1

    # Blocked = in grid but not selectable (not adjacent to tip, not already selected)
    blocked_indices = []
    if sel:
        last_r, last_c = sel[-1]
        for ri in range(BOARD_SIZE):
            for ci in range(BOARD_SIZE):
                idx = ri * BOARD_SIZE + ci
                in_s = (ri, ci) in sel
                adj  = is_adjacent(last_r, last_c, ri, ci)
                if not in_s and not adj:
                    blocked_indices.append(idx)

    st.markdown(f"""
    <script>
    (function() {{
      // Give Streamlit a moment to render the buttons
      setTimeout(() => {{
        const btns = window.parent.document.querySelectorAll(
          '.board-wrapper div[data-testid="stButton"] button'
        );
        const sel     = {sel_indices};
        const tip     = {tip_index};
        const blocked = {blocked_indices};
        const size    = {BOARD_SIZE};

        let tileBtns = Array.from(btns);

        tileBtns.forEach((btn, i) => {{
          const parent = btn.parentElement;
          parent.classList.remove('tile-selected','tile-tip','tile-blocked');
          if (i === tip) {{
            parent.classList.add('tile-tip');
          }} else if (sel.includes(i)) {{
            parent.classList.add('tile-selected');
          }} else if (blocked.includes(i)) {{
            parent.classList.add('tile-blocked');
          }}
        }});
      }}, 80);
    }})();
    </script>
    """, unsafe_allow_html=True)

    # Clear button
    st.write("")
    if sel:
        if st.button("✖ Clear selection", use_container_width=True):
            st.session_state[KEY_SELECTED] = []
            st.session_state[KEY_FEEDBACK] = None
            st.rerun()

    st.caption("💡 Tap the last selected letter to deselect. Word auto-submits when complete.")

    if st.button("🏠 Back to Home", use_container_width=True):
        go_home()
        st.rerun()


# ==============================
# STAGE 3 — RESULT
# ==============================
elif st.session_state[KEY_STAGE] == "result":

    st.markdown('<div class="big-title">Project Clue</div>', unsafe_allow_html=True)

    msg = st.session_state[KEY_LAST_MSG]
    if msg:
        if msg[0] == "win": st.success(msg[1])
        else: st.error(msg[1])

    st.markdown(
        f'<div class="total-score">🏆 Total Score: {st.session_state[KEY_TOTAL_SCORE]} pts</div>',
        unsafe_allow_html=True
    )

    if st.session_state[KEY_WORDS_PLAYED] >= DEMO_LIMIT:
        st.info(f"You've completed all {DEMO_LIMIT} demo words!")
        if st.button("🔔 Subscribe to Continue", use_container_width=True):
            st.session_state[KEY_STAGE] = "subscribe"
            st.rerun()
        if st.button("🏠 Back to Home", use_container_width=True):
            go_home()
            st.rerun()
    else:
        st.markdown("### Continue playing?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Next Word", use_container_width=True):
                start_new_game()
                st.rerun()
        with col2:
            if st.button("🏠 End Session", use_container_width=True):
                go_home()
                st.rerun()

    st.divider()
    st.markdown("### 📊 Session History")
    history = st.session_state[KEY_HISTORY]
    wins  = sum(1 for h in history if h["result"] == "win")
    total = len(history)
    st.markdown(f"**{wins} wins / {total-wins} losses** across {total} words")
    st.write("")
    for i, h in enumerate(reversed(history), 1):
        icon      = "✅" if h["result"] == "win" else "❌"
        pts       = h.get("points", 0)
        pts_label = f" · **+{pts} pts**" if pts > 0 else " · *0 pts*"
        bw = h.get("bonus_words", 0)
        bw_label = f" · 🌟 {bw} bonus" if bw else ""
        st.markdown(
            f'<div class="history-row">{icon} Word {total-i+1}: '
            f'<code>{h["word"]}</code> — attempt {h["attempts"]}{pts_label}{bw_label}</div>',
            unsafe_allow_html=True
        )


# ==============================
# STAGE 4 — SUBSCRIBE WALL
# ==============================
elif st.session_state[KEY_STAGE] == "subscribe":

    st.markdown('<div class="big-title">Project Clue</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;padding:2rem 1rem;">
      <div style="font-size:64px;">🔒</div>
      <h2 style="font-size:clamp(22px,6vw,34px);font-weight:800;margin:0.5rem 0;">Thanks for playing!</h2>
      <p style="color:#555;font-size:clamp(14px,4vw,18px);margin-bottom:1.5rem;">
        You've completed all 3 free words.<br>
        Subscribe to unlock unlimited words, more categories, and a global leaderboard.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<div class="total-score">🏆 Your demo score: {st.session_state[KEY_TOTAL_SCORE]} pts</div>',
        unsafe_allow_html=True
    )

    # ← Replace with your real subscribe link
    st.markdown("""
    <div style="text-align:center;margin:1rem 0 0.5rem 0;">
      <a href="https://your-subscribe-link.com" target="_blank"
         style="display:inline-block;background:#4CAF50;color:white;
                font-weight:700;font-size:18px;padding:14px 32px;
                border-radius:10px;text-decoration:none;">
        🔔 Subscribe to Continue Playing
      </a>
    </div>
    <p style="text-align:center;color:#aaa;font-size:13px;margin-top:10px;">— End of Demo —</p>
    """, unsafe_allow_html=True)

    st.write("")
    if st.button("🏠 Back to Home", use_container_width=True):
        go_home()
        st.rerun()
