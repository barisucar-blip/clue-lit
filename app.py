import streamlit as st
import random
import string
import streamlit.components.v1 as components

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
KEY_TILE_WORD    = "tile_word"   # word submitted from tile, read on next rerun

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
    (KEY_TILE_WORD,    None),
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


# ---------------------------
# Stage Transitions
# ---------------------------
def go_home():
    st.session_state[KEY_STAGE]     = "home"
    st.session_state[KEY_LAST_MSG]  = None
    st.session_state[KEY_FEEDBACK]  = None
    st.session_state[KEY_TILE_WORD] = None


def start_new_game():
    if st.session_state[KEY_WORDS_PLAYED] >= DEMO_LIMIT:
        st.session_state[KEY_STAGE] = "subscribe"
        return
    level = pick_unused_word()
    st.session_state[KEY_TARGET_WORD]  = level["word"].upper()
    st.session_state[KEY_CLUE]         = level["clue"]
    st.session_state[KEY_BOARD]        = generate_board(level["word"].upper())
    st.session_state[KEY_ATTEMPTS]     = 0
    st.session_state[KEY_GUESS_KEY]   += 1
    st.session_state[KEY_LAST_MSG]     = None
    st.session_state[KEY_FEEDBACK]     = None
    st.session_state[KEY_TILE_WORD]    = None
    st.session_state[KEY_STAGE]        = "game"


def go_result(msg_type, msg_text, history_entry):
    st.session_state[KEY_HISTORY].append(history_entry)
    st.session_state[KEY_LAST_MSG]     = (msg_type, msg_text)
    st.session_state[KEY_FEEDBACK]     = None
    st.session_state[KEY_WORDS_PLAYED] += 1
    st.session_state[KEY_TILE_WORD]    = None
    st.session_state[KEY_STAGE]        = "result"


def evaluate_guess(raw_guess):
    clue     = st.session_state[KEY_CLUE]
    target   = st.session_state[KEY_TARGET_WORD]
    attempts = st.session_state[KEY_ATTEMPTS]

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

    st.session_state[KEY_ATTEMPTS]  += 1
    st.session_state[KEY_GUESS_KEY] += 1
    attempt_number = st.session_state[KEY_ATTEMPTS]

    if guess == target and word_exists(st.session_state[KEY_BOARD], guess):
        pts = SCORE_MAP.get(attempt_number, 0)
        st.session_state[KEY_TOTAL_SCORE] += pts
        go_result("win",
            f"🎉 Correct! You found **{target}** on attempt {attempt_number} — **+{pts} points!**",
            {"word": target, "result": "win", "attempts": attempt_number, "points": pts})
    elif attempt_number >= MAX_ATTEMPTS:
        go_result("loss",
            f"💀 Out of attempts! The word was **{target}**.",
            {"word": target, "result": "loss", "attempts": attempt_number, "points": 0})
    elif word_exists(st.session_state[KEY_BOARD], guess):
        st.session_state[KEY_FEEDBACK] = ("error", "That word is on the board but isn't the answer!")
    else:
        st.session_state[KEY_FEEDBACK] = ("error", "Word can't be traced on the board. Try again!")


# ---------------------------
# Process tile word submitted from hidden form (runs before rendering)
# ---------------------------
tile_word = st.session_state.get(KEY_TILE_WORD)
if tile_word and st.session_state[KEY_STAGE] == "game":
    st.session_state[KEY_TILE_WORD] = None
    evaluate_guess(tile_word)
    st.rerun()


# ---------------------------
# CSS
# ---------------------------
st.markdown("""
<style>
  .big-title { font-size:clamp(28px,8vw,48px); font-weight:800; text-align:center; margin-bottom:0.2em; }
  .clue-box  { background:#f0f4ff; border-radius:10px; padding:12px 18px; margin-bottom:0.6rem; font-size:clamp(14px,4vw,16px); }
  .bonus-clue-box { background:#fffbe6; border:1px solid #f6d860; border-radius:10px; padding:10px 16px; margin-bottom:0.6rem; font-size:clamp(13px,3.8vw,15px); }
  .attempt-bar { text-align:center; font-size:15px; color:#444; margin-bottom:0.8rem; }
  .total-score { font-size:clamp(20px,6vw,28px); font-weight:800; text-align:center; color:#4CAF50; margin:0.5rem 0 1rem 0; }
  .history-row { font-size:clamp(13px,3.5vw,15px); padding:4px 0; }
  /* Hide the tile-submit form visually but keep it functional */
  div[data-testid="stForm"].tile-form { display:none !important; }
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
        f"1. A **4×4 grid** of letters appears — **tap letters** on the board to build your word.\n"
        f"2. Each letter must be **adjacent** to the previous one (up/down/left/right). No reusing cells.\n"
        f"3. **Tap the last selected letter again** to deselect it and step back.\n"
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

    st.markdown('<div class="big-title">Project Clue</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="text-align:center;color:#888;font-size:13px;margin-bottom:0.6rem;">'
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
        f'<div style="text-align:center;color:#4CAF50;font-weight:700;margin-bottom:0.4rem;">'
        f'🏆 Score: {st.session_state[KEY_TOTAL_SCORE]} pts</div>',
        unsafe_allow_html=True
    )

    fb = st.session_state[KEY_FEEDBACK]
    if fb:
        if fb[0] == "warning": st.warning(fb[1])
        else: st.error(fb[1])

    # ── Hidden form — JS will fill & submit this to pass the word back to Streamlit ──
    # It's rendered invisibly; the tile component triggers it via JS.
    with st.form(key=f"tile_form_{st.session_state[KEY_GUESS_KEY]}"):
        hidden_input = st.text_input("tile_word_input", value="", key=f"tile_input_{st.session_state[KEY_GUESS_KEY]}", label_visibility="collapsed")
        submitted    = st.form_submit_button("submit_tile", use_container_width=False)

    if submitted and hidden_input:
        st.session_state[KEY_TILE_WORD] = hidden_input
        st.rerun()

    # ── Interactive board ──
    flat    = [board[r][c] for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)]
    clu_len = clue["length"]
    # unique DOM IDs tied to guess_key so they always match the current form
    gk      = st.session_state[KEY_GUESS_KEY]

    board_html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:sans-serif; background:transparent; padding:6px 0; }}

#word-display {{
  text-align:center;
  font-size:clamp(20px,6vw,26px);
  font-weight:800;
  letter-spacing:8px;
  min-height:38px;
  margin-bottom:8px;
  color:#bbb;
  transition:color 0.2s;
}}
#board {{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:8px;
  max-width:300px;
  width:100%;
  margin:0 auto 10px auto;
}}
.cell {{
  display:flex; align-items:center; justify-content:center;
  font-size:clamp(20px,7vw,28px); font-weight:800;
  border:2px solid #ddd; border-radius:10px;
  background:#f9f9f9; aspect-ratio:1;
  cursor:pointer; user-select:none; position:relative;
  transition:background 0.12s, border-color 0.12s, transform 0.1s, box-shadow 0.12s;
  -webkit-tap-highlight-color:transparent;
}}
.cell.available:hover  {{ border-color:#999; transform:scale(1.06); box-shadow:0 2px 8px rgba(0,0,0,0.12); }}
.cell.selected {{ background:#4f86f7; border-color:#1a56db; color:white; box-shadow:0 2px 8px rgba(79,134,247,0.35); }}
.cell.tip      {{ background:#1a56db; border-color:#0d3b9e; color:white; box-shadow:0 3px 12px rgba(26,86,219,0.45); transform:scale(1.09); }}
.cell.blocked  {{ opacity:0.32; cursor:not-allowed; }}
.cell.done     {{ background:#16a34a; border-color:#15803d; color:white; }}
.seq-num {{ position:absolute; top:3px; right:5px; font-size:10px; font-weight:700; color:rgba(255,255,255,0.88); }}
#hint {{ text-align:center; font-size:13px; color:#888; min-height:18px; margin-bottom:6px; }}
#btn-clear {{
  display:block; margin:0 auto;
  padding:7px 24px; border:none; border-radius:8px;
  font-size:14px; font-weight:700; cursor:pointer;
  background:#f3f4f6; color:#555; transition:background 0.12s;
}}
#btn-clear:hover {{ background:#e5e7eb; }}
</style>
</head>
<body>
<div id="word-display">· · ·</div>
<div id="board"></div>
<div id="hint">Tap a letter to start</div>
<button id="btn-clear" onclick="clearAll()">✖ Clear</button>

<script>
const LETTERS = {flat};
const SIZE    = 4;
const CLU_LEN = {clu_len};
const GK      = "{gk}";   // guess key — matches Streamlit form IDs

let seq       = [];
let done      = false;

const rowOf = i => Math.floor(i / SIZE);
const colOf = i => i % SIZE;
const adj   = (r1,c1,r2,c2) => Math.abs(r1-r2)+Math.abs(c1-c2)===1;
const inSeq = i => seq.some(s=>s.idx===i);
const last  = () => seq.length ? seq[seq.length-1] : null;
const word  = () => seq.map(s=>LETTERS[s.idx]).join("");

function render() {{
  const boardEl = document.getElementById("board");
  boardEl.innerHTML = "";
  const L = last();

  for (let i=0; i<SIZE*SIZE; i++) {{
    const r=rowOf(i), c=colOf(i);
    const div = document.createElement("div");
    div.className = "cell";
    div.textContent = LETTERS[i];

    const pos    = seq.findIndex(s=>s.idx===i);
    const inS    = pos !== -1;
    const isTip  = inS && pos===seq.length-1;
    const canAdd = !inS && (seq.length===0 || (L && adj(L.r,L.c,r,c)));

    if (done) {{
      div.classList.add(inS ? "done" : "blocked");
    }} else if (isTip) {{
      div.classList.add("tip");
      div.addEventListener("click", deselectTip);
    }} else if (inS) {{
      div.classList.add("selected");
      const badge = document.createElement("span");
      badge.className = "seq-num";
      badge.textContent = pos+1;
      div.appendChild(badge);
    }} else if (canAdd) {{
      div.classList.add("available");
      div.addEventListener("click", ()=>selectCell(i,r,c));
    }} else {{
      div.classList.add("blocked");
    }}
    boardEl.appendChild(div);
  }}

  const w    = word();
  const disp = document.getElementById("word-display");
  const hint = document.getElementById("hint");

  if (w.length===0) {{
    disp.textContent="· · ·"; disp.style.color="#bbb";
    hint.textContent="Tap a letter to start"; hint.style.color="#888";
  }} else if (done) {{
    disp.textContent=w.split("").join("  "); disp.style.color="#16a34a";
    hint.textContent="✅ Checking…"; hint.style.color="#16a34a";
  }} else {{
    disp.textContent=w.split("").join("  "); disp.style.color="#1a56db";
    const left=CLU_LEN-w.length;
    hint.textContent=`${{left}} more letter${{left!==1?"s":""}} to go`; hint.style.color="#888";
  }}
}}

function selectCell(i,r,c) {{
  if (done) return;
  seq.push({{idx:i,r,c}});
  render();
  if (seq.length===CLU_LEN) autoSubmit();
}}

function deselectTip() {{
  if (done) return;
  seq.pop();
  render();
}}

function clearAll() {{
  if (done) return;
  seq=[];
  render();
}}

function autoSubmit() {{
  done = true;
  render();

  const w = word();

  // Strategy: find the Streamlit text input and form button inside the parent
  // document, fill in the word, then click submit. Both live in the same
  // Streamlit page (parent frame), not a different origin.
  setTimeout(() => {{
    try {{
      const parentDoc = window.parent.document;

      // The text input has a data-testid and a key we can target
      const inputs = parentDoc.querySelectorAll('input[type="text"]');
      let targetInput = null;
      for (const inp of inputs) {{
        // Match the input whose closest form contains our submit button label
        const form = inp.closest('form');
        if (form) {{
          const btn = form.querySelector('button');
          if (btn && btn.textContent.includes('submit_tile')) {{
            targetInput = inp;
            break;
          }}
        }}
      }}

      // Fallback: just grab the first visible text input in the page
      if (!targetInput) {{
        for (const inp of inputs) {{
          if (inp.offsetParent !== null) {{ targetInput = inp; break; }}
        }}
      }}

      if (targetInput) {{
        // Set value using React's synthetic event system
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
          window.parent.HTMLInputElement.prototype, 'value'
        ).set;
        nativeInputValueSetter.call(targetInput, w);
        targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));

        // Click the form submit button
        const form = targetInput.closest('form');
        if (form) {{
          const submitBtn = form.querySelector('button[type="submit"], button');
          if (submitBtn) {{ submitBtn.click(); }}
        }}
      }}
    }} catch(e) {{
      // If DOM manipulation fails (e.g. stricter sandbox), fall back gracefully
      console.warn("Tile submit fallback:", e);
    }}
  }}, 350);
}}

render();
</script>
</body>
</html>"""

    components.html(board_html, height=400, scrolling=False)
    st.caption("💡 Tap the last letter again to deselect. Word auto-submits when complete.")

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
        st.markdown(
            f'<div class="history-row">{icon} Word {total-i+1}: '
            f'<code>{h["word"]}</code> — attempt {h["attempts"]}{pts_label}</div>',
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
