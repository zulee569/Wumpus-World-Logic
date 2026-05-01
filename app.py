import streamlit as st
import numpy as np
from sympy import symbols, Not, Or, And, to_cnf, satisfiable

# --- HEADER & PAGE CONFIG ---
st.set_page_config(layout="wide")
st.markdown("<h2 style='text-align: center;'>Wumpus World Logic Agent - Developed by Muhammad Zulqarnain (24F-0536)</h2>", unsafe_allow_html=True)

# --- CSS FOR ZERO-GAP SOLID GRID ---
st.markdown("""
    <style>
    /* Remove gaps between Streamlit columns */
    [data-testid="column"] {
        padding: 0px !important;
        margin: 0px !important;
        gap: 0px !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    /* Grid Cell Styling */
    .grid-cell {
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #222;
        font-weight: bold;
        color: white;
        font-size: 14px;
        margin: 0px;
    }
    .main .block-container {
        padding-top: 2rem;
        max-width: 700px;
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
with st.sidebar:
    st.header("Settings")
    rows = st.number_input("Rows", 3, 6, 4)
    cols = st.number_input("Cols", 3, 6, 4)
    if st.button("Reset Game"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

if 'grid' not in st.session_state:
    # 0: Safe, 1: Pit, 2: Wumpus
    grid = np.zeros((rows, cols))
    for r in range(rows):
        for c in range(cols):
            if (r, c) != (0, 0) and np.random.rand() < 0.15: grid[r, c] = 1
    w_r, w_c = np.random.randint(0, rows), np.random.randint(0, cols)
    while (w_r, w_c) == (0, 0) or grid[w_r, w_c] == 1:
        w_r, w_c = np.random.randint(0, rows), np.random.randint(0, cols)
    grid[w_r, w_c] = 2
    
    st.session_state.grid = grid
    st.session_state.pos = (0, 0)
    st.session_state.visited = {(0, 0)}
    st.session_state.kb = []
    st.session_state.inf_steps = 0
    st.session_state.game_over = False

# --- LOGIC HELPERS ---
def get_syms(r, c): return symbols(f"P{r}_{c} W{r}_{c}")

def tell_kb(expr): st.session_state.kb.append(to_cnf(expr))

def ask_safe(r, c):
    st.session_state.inf_steps += 1
    P, W = get_syms(r, c)
    combined_kb = And(*st.session_state.kb)
    # Check if assuming (Pit or Wumpus) causes a contradiction
    if not satisfiable(And(combined_kb, Or(P, W))): return True
    return False

# --- UPDATE KB BASED ON POSITION ---
curr_r, curr_c = st.session_state.pos
P_curr, W_curr = get_syms(curr_r, curr_c)
tell_kb(And(Not(P_curr), Not(W_curr)))

percepts = []
adj_syms = []
for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
    nr, nc = curr_r + dr, curr_c + dc
    if 0 <= nr < rows and 0 <= nc < cols:
        adj_syms.append(get_syms(nr, nc))
        if st.session_state.grid[nr, nc] == 1: percepts.append("Breeze")
        if st.session_state.grid[nr, nc] == 2: percepts.append("Stench")

percepts = list(set(percepts))
if "Breeze" not in percepts:
    for P, W in adj_syms: tell_kb(Not(P))
if "Stench" not in percepts:
    for P, W in adj_syms: tell_kb(Not(W))

# --- WIN/LOSS CHECK ---
if st.session_state.grid[st.session_state.pos] != 0:
    st.error("GAME OVER: Caught by Hazard!")
    st.session_state.game_over = True

total_safe_spots = np.sum(st.session_state.grid == 0)
if len(st.session_state.visited) == total_safe_spots and not st.session_state.game_over:
    st.success("ALL CAVES COVERED: YOU WIN!")
    st.session_state.game_over = True

# --- DASHBOARD ---
d1, d2 = st.columns(2)
d1.metric("Percepts", ", ".join(percepts) if percepts else "Clear")
d2.metric("Inference Steps", st.session_state.inf_steps)

# --- RENDER GRID ---
for r in range(rows):
    row_cols = st.columns(cols)
    for c in range(cols):
        with row_cols[c]:
            label = "???"
            bg = "#333333" # Default Gray
            
            # 1. Check Inference (Safe)
            if ask_safe(r, c):
                label, bg = "SAFE", "#4CAF50" # Light Green
            
            # 2. Check Visited
            if (r, c) in st.session_state.visited:
                label, bg = "VISITED", "#2E7D32" # Green
                
            # 3. Check Agent Position
            if (r, c) == st.session_state.pos:
                label, bg = "AGENT", "#FFD700" # Yellow
            
            # 4. Reveal Hazards on Game Over
            if st.session_state.game_over:
                if st.session_state.grid[r, c] == 1: label, bg = "PIT", "#D32F2F"
                elif st.session_state.grid[r, c] == 2: label, bg = "WUMPUS", "#D32F2F"

            st.markdown(f"<div class='grid-cell' style='background-color:{bg};'>{label}</div>", unsafe_allow_html=True)

# --- CONTROLS ---
st.write("### Controls")
c1, c2, c3, c4 = st.columns(4)
def move(dr, dc):
    if not st.session_state.game_over:
        nr, nc = st.session_state.pos[0] + dr, st.session_state.pos[1] + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            st.session_state.pos = (nr, nc)
            st.session_state.visited.add((nr, nc))
            st.rerun()

if c1.button("LEFT"): move(0, -1)
if c2.button("UP"): move(-1, 0)
if c3.button("DOWN"): move(1, 0)
if c4.button("RIGHT"): move(0, 1)