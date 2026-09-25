import re
import hashlib
from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from supabase import create_client

SUPABASE_URL = "https://aekoktcexfbbilqzrhyc.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_69GJzmzxAwLGgPzYMVj6AQ_GKLoZAse"

st.set_page_config(page_title="MLBB Tracker", page_icon="\U0001F3AE", layout="wide")

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

ACCENT_GOLD = "#f0c531"
ACCENT_CYAN = "#2ee6ff"
ACCENT_PURPLE = "#a855f7"
ACCENT_MAGENTA = "#e935c1"
BG_DEEP = "#050510"
BG_PANEL = "#0c0a22"
WIN_GREEN = "#39ffb0"
LOSS_RED = "#ff4d6d"

TIER_COLORS = {"S": "#ff3d71", "A": "#ff9f43", "B": "#f2c94c", "C": "#39ffb0", "D": "#8892b0"}
ROLE_ICON = {"exp": "⚔️", "jungle": "\U0001F332", "mid": "\U0001F52E", "roam": "\U0001F6E1️", "gold": "\U0001F3F9"}
ROLE_LABEL = {"exp": "EXP Lane", "jungle": "Jungle", "mid": "Mid Lane", "roam": "Roam", "gold": "Gold Lane"}
RANK_LADDER = ["Warrior", "Elite", "Master", "Grandmaster", "Epic", "Legend", "Mythic", "Mythical Honor", "Mythical Glory"]
METRIC_LABEL = {
    "deaths": "Deaths",
    "gold_earned": "Gold earned",
    "damage_dealt": "Hero damage",
    "damage_taken": "Damage taken",
    "teamfight_participation": "Teamfight participation %",
    "kda": "KDA",
}
METRIC_LOWER_IS_BETTER = {"deaths", "damage_taken"}
TIP_CATEGORY_META = {
    "macro": {"icon": "\U0001F6E1️", "color": ACCENT_CYAN, "label": "Macro"},
    "pattern": {"icon": "\U0001F50D", "color": ACCENT_GOLD, "label": "Pattern"},
    "meta": {"icon": "\U000026A1", "color": ACCENT_MAGENTA, "label": "Meta"},
    "hero": {"icon": "\U0001F3AF", "color": ACCENT_PURPLE, "label": "Hero"},
    "general": {"icon": "\U0001F4A1", "color": WIN_GREEN, "label": "General"},
    "aspirational": {"icon": "\U0001F31F", "color": ACCENT_GOLD, "label": "Inspiration"},
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

/* ---- Galactic background: nebula gradients + starfield ---- */
.stApp {{
    background-image:
        radial-gradient(ellipse 900px 600px at 8% -5%, rgba(168,85,247,0.22) 0%, transparent 55%),
        radial-gradient(ellipse 800px 700px at 100% 10%, rgba(46,230,255,0.14) 0%, transparent 50%),
        radial-gradient(ellipse 700px 500px at 30% 110%, rgba(233,53,193,0.14) 0%, transparent 55%),
        radial-gradient(ellipse 600px 500px at 90% 100%, rgba(240,197,49,0.08) 0%, transparent 50%),
        radial-gradient(1.6px 1.6px at 40px 60px, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 140px 25px, rgba(255,255,255,0.65), transparent),
        radial-gradient(1.6px 1.6px at 210px 150px, rgba(200,220,255,0.85), transparent),
        radial-gradient(1px 1px at 95px 190px, rgba(255,255,255,0.55), transparent),
        radial-gradient(1.4px 1.4px at 260px 90px, rgba(255,255,255,0.7), transparent),
        radial-gradient(1px 1px at 170px 230px, rgba(200,220,255,0.6), transparent);
    background-repeat: no-repeat, no-repeat, no-repeat, no-repeat, repeat, repeat, repeat, repeat, repeat, repeat;
    background-size: auto, auto, auto, auto, 300px 300px, 300px 300px, 300px 300px, 300px 300px, 300px 300px, 300px 300px;
    background-color: {BG_DEEP};
    background-attachment: fixed;
}}
h1, h2, h3, .mlbb-title {{
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 0.02em;
}}
h2, h3 {{ color: #eef2ff !important; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {BG_PANEL} 0%, {BG_DEEP} 100%);
    border-right: 1px solid rgba(46,230,255,0.15);
    box-shadow: 4px 0 24px rgba(168,85,247,0.06);
}}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
    font-family: 'Orbitron', sans-serif !important; font-size: 0.95rem; letter-spacing: 0.06em;
    background: linear-gradient(90deg, {ACCENT_CYAN}, {ACCENT_PURPLE});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}

/* ---- Hero banner ---- */
@keyframes glowPulse {{
    0%, 100% {{ box-shadow: 0 0 24px rgba(46,230,255,0.10), 0 0 60px rgba(168,85,247,0.06), inset 0 0 40px rgba(46,230,255,0.03); }}
    50% {{ box-shadow: 0 0 32px rgba(46,230,255,0.18), 0 0 80px rgba(168,85,247,0.12), inset 0 0 50px rgba(46,230,255,0.06); }}
}}
.mlbb-hero {{
    padding: 2rem 2.2rem;
    margin-bottom: 1.4rem;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(168,85,247,0.14), rgba(46,230,255,0.08) 45%, rgba(233,53,193,0.10));
    border: 1px solid rgba(46,230,255,0.28);
    animation: glowPulse 5s ease-in-out infinite;
    position: relative; overflow: hidden;
}}
.mlbb-hero::before {{
    content: ''; position: absolute; top: -40%; right: -10%; width: 300px; height: 300px; border-radius: 50%;
    background: radial-gradient(circle, rgba(233,53,193,0.18), transparent 70%); pointer-events: none;
}}
.mlbb-hero h1 {{
    margin: 0; font-family: 'Orbitron', sans-serif !important; font-weight: 900;
    font-size: 2.5rem; letter-spacing: 0.04em;
    background: linear-gradient(90deg, {ACCENT_GOLD}, {ACCENT_MAGENTA} 45%, {ACCENT_CYAN});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    text-shadow: 0 0 30px rgba(46,230,255,0.25);
}}
.mlbb-hero p {{ margin: 0.45rem 0 0 0; color: #aab4d4; font-size: 0.95rem; position: relative; z-index: 1; }}

/* ---- Glassmorphic cards ---- */
.mlbb-card {{
    background: rgba(18,16,40,0.55);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(46,230,255,0.14);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.9rem;
}}
.mlbb-stat-row {{ display: flex; gap: 0.9rem; flex-wrap: wrap; }}
.mlbb-stat {{
    flex: 1 1 140px;
    background: rgba(18,16,40,0.55);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(46,230,255,0.16);
    border-radius: 14px;
    padding: 0.85rem 1.05rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}}
.mlbb-stat:hover {{ border-color: rgba(46,230,255,0.4); box-shadow: 0 0 18px rgba(46,230,255,0.10); }}
.mlbb-stat .label {{ color: #8b93c4; font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.07em; }}
.mlbb-stat .value {{ font-family: 'Orbitron', sans-serif; font-size: 1.6rem; font-weight: 700; color: #f2f5fa; }}
.mlbb-stat .value.gold {{ color: {ACCENT_GOLD}; text-shadow: 0 0 14px rgba(240,197,49,0.45); }}
.mlbb-stat .value.cyan {{ color: {ACCENT_CYAN}; text-shadow: 0 0 14px rgba(46,230,255,0.45); }}
.mlbb-stat .value.win {{ color: {WIN_GREEN}; text-shadow: 0 0 14px rgba(57,255,176,0.4); }}

/* ---- Tier badges (glowing) ---- */
.tier-badge {{
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 34px; height: 30px; padding: 0 10px;
    border-radius: 8px; font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 1rem;
    color: #08070f; margin-right: 6px;
}}
.role-chip {{
    display: inline-block; padding: 2px 11px; border-radius: 999px;
    background: rgba(46,230,255,0.10); border: 1px solid rgba(46,230,255,0.35);
    color: {ACCENT_CYAN}; font-size: 0.78rem; margin-right: 6px;
}}
.result-chip {{
    display: inline-flex; align-items:center; justify-content:center;
    width: 26px; height: 26px; border-radius: 50%; font-size: 0.72rem; font-weight: 700;
}}
.result-win {{ background: rgba(57,255,176,0.16); color: {WIN_GREEN}; border: 1px solid rgba(57,255,176,0.5); box-shadow: 0 0 8px rgba(57,255,176,0.25); }}
.result-loss {{ background: rgba(255,77,109,0.16); color: {LOSS_RED}; border: 1px solid rgba(255,77,109,0.5); box-shadow: 0 0 8px rgba(255,77,109,0.25); }}

.mlbb-tip {{
    border-left: 3px solid {ACCENT_GOLD};
    background: rgba(240,197,49,0.05);
    backdrop-filter: blur(6px);
    padding: 0.7rem 1rem;
    border-radius: 0 12px 12px 0;
    margin-bottom: 0.6rem;
}}
.mlbb-aspire {{
    border-left: 3px solid {ACCENT_CYAN};
    background: rgba(46,230,255,0.06);
    backdrop-filter: blur(6px);
    padding: 0.9rem 1.1rem;
    border-radius: 0 12px 12px 0;
    margin-bottom: 0.8rem;
}}
[data-testid="stMetric"] {{
    background: rgba(18,16,40,0.55);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(46,230,255,0.16);
    border-radius: 14px;
    padding: 0.6rem 0.8rem 0.3rem 0.8rem;
}}
[data-testid="stMetricValue"] {{ font-family: 'Orbitron', sans-serif; }}
.streamlit-expanderHeader {{
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
}}
[data-testid="stExpander"] {{
    background: rgba(18,16,40,0.4);
    border: 1px solid rgba(46,230,255,0.12) !important;
    border-radius: 12px !important;
}}

/* ---- Tabs: cyan/purple instead of default red ---- */
[data-testid="stTabs"] [data-testid="stTab"] {{
    color: #9aa3c9 !important; font-family: 'Rajdhani', sans-serif; font-weight: 600;
    border-bottom-color: rgba(255,255,255,0.08) !important;
}}
[data-testid="stTabs"] [data-testid="stTab"] p {{ color: inherit !important; }}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {{
    color: {ACCENT_CYAN} !important;
    border-bottom-color: {ACCENT_CYAN} !important;
    box-shadow: 0 2px 10px -2px rgba(46,230,255,0.7);
}}
[data-testid="stTabs"] [data-testid="stTab"]:hover {{ color: {ACCENT_CYAN} !important; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background-color: {ACCENT_CYAN} !important; }}
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label {{ color: #cdd4f0 !important; }}

/* ---- Hero cards (Builds tab) ---- */
.hero-card {{
    position: relative;
    display: block;
    height: 150px;
    border-radius: 16px;
    overflow: hidden;
    background-size: cover;
    background-position: center 15%;
    border: 1px solid rgba(46,230,255,0.20);
    text-decoration: none;
    margin-bottom: 0.5rem;
    transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}}
.hero-card:hover {{
    border-color: rgba(46,230,255,0.65);
    transform: translateY(-2px);
    box-shadow: 0 0 22px rgba(46,230,255,0.25);
}}
.hero-card::after {{
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(to top, rgba(5,5,16,0.96) 0%, rgba(5,5,16,0.25) 55%, rgba(5,5,16,0.0) 100%);
}}
.hero-card .hc-label {{
    position: absolute; left: 10px; right: 10px; bottom: 8px; z-index: 2;
}}
.hero-card .hc-name {{
    display: block;
    font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 1.05rem; color: #f5f7fb;
    text-shadow: 0 1px 4px rgba(0,0,0,0.6);
}}
.hero-card .hc-sub {{ display: block; font-size: 0.72rem; color: #b9c4d6; }}
.hero-card .hc-tier {{
    position: absolute; top: 8px; right: 8px; z-index: 3;
}}
.hero-card .hc-play {{
    position: absolute; top: 8px; left: 8px; z-index: 3;
    background: rgba(0,0,0,0.55); border-radius: 50%; width: 26px; height: 26px;
    display: flex; align-items: center; justify-content: center; font-size: 0.8rem;
}}
.roster-avatar {{
    width: 100%; aspect-ratio: 1 / 1; border-radius: 50%;
    background-size: cover; background-position: center 12%;
    border: 2px solid rgba(46,230,255,0.28);
    box-shadow: 0 0 12px rgba(46,230,255,0.12);
    margin-bottom: 4px;
    transition: box-shadow 0.15s ease, border-color 0.15s ease;
}}

/* ---- Tier list hero icon grid ---- */
.tier-grid {{ display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 1.3rem; }}
.tier-chip {{ width: 88px; text-align: center; }}
.tier-chip .tc-avatar {{
    width: 66px; height: 66px; border-radius: 50%; margin: 0 auto 5px auto;
    background-size: cover; background-position: center 12%;
    border: 2px solid var(--tc-color, {ACCENT_CYAN});
    box-shadow: 0 0 12px var(--tc-glow, rgba(46,230,255,0.35));
    position: relative; transition: transform 0.15s ease;
}}
.tier-chip:hover .tc-avatar {{ transform: scale(1.08); }}
.tier-chip .tc-name {{ font-size: 0.72rem; color: #e4e8fb; font-weight: 600; line-height: 1.15; font-family: 'Rajdhani', sans-serif; }}
.tier-chip .tc-stat {{ font-size: 0.68rem; color: {ACCENT_GOLD}; font-family: 'Orbitron', sans-serif; margin-top: 1px; }}
.tier-chip .tc-sub {{ font-size: 0.62rem; color: #7c85ad; }}

.stButton > button {{
    background: rgba(18,16,40,0.6);
    border: 1px solid rgba(46,230,255,0.28);
    color: #dbe3f0;
    border-radius: 9px;
    font-size: 0.78rem;
    font-family: 'Rajdhani', sans-serif; font-weight: 600;
    padding: 0.2rem 0.5rem;
    transition: border-color 0.15s ease, box-shadow 0.15s ease, color 0.15s ease;
}}
.stButton > button:hover {{
    border-color: {ACCENT_CYAN};
    color: {ACCENT_CYAN};
    box-shadow: 0 0 14px rgba(46,230,255,0.3);
}}

/* ---- Scrollbar ---- */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: {BG_DEEP}; }}
::-webkit-scrollbar-thumb {{ background: linear-gradient(180deg, {ACCENT_PURPLE}, {ACCENT_CYAN}); border-radius: 6px; }}

[data-testid="stDataFrame"] {{
    border: 1px solid rgba(46,230,255,0.14) !important;
    border-radius: 12px !important;
    overflow: hidden;
}}

/* ---- Sidebar filters: glassmorphic selects + tags ---- */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
    color: #8b93c4 !important;
    font-family: 'Rajdhani', sans-serif; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.76rem;
}}
[data-testid="stMultiSelect"] div[role="group"][data-rac],
[data-testid="stSelectbox"] div[role="group"][data-rac] {{
    background: rgba(18,16,40,0.6) !important;
    border: 1px solid rgba(46,230,255,0.18) !important;
    border-radius: 10px !important;
    backdrop-filter: blur(6px);
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}}
[data-testid="stMultiSelect"] div[role="group"][data-rac]:focus-within,
[data-testid="stSelectbox"] div[role="group"][data-rac]:focus-within {{
    border-color: rgba(46,230,255,0.6) !important;
    box-shadow: 0 0 12px rgba(46,230,255,0.25) !important;
}}
[data-testid="stMultiSelectTagsContainer"] span[data-tag] {{
    background: rgba(46,230,255,0.14) !important;
    border: 1px solid rgba(46,230,255,0.4) !important;
    border-radius: 999px !important;
    color: {ACCENT_CYAN} !important;
}}

/* ---- Alerts / empty states ---- */
[data-testid="stAlert"] {{
    background: rgba(46,230,255,0.06) !important;
    border: 1px solid rgba(46,230,255,0.22) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(6px);
}}

/* ---- Dividers: gradient line instead of flat grey ---- */
hr {{
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, rgba(168,85,247,0.55), rgba(46,230,255,0.55), rgba(233,53,193,0.3)) !important;
    opacity: 0.55;
    margin: 1.3rem 0 !important;
}}

/* ---- Spinner ---- */
[data-testid="stSpinner"] {{
    color: {ACCENT_CYAN} !important;
}}
[data-testid="stSpinner"] p {{
    font-family: 'Rajdhani', sans-serif; font-weight: 600; color: {ACCENT_CYAN} !important;
}}

/* ---- Insight of the day ---- */
.insight-card {{
    border-left: 3px solid {ACCENT_GOLD};
    background: linear-gradient(90deg, rgba(240,197,49,0.08), rgba(46,230,255,0.04));
    backdrop-filter: blur(8px);
    padding: 1rem 1.2rem;
    border-radius: 0 14px 14px 0;
    margin-bottom: 1rem;
}}
.insight-label {{
    font-family: 'Orbitron', sans-serif; font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.08em; color: {ACCENT_GOLD}; margin-bottom: 0.35rem;
}}
.insight-title {{ font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 1.1rem; color: #f5f7fb; margin-bottom: 0.2rem; }}
.insight-body {{ font-size: 0.85rem; color: #b9c4d6; line-height: 1.4; }}

/* ---- Achievement / streak badges ---- */
.badge-chip {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 14px; border-radius: 999px; margin: 0 8px 8px 0;
    background: rgba(18,16,40,0.6); border: 1px solid rgba(46,230,255,0.25);
    font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 0.85rem; color: #dbe3f0;
}}
.badge-chip.glow {{
    border-color: {ACCENT_GOLD};
    box-shadow: 0 0 14px rgba(240,197,49,0.4);
    color: {ACCENT_GOLD};
}}
.badge-chip .bc-icon {{ font-size: 1rem; }}

/* ---- Rank ladder ---- */
.rank-ladder {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 2px; margin: 0.7rem 0 0.5rem 0; }}
.rank-step {{ flex: 1; text-align: center; position: relative; }}
.rank-step::before {{
    content: ''; position: absolute; top: 9px; left: -50%; width: 100%; height: 2px;
    background: rgba(46,230,255,0.15); z-index: 0;
}}
.rank-step:first-child::before {{ display: none; }}
.rank-step.passed::before, .rank-step.active::before {{
    background: linear-gradient(90deg, {ACCENT_PURPLE}, {ACCENT_CYAN});
}}
.rank-dot {{
    width: 18px; height: 18px; border-radius: 50%; margin: 0 auto 6px auto;
    background: rgba(18,16,40,0.8); border: 2px solid rgba(46,230,255,0.25);
    position: relative; z-index: 1;
}}
.rank-step.passed .rank-dot {{ background: {ACCENT_CYAN}; border-color: {ACCENT_CYAN}; }}
.rank-step.active .rank-dot {{
    background: {ACCENT_GOLD}; border-color: {ACCENT_GOLD};
    box-shadow: 0 0 14px rgba(240,197,49,0.7); width: 22px; height: 22px; margin-top: -2px;
}}
.rank-label {{ font-size: 0.62rem; color: #8b93c4; font-family: 'Rajdhani', sans-serif; font-weight: 600; white-space: nowrap; }}
.rank-step.active .rank-label {{ color: {ACCENT_GOLD}; font-weight: 700; }}

/* ---- Coaching tip cards ---- */
.tip-card {{
    background: rgba(18,16,40,0.55);
    backdrop-filter: blur(10px);
    border: 1px solid var(--tip-color, {ACCENT_CYAN});
    border-top: 3px solid var(--tip-color, {ACCENT_CYAN});
    border-radius: 14px;
    padding: 0.9rem 1rem 0.7rem 1rem;
    margin-bottom: 0.5rem;
    min-height: 92px;
    transition: box-shadow 0.15s ease, transform 0.15s ease;
}}
.tip-card:hover {{ box-shadow: 0 0 18px var(--tip-glow, rgba(46,230,255,0.25)); transform: translateY(-2px); }}
.tip-card-badge {{
    display: inline-flex; align-items: center; gap: 5px;
    font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 0.68rem;
    text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--tip-color, {ACCENT_CYAN}); margin-bottom: 0.35rem;
}}
.tip-card-title {{ font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 0.95rem; color: #f2f5fa; line-height: 1.25; }}
.tip-card-hero {{ font-size: 0.7rem; color: #8b93c4; margin-top: 0.2rem; }}

.meta-card {{
    background: rgba(233,53,193,0.06);
    border: 1px solid rgba(233,53,193,0.3);
    border-radius: 12px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.5rem;
}}
.meta-card b {{ color: {ACCENT_MAGENTA}; }}
</style>
""", unsafe_allow_html=True)

pio.templates.default = "plotly_dark"
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#dbe3f0"),
    colorway=[ACCENT_GOLD, ACCENT_CYAN, WIN_GREEN, "#c084fc", LOSS_RED],
    margin=dict(t=40, b=30, l=10, r=10),
)


def style_fig(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


def tier_badge(tier):
    color = TIER_COLORS.get(str(tier).upper(), "#888")
    return f'<span class="tier-badge" style="background:{color}">{tier}</span>'


def style_match_table(df):
    """Tint rows by result (win/loss) and highlight MVP games in gold."""
    def row_style(row):
        if row.get("mvp"):
            bg = f"background-color: {_hex_to_rgba(ACCENT_GOLD, 0.10)};"
        elif row.get("result") == "win":
            bg = f"background-color: {_hex_to_rgba(WIN_GREEN, 0.07)};"
        elif row.get("result") == "loss":
            bg = f"background-color: {_hex_to_rgba(LOSS_RED, 0.07)};"
        else:
            bg = ""
        return [bg] * len(row)
    return df.style.apply(row_style, axis=1)


def _hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def tier_grid_html(rows, tier, stat_label="win_rate", stat_suffix="%", sub_label=None):
    """rows: list of dicts with hero, thumb_url, stat, sub (optional)."""
    color = TIER_COLORS.get(str(tier).upper(), ACCENT_CYAN)
    glow = _hex_to_rgba(color, 0.45)
    chips = []
    for r in rows:
        thumb = r.get("thumb_url")
        if thumb:
            avatar_style = f"background-image:url('{thumb}');"
            inner = ""
        else:
            acolor = hero_avatar_color(r["hero"])
            avatar_style = f"background: radial-gradient(circle at 50% 35%, {acolor}33, #10131c 75%);"
            initials = "".join([w[0] for w in r["hero"].replace("-", " ").split()][:2]).upper()
            inner = (
                f'<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;'
                f'font-family:\'Rajdhani\',sans-serif;font-weight:700;font-size:0.95rem;color:{acolor};">{initials}</div>'
            )
        stat_txt = f'<div class="tc-stat">{r["stat"]}{stat_suffix}</div>' if r.get("stat") is not None else ""
        sub_txt = f'<div class="tc-sub">{r["sub"]}</div>' if r.get("sub") else ""
        chips.append(
            f'<div class="tier-chip">'
            f'<div class="tc-avatar" style="{avatar_style}position:relative;--tc-color:{color};--tc-glow:{glow};">{inner}</div>'
            f'<div class="tc-name">{r["hero"]}</div>{stat_txt}{sub_txt}'
            f'</div>'
        )
    return f'<div class="tier-grid">{"".join(chips)}</div>'


def counter_chip_row(names, color):
    """Small hero-portrait chips with no stat line, used for counter-pick lists."""
    glow = _hex_to_rgba(color, 0.45)
    chips = []
    for name in names:
        thumb = hero_image_url(name)
        if thumb:
            avatar_style = f"background-image:url('{thumb}');"
            inner = ""
        else:
            acolor = hero_avatar_color(name)
            avatar_style = f"background: radial-gradient(circle at 50% 35%, {acolor}33, #10131c 75%);"
            initials = "".join([w[0] for w in name.replace("-", " ").split()][:2]).upper()
            inner = (
                f'<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;'
                f'font-family:\'Rajdhani\',sans-serif;font-weight:700;font-size:0.95rem;color:{acolor};">{initials}</div>'
            )
        chips.append(
            f'<div class="tier-chip">'
            f'<div class="tc-avatar" style="{avatar_style}position:relative;--tc-color:{color};--tc-glow:{glow};">{inner}</div>'
            f'<div class="tc-name">{name}</div>'
            f'</div>'
        )
    return f'<div class="tier-grid">{"".join(chips)}</div>'


def role_chip(role):
    if pd.isna(role):
        return ""
    key = str(role).lower()
    label = ROLE_LABEL.get(key, str(role).title())
    icon = ROLE_ICON.get(key, "")
    return f'<span class="role-chip">{icon} {label}</span>'


def result_chip(result):
    cls = "result-win" if str(result).lower() == "win" else "result-loss"
    label = "W" if str(result).lower() == "win" else "L"
    return f'<span class="result-chip {cls}">{label}</span>'


def badge_chip(icon, label, glow=False):
    cls = "badge-chip glow" if glow else "badge-chip"
    return f'<span class="{cls}"><span class="bc-icon">{icon}</span>{label}</span>'


def tip_card_html(tip):
    meta = TIP_CATEGORY_META.get(tip["category"], {"icon": "\U0001F4A1", "color": ACCENT_CYAN, "label": str(tip["category"]).title()})
    glow = _hex_to_rgba(meta["color"], 0.35)
    hero_line = f'<div class="tip-card-hero">\U0001F464 {tip["hero"]}</div>' if pd.notna(tip.get("hero")) else ""
    return (
        f'<div class="tip-card" style="--tip-color:{meta["color"]};--tip-glow:{glow};">'
        f'<div class="tip-card-badge">{meta["icon"]} {meta["label"]}</div>'
        f'<div class="tip-card-title">{tip["title"]}</div>'
        f'{hero_line}'
        f'</div>'
    )


def render_tip_grid(tips_df, cols=3):
    rows = [tips_df.iloc[i:i + cols] for i in range(0, len(tips_df), cols)]
    for row in rows:
        columns = st.columns(cols)
        for col, (_, tip) in zip(columns, row.iterrows()):
            with col:
                st.markdown(tip_card_html(tip), unsafe_allow_html=True)
                with st.expander("Read"):
                    st.markdown(tip["body"])
                    st.caption(f"{tip['source']} · {pd.to_datetime(tip['created_at']).strftime('%Y-%m-%d')}")


def render_rank_ladder(df):
    st.subheader("Rank ladder")
    current = None
    if not df.empty and "rank_tier" in df.columns:
        recent = df.dropna(subset=["rank_tier"]).sort_values("played_at", ascending=False)
        if not recent.empty:
            current = recent.iloc[0]["rank_tier"]
    if not current:
        st.caption("No rank logged yet — send Claude a screenshot of your rank badge and it'll show up here.")
        return
    cur_low = str(current).lower()
    cur_idx = next((i for i, t in enumerate(RANK_LADDER) if t.lower() in cur_low), len(RANK_LADDER) - 1)
    steps = []
    for i, tname in enumerate(RANK_LADDER):
        state = "active" if i == cur_idx else ("passed" if i < cur_idx else "")
        steps.append(f'<div class="rank-step {state}"><div class="rank-dot"></div><div class="rank-label">{tname}</div></div>')
    st.markdown(f'<div class="rank-ladder">{"".join(steps)}</div>', unsafe_allow_html=True)
    st.caption(f"Current: **{current}**")


def render_activity_heatmap(df):
    if df.empty:
        return
    st.subheader("Activity heatmap")
    daily = df.copy()
    daily["date"] = daily["played_at"].dt.floor("D")
    grp = daily.groupby("date").agg(games=("result", "count"), wins=("result", lambda s: (s == "win").sum())).reset_index()
    grp["win_rate"] = (grp["wins"] / grp["games"] * 100).round(1)

    end = grp["date"].max()
    start = end - pd.Timedelta(weeks=11)
    start = start - pd.Timedelta(days=int(start.weekday()))
    full = pd.DataFrame({"date": pd.date_range(start, end, freq="D")}).merge(grp, on="date", how="left")
    full["games"] = full["games"].fillna(0)
    full["week"] = ((full["date"] - start).dt.days // 7).astype(int)
    full["weekday"] = full["date"].dt.weekday

    n_weeks = int(full["week"].max()) + 1
    z = [[0] * n_weeks for _ in range(7)]
    text = [[""] * n_weeks for _ in range(7)]
    for _, r in full.iterrows():
        w, d = int(r["week"]), int(r["weekday"])
        z[d][w] = r["games"]
        if r["games"] > 0:
            text[d][w] = f"{r['date'].strftime('%Y-%m-%d')}<br>{int(r['games'])} games · {r['win_rate']:.0f}% WR"
        else:
            text[d][w] = f"{r['date'].strftime('%Y-%m-%d')}<br>No games"

    week_labels = [(start + pd.Timedelta(weeks=w)).strftime("%b %d") for w in range(n_weeks)]
    fig = go.Figure(data=go.Heatmap(
        z=z, x=week_labels, y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        text=text, hoverinfo="text",
        colorscale=[[0, "rgba(18,16,40,0.55)"], [0.001, "rgba(57,255,176,0.18)"], [1, WIN_GREEN]],
        showscale=False, xgap=4, ygap=4,
    ))
    fig.update_layout(height=230)
    st.plotly_chart(style_fig(fig), use_container_width=True)
    st.caption("Darker green = more games played that day. Last 12 weeks.")


def render_time_patterns(df):
    if df.empty:
        return
    st.subheader("When do you actually win?")
    st.caption(
        "Win rate by hour (Norway time) and day of week, from your own logged matches — use it for scheduling, "
        "not as a verdict on any single game. This is the honest alternative to generic \"best hours to queue\" "
        "advice found online — it's built from your actual results, not someone else's server."
    )
    d = df.copy()
    played_local = d["played_at"].dt.tz_convert("Europe/Oslo") if d["played_at"].dt.tz is not None else d["played_at"].dt.tz_localize("UTC").dt.tz_convert("Europe/Oslo")
    d["hour"] = played_local.dt.hour
    d["dow"] = played_local.dt.day_name()

    tcol1, tcol2 = st.columns(2)
    with tcol1:
        hourly = d.groupby("hour").agg(games=("result", "count"), wins=("result", lambda s: (s == "win").sum())).reset_index()
        hourly["win_rate"] = (hourly["wins"] / hourly["games"] * 100).round(1)
        fig = px.bar(
            hourly, x="hour", y="win_rate", hover_data=["games"],
            labels={"hour": "Hour of day", "win_rate": "Win rate (%)"}, title="By hour",
        )
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with tcol2:
        dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily = (
            d.groupby("dow").agg(games=("result", "count"), wins=("result", lambda s: (s == "win").sum()))
            .reindex(dow_order).dropna(how="all").reset_index()
        )
        daily["win_rate"] = (daily["wins"] / daily["games"] * 100).round(1)
        fig2 = px.bar(
            daily, x="dow", y="win_rate", hover_data=["games"],
            labels={"dow": "Day", "win_rate": "Win rate (%)"}, title="By day of week",
        )
        fig2.update_yaxes(range=[0, 100])
        st.plotly_chart(style_fig(fig2), use_container_width=True)

    min_sample = 3
    qualified = hourly[hourly["games"] >= min_sample]
    if len(qualified) >= 2:
        best = qualified.loc[qualified["win_rate"].idxmax()]
        worst = qualified.loc[qualified["win_rate"].idxmin()]
        if best["hour"] != worst["hour"]:
            st.markdown(
                f'<div class="insight-card">'
                f'<div class="insight-label">\U0001F551 Your window, not a stranger\'s</div>'
                f'<div class="insight-body">Best so far: <b>{int(best["hour"]):02d}:00</b> Norway time '
                f'({best["win_rate"]:.0f}% over {int(best["games"])} games). '
                f'Worst so far: <b>{int(worst["hour"]):02d}:00</b> ({worst["win_rate"]:.0f}% over {int(worst["games"])} games).'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    if len(d) < 15:
        st.caption(f"Only {len(d)} games logged — these patterns are still noisy. They'll sharpen as more matches come in.")


def compute_streak_followup_wr(results, streak_len=2, streak_result="loss"):
    """Win rate on the game immediately after a run of `streak_len` consecutive `streak_result`s."""
    outcomes = [results[i] for i in range(streak_len, len(results)) if all(r == streak_result for r in results[i - streak_len:i])]
    if not outcomes:
        return None, 0
    wins = sum(1 for r in outcomes if r == "win")
    return wins / len(outcomes) * 100, len(outcomes)


def render_team_strength(df):
    if "team_stars_avg" not in df.columns:
        return
    st.subheader("Teammate vs. enemy strength")
    st.caption(
        "Logged manually — after a match that feels lopsided, check each player's profile (career star/rank count) "
        "and tell Claude the numbers so it gets added here."
    )
    logged = df.dropna(subset=["team_stars_avg", "enemy_stars_avg"])
    if logged.empty:
        st.caption("No strength-gap data logged yet.")
        return
    logged = logged.copy()
    logged["gap"] = logged["enemy_stars_avg"] - logged["team_stars_avg"]
    fig = px.bar(
        logged.sort_values("played_at"), x="played_at", y="gap", color="result",
        color_discrete_map={"win": WIN_GREEN, "loss": LOSS_RED},
        labels={"played_at": "Date", "gap": "Enemy stars − your team's stars"},
    )
    st.plotly_chart(style_fig(fig), use_container_width=True)
    avg_gap_losses = logged[logged["result"] == "loss"]["gap"].mean()
    caption = f"Avg strength gap in losses: {avg_gap_losses:+.0f} stars"
    if (logged["result"] == "win").any():
        avg_gap_wins = logged[logged["result"] == "win"]["gap"].mean()
        caption += f" · in wins: {avg_gap_wins:+.0f}"
    st.caption(caption)


def render_hero_radar(hero, role):
    if tiers.empty:
        return
    hero_row = tiers[(tiers["hero"] == hero) & (tiers["role"] == role)]
    if hero_row.empty:
        return
    role_rows = tiers[tiers["role"] == role]
    h = hero_row.iloc[0]
    metrics = ["win_rate", "pick_rate", "ban_rate"]
    labels = ["Win Rate", "Pick Rate", "Ban Rate"]
    hero_raw = [float(h.get(m) or 0) for m in metrics]
    avg_raw = [float(role_rows[m].mean() or 0) for m in metrics]

    def norm(val, metric):
        series = tiers[metric].dropna()
        lo, hi = series.min(), series.max()
        if hi <= lo:
            return 50.0
        return max(0.0, min(100.0, (val - lo) / (hi - lo) * 100))

    hero_norm = [norm(v, m) for v, m in zip(hero_raw, metrics)]
    avg_norm = [norm(v, m) for v, m in zip(avg_raw, metrics)]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=avg_norm + [avg_norm[0]], theta=labels + [labels[0]], fill="toself",
        name=f"{ROLE_LABEL.get(role, role)} avg", line=dict(color=ACCENT_PURPLE, width=2),
        fillcolor=_hex_to_rgba(ACCENT_PURPLE, 0.20),
        customdata=avg_raw + [avg_raw[0]],
        hovertemplate="%{theta}: %{customdata:.1f}%<extra>Role avg</extra>",
    ))
    fig.add_trace(go.Scatterpolar(
        r=hero_norm + [hero_norm[0]], theta=labels + [labels[0]], fill="toself",
        name=hero, line=dict(color=ACCENT_CYAN, width=2),
        fillcolor=_hex_to_rgba(ACCENT_CYAN, 0.25),
        customdata=hero_raw + [hero_raw[0]],
        hovertemplate=f"%{{theta}}: %{{customdata:.1f}}%<extra>{hero}</extra>",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, gridcolor="rgba(255,255,255,0.08)")),
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        height=320,
    )
    st.caption("Axes are scaled relative to all heroes (0-100). Hover a point for the real %.")
    st.plotly_chart(style_fig(fig), use_container_width=True)


AVATAR_PALETTE = ["#f0b429", "#4fd1ff", "#c084fc", "#4ade80", "#f87171", "#fb923c", "#38bdf8", "#f472b6"]


def parse_source(source_text):
    """Split a 'Title - https://...' source string into (title, url)."""
    if not source_text or "http" not in source_text:
        return None, None
    title_part, url_part = source_text.rsplit("http", 1)
    return title_part.strip(" -"), "http" + url_part.strip()


def youtube_thumbnail(url):
    if not url:
        return None
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return f"https://img.youtube.com/vi/{m.group(1)}/mqdefault.jpg" if m else None


def hero_avatar_color(hero):
    idx = int(hashlib.md5(hero.encode()).hexdigest(), 16) % len(AVATAR_PALETTE)
    return AVATAR_PALETTE[idx]


def hero_card_html(hero, sub="", tier=None, video_url=None, thumb_url=None):
    tier_html = tier_badge(tier) if tier else ""
    play_html = '<span class="hc-play">▶</span>' if video_url else ""
    if thumb_url:
        style = f'background-image:url({thumb_url});'
        inner = ""
    else:
        color = hero_avatar_color(hero)
        style = f"background: radial-gradient(circle at 50% 35%, {color}33, #10131c 75%);"
        initials = "".join([w[0] for w in hero.replace("-", " ").split()][:2]).upper()
        inner = (
            f'<span style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;'
            f'font-family:\'Rajdhani\',sans-serif;font-weight:700;font-size:2.2rem;color:{color};opacity:0.85;">{initials}</span>'
        )
    tag = "a" if video_url else "div"
    href = f'href="{video_url}" target="_blank"' if video_url else ""
    return (
        f'<{tag} class="hero-card" style="{style}" {href}>'
        f'{inner}{play_html}<span class="hc-tier">{tier_html}</span>'
        f'<span class="hc-label"><span class="hc-name">{hero}</span><span class="hc-sub">{sub}</span></span>'
        f'</{tag}>'
    )


def avatar_div(hero, thumb_url):
    if thumb_url:
        style = f'background-image:url({thumb_url});'
        inner = ""
    else:
        color = hero_avatar_color(hero)
        style = f"background: radial-gradient(circle at 50% 35%, {color}33, #10131c 75%);"
        initials = "".join([w[0] for w in hero.replace("-", " ").split()][:2]).upper()
        inner = (
            f'<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;'
            f'font-family:\'Rajdhani\',sans-serif;font-weight:700;font-size:1.1rem;color:{color};opacity:0.9;">{initials}</div>'
        )
    return f'<div class="roster-avatar" style="{style}position:relative;">{inner}</div>'


@st.cache_resource
def get_client():
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


@st.cache_data(ttl=30)
def load_matches():
    client = get_client()
    rows = client.table("matches").select("*").order("played_at", desc=True).execute().data
    df = pd.DataFrame(rows)
    if not df.empty:
        df["played_at"] = pd.to_datetime(df["played_at"])
        df["kda"] = (df["kills"] + df["assists"]) / df["deaths"].replace(0, 1)
    return df


@st.cache_data(ttl=30)
def load_match_heroes():
    client = get_client()
    rows = client.table("match_heroes").select("*").execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_career_snapshots():
    client = get_client()
    rows = client.table("career_snapshots").select("*").order("snapshot_date", desc=True).execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_hero_favorites():
    client = get_client()
    rows = client.table("hero_favorites").select("*").order("matches", desc=True).execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_coaching_tips():
    client = get_client()
    rows = client.table("coaching_tips").select("*").order("created_at", desc=True).execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_hero_pool():
    client = get_client()
    rows = client.table("hero_pool").select("*").execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_hero_builds():
    client = get_client()
    rows = client.table("hero_builds").select("*").execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_tier_list():
    client = get_client()
    rows = client.table("tier_list").select("*").execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_coaching_reports():
    client = get_client()
    rows = client.table("coaching_reports").select("*").order("created_at", desc=True).execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_hero_portraits():
    client = get_client()
    rows = client.table("hero_portraits").select("*").execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_hero_counters():
    client = get_client()
    rows = client.table("hero_counters").select("*").execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_top_counters():
    client = get_client()
    rows = client.table("top_counters").select("*").execute().data
    return pd.DataFrame(rows)


matches = load_matches()
snapshots = load_career_snapshots()
favorites = load_hero_favorites()
tips = load_coaching_tips()
pool = load_hero_pool()
builds = load_hero_builds()
tiers = load_tier_list()
reports = load_coaching_reports()
portraits = load_hero_portraits()
counters = load_hero_counters()
top_counters = load_top_counters()
match_heroes_df = load_match_heroes()


def hero_image_url(hero, video_url=None):
    """Prefer the real portrait; fall back to the build video's YouTube thumbnail."""
    if not portraits.empty:
        match = portraits[portraits["hero"] == hero]
        if not match.empty:
            return match.iloc[0]["portrait_url"]
    return youtube_thumbnail(video_url)


def go_to_hero(hero):
    st.session_state.selected_hero = hero
    st.rerun()


if "selected_hero" not in st.session_state:
    st.session_state.selected_hero = None

st.markdown(
    '<div class="mlbb-hero"><h1>MLBB Tracker</h1>'
    '<p>Match history, builds, meta tier list, and a coach grounded in your own stats.</p></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Hero profile page
# ---------------------------------------------------------------------------


def render_hero_profile(hero):
    if st.button("← Back to Dashboard"):
        st.session_state.selected_hero = None
        st.rerun()

    hero_roles = sorted(pool[pool["hero"] == hero]["role"].unique().tolist()) if not pool.empty else []
    portrait_row = portraits[portraits["hero"] == hero] if not portraits.empty else pd.DataFrame()
    portrait_url = portrait_row.iloc[0]["portrait_url"] if not portrait_row.empty else None

    pcol1, pcol2 = st.columns([1, 3])
    with pcol1:
        if portrait_url:
            st.image(portrait_url, use_container_width=True)
    with pcol2:
        st.markdown(f"## {hero}")
        st.markdown("".join(role_chip(r) for r in hero_roles), unsafe_allow_html=True)
        tier_bits = []
        for r in hero_roles:
            trow = tiers[(tiers["hero"] == hero) & (tiers["role"] == r)] if not tiers.empty else pd.DataFrame()
            if not trow.empty:
                tier_bits.append(f"{ROLE_LABEL.get(r, r)}: {tier_badge(trow.iloc[0]['tier'])}")
        if tier_bits:
            st.markdown("&nbsp;&nbsp;·&nbsp;&nbsp;".join(tier_bits), unsafe_allow_html=True)

    radar_roles = [r for r in hero_roles if not tiers.empty and not tiers[(tiers["hero"] == hero) & (tiers["role"] == r)].empty]
    if radar_roles:
        st.subheader("Meta radar")
        st.caption("This hero vs. the role average on official win/pick/ban rate.")
        rcols = st.columns(len(radar_roles))
        for col, r in zip(rcols, radar_roles):
            with col:
                st.markdown(f"**{ROLE_LABEL.get(r, r)}**")
                render_hero_radar(hero, r)

    threats = counters[counters["hero"] == hero] if not counters.empty else pd.DataFrame()
    favorable = counters[counters["countered_by"] == hero] if not counters.empty else pd.DataFrame()
    if not threats.empty or not favorable.empty:
        st.subheader("Counter picks")
        st.caption("Official Moonton data (mobilelegends.com/rank) — Mythical Glory+, past 7 days.")
        ccol1, ccol2 = st.columns(2)
        with ccol1:
            st.markdown("**\U0001F6E1️ Countered by** — bad matchups against this hero")
            if not threats.empty:
                st.markdown(counter_chip_row(threats["countered_by"].tolist(), LOSS_RED), unsafe_allow_html=True)
            else:
                st.caption("No data yet.")
        with ccol2:
            st.markdown("**\U00002694️ Good against** — this hero counters these")
            if not favorable.empty:
                st.markdown(counter_chip_row(favorable["hero"].tolist(), WIN_GREEN), unsafe_allow_html=True)
            else:
                st.caption("No data yet.")

    st.divider()

    fav_rows = favorites[favorites["hero"] == hero] if not favorites.empty else pd.DataFrame()
    if not fav_rows.empty:
        st.subheader("In-game stats")
        fcols = st.columns(len(fav_rows))
        for col, (_, row) in zip(fcols, fav_rows.iterrows()):
            with col:
                st.markdown(f"**{row['scope'].replace('_', ' ').title()}**")
                m1, m2, m3 = st.columns(3)
                m1.metric("Matches", int(row["matches"]) if pd.notna(row["matches"]) else "-")
                m2.metric("Win rate", f"{row['win_rate']:.1f}%" if pd.notna(row["win_rate"]) else "-")
                m3.metric("Hero Power", int(row["hero_power"]) if pd.notna(row["hero_power"]) else "-")
        st.divider()

    st.subheader("Builds")
    if not hero_roles:
        st.caption("Not in your tracked pool.")
    for r in hero_roles:
        brow = builds[(builds["hero"] == hero) & (builds["role"] == r)] if not builds.empty else pd.DataFrame()
        with st.expander(f"{ROLE_ICON.get(r, '')} {ROLE_LABEL.get(r, r)}", expanded=(len(hero_roles) == 1)):
            if brow.empty:
                st.caption("No build data yet.")
            else:
                b = brow.iloc[0]
                if pd.notna(b.get("items")):
                    st.markdown(f"**Items:** {b['items']}")
                if pd.notna(b.get("emblem")):
                    st.markdown(f"**Emblem:** {b['emblem']}")
                if pd.notna(b.get("spell")):
                    st.markdown(f"**Spell:** {b['spell']}")
                if pd.notna(b.get("combo")):
                    st.markdown(f"**Combo:** {b['combo']}")
                title, url = parse_source(b.get("source"))
                if url:
                    st.markdown(f'▶️ [{title or "Watch the build"}]({url})')
                if pd.notna(b.get("notes")):
                    st.caption(b["notes"])
    st.divider()

    st.subheader("Your matches on this hero")
    hero_matches = matches[matches["my_hero"] == hero] if not matches.empty else pd.DataFrame()
    if hero_matches.empty:
        st.caption("No logged matches on this hero yet — send Claude a screenshot after your next game on him/her.")
    else:
        g = len(hero_matches)
        w = int((hero_matches["result"] == "win").sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Games", g)
        c2.metric("Win rate", f"{w / g * 100:.1f}%")
        c3.metric("Avg KDA", f"{hero_matches['kda'].mean():.2f}")
        cols = ["played_at", "mode", "result", "kills", "deaths", "assists", "kda", "gold_earned", "mvp"]
        cols = [c for c in cols if c in hero_matches.columns]
        hm = hero_matches[cols].copy().sort_values("played_at", ascending=False)
        hm["played_at"] = hm["played_at"].dt.strftime("%Y-%m-%d %H:%M")
        hm["kda"] = hm["kda"].round(2)
        st.dataframe(style_match_table(hm), use_container_width=True, hide_index=True)
    st.divider()

    hero_tips = tips[tips["hero"] == hero] if not tips.empty else pd.DataFrame()
    if not hero_tips.empty:
        st.subheader("Coaching notes")
        for _, t in hero_tips.iterrows():
            with st.expander(f"{t['title']} ({t['category']})"):
                st.write(t["body"])
                st.caption(f"Source: {t['source']} · {pd.to_datetime(t['created_at']).strftime('%Y-%m-%d')}")


if st.session_state.selected_hero:
    render_hero_profile(st.session_state.selected_hero)
    st.stop()

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

tab_dashboard, tab_builds, tab_tierlist, tab_coach = st.tabs(["\U0001F4CA Dashboard", "\U0001F6E0️ Builds", "\U0001F3C6 Tier List", "\U0001F9E0 Coach"])


def render_tip_followthrough():
    if matches.empty or "target_metric" not in matches.columns:
        return
    tipped = matches[matches["target_metric"].notna()]
    if tipped.empty:
        return
    st.subheader("\U0001F4C8 Is it working?")
    st.caption("Whether the stat each past tip targeted has actually moved in your games on that hero since.")
    for _, t in tipped.sort_values("played_at", ascending=False).iterrows():
        metric = t["target_metric"]
        hero = t["my_hero"]
        if pd.isna(hero) or metric not in METRIC_LABEL or metric not in matches.columns:
            continue
        label = METRIC_LABEL[metric]
        before_val = t.get(metric)
        if pd.isna(before_val):
            continue
        later = matches[(matches["my_hero"] == hero) & (matches["played_at"] > t["played_at"])]
        later_vals = later[metric].dropna() if not later.empty else later
        with st.container():
            st.markdown(f"**{hero}** — {label}")
            if later_vals.empty:
                st.caption(f"Tip given {t['played_at'].strftime('%Y-%m-%d')} — waiting on your next {hero} game to check progress.")
            else:
                after_val = later_vals.mean()
                lower_is_better = metric in METRIC_LOWER_IS_BETTER
                improved = (after_val < before_val) if lower_is_better else (after_val > before_val)
                icon = "✅" if improved else "⚠️"
                verdict = "trending the right way" if improved else "hasn't moved yet — worth revisiting"
                st.caption(f"{icon} {before_val:.0f} → {after_val:.0f} avg over {len(later_vals)} game(s) since — {verdict}")
    st.divider()


# ---------------------------------------------------------------------------
# Coach
# ---------------------------------------------------------------------------
with tab_coach:
    render_tip_followthrough()

    aspire_reports = reports[reports["category"] == "aspirational"] if not reports.empty else reports
    if not aspire_reports.empty:
        st.subheader("\U0001F31F Play like your inspirations")
        for _, rep in aspire_reports.iterrows():
            with st.expander(f"**{rep['title']}**", expanded=True):
                st.markdown(rep["body"])
                st.caption(f"{rep['source']} · {pd.to_datetime(rep['created_at']).strftime('%Y-%m-%d')}")
        st.divider()

    aspire_tips = tips[tips["category"] == "aspirational"] if not tips.empty else tips
    if not aspire_tips.empty and aspire_reports.empty:
        st.subheader("\U0001F31F Play like your inspirations")
        for _, tip in aspire_tips.iterrows():
            st.markdown(f'<div class="mlbb-aspire"><b>{tip["title"]}</b><br>{tip["body"]}</div>', unsafe_allow_html=True)
        st.divider()

    pattern_tips = tips[tips["category"] == "pattern"] if not tips.empty else tips
    if not pattern_tips.empty:
        st.subheader("\U0001F50D Your patterns")
        st.caption("Mined from your own logged matches — not generic advice, things your data actually shows.")
        for _, tip in pattern_tips.sort_values("created_at", ascending=False).iterrows():
            with st.expander(f"**{tip['title']}**", expanded=True):
                st.markdown(tip["body"])
                st.caption(f"{tip['source']} · {pd.to_datetime(tip['created_at']).strftime('%Y-%m-%d')}")
        st.divider()

    meta_tips = tips[tips["category"] == "meta"] if not tips.empty else tips
    if not meta_tips.empty:
        st.subheader("⚡ Latest meta shifts")
        for _, tip in meta_tips.head(6).iterrows():
            hero_tag = f" ({tip['hero']})" if pd.notna(tip.get("hero")) else ""
            st.markdown(
                f'<div class="meta-card"><b>{tip["title"]}{hero_tag}</b><br>{tip["body"]}</div>',
                unsafe_allow_html=True,
            )
        st.divider()

    st.subheader("\U0001F4DA Coaching tips")
    st.caption("Grounded in your own stats plus current meta/community sources. Click a card to read the full tip.")
    if tips.empty:
        st.info("No coaching tips yet.")
    else:
        cats_present = sorted(tips["category"].unique().tolist())
        cat_filter = st.multiselect(
            "Filter by category", cats_present,
            format_func=lambda c: f"{TIP_CATEGORY_META.get(c, {}).get('icon', '')} {TIP_CATEGORY_META.get(c, {'label': c.title()})['label']}",
        )
        shown = tips[tips["category"].isin(cat_filter)] if cat_filter else tips
        render_tip_grid(shown.sort_values("created_at", ascending=False), cols=3)

# ---------------------------------------------------------------------------
# Builds
# ---------------------------------------------------------------------------
with tab_builds:
    st.subheader("Build recommendations")
    st.caption("Current build/emblem/combo per hero in your pool, organized by role. Click a card's portrait to open its full profile. Refreshed weekly alongside the meta research.")
    if pool.empty:
        st.info("No hero pool defined yet.")
    else:
        active_roles = [r for r in ["exp", "jungle", "mid", "roam"] if r in pool["role"].unique()]
        role_tabs = st.tabs([f"{ROLE_ICON.get(r, '')} {ROLE_LABEL.get(r, r)}" for r in active_roles])
        for role, role_tab in zip(active_roles, role_tabs):
            with role_tab:
                heroes_in_role = sorted(pool[pool["role"] == role]["hero"].unique().tolist())
                n_cols = 4
                rows = [heroes_in_role[i:i + n_cols] for i in range(0, len(heroes_in_role), n_cols)]
                for row_heroes in rows:
                    cols = st.columns(n_cols)
                    for col, hero in zip(cols, row_heroes):
                        build_row = builds[(builds["hero"] == hero) & (builds["role"] == role)] if not builds.empty else pd.DataFrame()
                        b = build_row.iloc[0] if not build_row.empty else None
                        video_title, video_url = (None, None)
                        tier, sub = None, ROLE_LABEL.get(role, role)
                        if b is not None:
                            video_title, video_url = parse_source(b.get("source"))
                            tier = b["tier"] if pd.notna(b.get("tier")) else None
                            if pd.notna(b.get("meta_win_rate")):
                                sub = f"{b['meta_win_rate']}% meta WR"
                        img_url = hero_image_url(hero, video_url)
                        with col:
                            st.markdown(
                                hero_card_html(hero, sub=sub, tier=tier, video_url=video_url, thumb_url=img_url),
                                unsafe_allow_html=True,
                            )
                            if st.button("View profile", key=f"profile-build-{role}-{hero}", use_container_width=True):
                                go_to_hero(hero)
                            if b is None:
                                st.caption("No build data researched yet.")
                            else:
                                with st.expander("Details"):
                                    if pd.notna(b.get("items")):
                                        st.markdown(f"**Items:** {b['items']}")
                                    if pd.notna(b.get("emblem")):
                                        st.markdown(f"**Emblem:** {b['emblem']}")
                                    if pd.notna(b.get("spell")):
                                        st.markdown(f"**Spell:** {b['spell']}")
                                    if pd.notna(b.get("combo")):
                                        st.markdown(f"**Combo:** {b['combo']}")
                                    if video_url:
                                        st.markdown(f'▶️ [{video_title or "Watch the build"}]({video_url})')
                                    if pd.notna(b.get("notes")):
                                        st.caption(b["notes"])
                                    st.caption(f"Updated {pd.to_datetime(b['updated_at']).strftime('%Y-%m-%d')}")

# ---------------------------------------------------------------------------
# Tier List
# ---------------------------------------------------------------------------
def personal_tier(win_rate):
    if win_rate >= 60:
        return "S"
    elif win_rate >= 52:
        return "A"
    elif win_rate >= 45:
        return "B"
    elif win_rate >= 35:
        return "C"
    return "D"


def compute_personal_tiers(scope):
    if favorites.empty:
        return pd.DataFrame()
    df = favorites[favorites["scope"] == scope].copy()
    if df.empty:
        return df
    total_games = df["matches"].sum()
    df["pick_rate"] = (df["matches"] / total_games * 100).round(2)
    df["tier"] = df["win_rate"].apply(personal_tier)
    if not pool.empty:
        role_map = pool.groupby("hero")["role"].apply(lambda s: ", ".join(sorted(set(s))))
        df["role"] = df["hero"].map(role_map)
    else:
        df["role"] = None
    return df


sub_official, sub_personal, sub_top_counters, sub_draft_helper = st.tabs(
    ["\U0001F30D Official meta", "\U0001F464 My performance", "\U0001F525 Top counters", "\U0001F3AF Draft helper"]
)

with sub_official:
    st.subheader("Current meta tier list")
    if tiers.empty:
        st.info("No tier list data yet. Send a tier-list screenshot to Claude and it'll be added here.")
    else:
        src_list = sorted(tiers['source'].dropna().unique().tolist())
        is_official = any("mobilelegends.com" in s for s in src_list)
        badge = "✅ Official Moonton data" if is_official else "Community source"
        st.caption(f"{badge} · Source: {', '.join(src_list)} · snapshot {tiers['snapshot_date'].max()}")

        pool_heroes = set(pool["hero"].unique().tolist()) if not pool.empty else set()
        c1, c2 = st.columns([1, 1])
        with c1:
            only_pool = st.checkbox("Show only heroes in my pool", value=False, key="official_only_pool")
        with c2:
            sort_by = st.selectbox("Sort by", ["Win rate", "Pick rate", "Ban rate"], index=0, key="official_sort")

        tv = tiers.copy()
        if only_pool and pool_heroes:
            tv = tv[tv["hero"].isin(pool_heroes)]

        tier_order = ["S", "A", "B", "C", "D"]
        roles_present = [r for r in ["exp", "jungle", "mid", "roam", "gold"] if r in tv["role"].dropna().unique()] or [None]
        role_pick = st.selectbox("Role", ["All"] + [ROLE_LABEL.get(r, r) for r in roles_present if r], index=0, key="official_role") if any(roles_present) else "All"
        if role_pick != "All":
            inv_label = {v: k for k, v in ROLE_LABEL.items()}
            tv = tv[tv["role"] == inv_label.get(role_pick, role_pick)]

        sort_col = {"Win rate": "win_rate", "Pick rate": "pick_rate", "Ban rate": "ban_rate"}[sort_by]
        has_extra_cols = "pick_rate" in tv.columns and "ban_rate" in tv.columns

        for t in tier_order:
            tier_rows = tv[tv["tier"].str.upper() == t] if not tv.empty else pd.DataFrame()
            if tier_rows.empty:
                continue
            st.markdown(tier_badge(t) + f"&nbsp;&nbsp;**{len(tier_rows)} heroes**", unsafe_allow_html=True)
            tier_rows = tier_rows.sort_values(sort_col, ascending=False, na_position="last") if sort_col in tier_rows.columns else tier_rows
            grid_rows = []
            for _, r in tier_rows.iterrows():
                grid_rows.append({
                    "hero": r["hero"],
                    "thumb_url": hero_image_url(r["hero"]),
                    "stat": r.get(sort_col),
                    "sub": ROLE_LABEL.get(r.get("role"), r.get("role")) if pd.notna(r.get("role")) else None,
                })
            st.markdown(tier_grid_html(grid_rows, t), unsafe_allow_html=True)
            if has_extra_cols:
                with st.expander(f"View {t}-tier as table"):
                    display = tier_rows[["hero", "role", "win_rate", "pick_rate", "ban_rate"]].copy()
                    display["role"] = display["role"].map(lambda r: ROLE_LABEL.get(r, r) if pd.notna(r) else "—")
                    display.columns = ["Hero", "Role", "Win Rate %", "Pick Rate %", "Ban Rate %"]
                    st.dataframe(display, use_container_width=True, hide_index=True)

with sub_personal:
    st.subheader("Your personal tier list")
    st.caption("Built from your own win rate, pick rate (share of your games), and hero power — not the global meta.")
    fav_scopes = [s for s in ["current_season", "all_time"] if not favorites.empty and s in favorites["scope"].unique()]
    if not fav_scopes:
        st.info("No favorite-hero stats logged yet.")
    else:
        for p_scope in fav_scopes:
            st.markdown(f"### {p_scope.replace('_', ' ').title()}")
            pdf = compute_personal_tiers(p_scope)
            if pdf.empty:
                st.info("No data for this scope yet.")
                continue
            tier_order = ["S", "A", "B", "C", "D"]
            for t in tier_order:
                tier_rows = pdf[pdf["tier"] == t].sort_values("win_rate", ascending=False)
                if tier_rows.empty:
                    continue
                st.markdown(tier_badge(t) + f"&nbsp;&nbsp;**{len(tier_rows)} heroes**", unsafe_allow_html=True)
                grid_rows = []
                for _, r in tier_rows.iterrows():
                    grid_rows.append({
                        "hero": r["hero"],
                        "thumb_url": hero_image_url(r["hero"]),
                        "stat": r.get("win_rate"),
                        "sub": f"{int(r['matches'])}g",
                    })
                st.markdown(tier_grid_html(grid_rows, t), unsafe_allow_html=True)
                with st.expander(f"View {t}-tier as table"):
                    display = tier_rows[["hero", "role", "win_rate", "pick_rate", "matches", "hero_power"]].copy()
                    display.columns = ["Hero", "Role(s)", "Win Rate %", "Pick Rate %", "Matches", "Hero Power"]
                    st.dataframe(display, use_container_width=True, hide_index=True)
            st.divider()
        st.caption("Tiers: S ≥60% · A ≥52% · B ≥45% · C ≥35% · D <35% win rate. Small sample sizes (1-2 games) can be noisy — check the Matches column.")

with sub_top_counters:
    st.subheader("Top 10 counter heroes")
    st.caption(
        "Ranked by how many heroes they counter, from official Moonton data (mobilelegends.com/rank, "
        "Mythical Glory+, past 7 days). Cross-checked against independent community sources where noted below."
    )
    if top_counters.empty:
        st.info("No top-counters data yet.")
    else:
        rank_groups = (
            top_counters.groupby(["rank", "hero"])
            .agg(
                targets=("target_hero", lambda s: sorted(s)),
                note=("corroboration_note", "first"),
                src=("corroboration_source", "first"),
            )
            .reset_index()
            .sort_values("rank")
        )
        for _, row in rank_groups.iterrows():
            hcol, ccol = st.columns([1, 5])
            with hcol:
                st.markdown(
                    f'<div style="text-align:center;">'
                    f'{avatar_div(row["hero"], hero_image_url(row["hero"]))}'
                    f'<div style="font-family:\'Orbitron\',sans-serif;color:{ACCENT_GOLD};font-weight:700;font-size:1.3rem;">#{int(row["rank"])}</div>'
                    f'<div style="font-family:\'Rajdhani\',sans-serif;font-weight:700;">{row["hero"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with ccol:
                st.caption(f"Counters {len(row['targets'])} heroes")
                st.markdown(counter_chip_row(row["targets"], WIN_GREEN), unsafe_allow_html=True)
                if pd.notna(row.get("note")):
                    src_txt = f" — [source]({row['src']})" if pd.notna(row.get("src")) else ""
                    st.caption(f"{row['note']}{src_txt}")
            st.divider()

with sub_draft_helper:
    st.subheader("Counter-pick advisor")
    st.caption(
        "Pick the enemy heroes you're facing (or expect) and see which of your own pool heroes "
        "officially counter them, from the same mobilelegends.com/rank data as the rest of this tab."
    )
    all_hero_options = sorted(tiers["hero"].unique().tolist()) if not tiers.empty else []
    enemy_picks = st.multiselect("Enemy draft", all_hero_options, key="draft_helper_enemies")

    if not enemy_picks:
        st.caption("Add one or more enemy heroes above to see your counter options.")
    elif counters.empty or pool.empty:
        st.info("No counter data or hero pool loaded yet.")
    else:
        pool_heroes = set(pool["hero"].unique().tolist())
        any_found = False
        for enemy in enemy_picks:
            enemy_row = counters[(counters["hero"] == enemy) & (counters["countered_by"].isin(pool_heroes))]
            st.markdown(f"**Vs {enemy}**")
            if enemy_row.empty:
                st.caption("None of your pool heroes are an official counter to this hero.")
            else:
                any_found = True
                picks = sorted(enemy_row["countered_by"].unique().tolist())
                st.markdown(counter_chip_row(picks, WIN_GREEN), unsafe_allow_html=True)
        if not any_found:
            st.caption("Tip: check the \U0001F525 Top counters tab above for strong picks outside your current pool.")

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
with tab_dashboard:
    insight_pool = []
    if not tips.empty:
        insight_pool.extend(tips.to_dict("records"))
    if insight_pool:
        pick = insight_pool[date.today().toordinal() % len(insight_pool)]
        hero_tag = f" · {pick['hero']}" if pd.notna(pick.get("hero")) else ""
        st.markdown(
            f'<div class="insight-card">'
            f'<div class="insight-label">✨ Insight of the day{hero_tag}</div>'
            f'<div class="insight-title">{pick["title"]}</div>'
            f'<div class="insight-body">{pick["body"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if not pool.empty:
        quick_heroes = sorted(pool["hero"].unique().tolist())
        quick_choice = st.selectbox(
            "\U0001F50D Quick jump to hero", options=["Type to search..."] + quick_heroes, index=0, key="quick_hero_search",
        )
        if quick_choice != "Type to search...":
            go_to_hero(quick_choice)

    if not pool.empty:
        st.subheader("Your roster")
        st.caption("Click any hero to open their profile.")
        for role in [r for r in ["exp", "jungle", "mid", "roam"] if r in pool["role"].unique()]:
            heroes_in_role = sorted(pool[pool["role"] == role]["hero"].unique().tolist())
            st.markdown(f'{ROLE_ICON.get(role, "")} **{ROLE_LABEL.get(role, role)}**')
            n_cols = 8
            rows = [heroes_in_role[i:i + n_cols] for i in range(0, len(heroes_in_role), n_cols)]
            for row_heroes in rows:
                cols = st.columns(n_cols)
                for col, hero in zip(cols, row_heroes):
                    build_row = builds[(builds["hero"] == hero) & (builds["role"] == role)] if not builds.empty else pd.DataFrame()
                    vurl = None
                    if not build_row.empty:
                        _, vurl = parse_source(build_row.iloc[0].get("source"))
                    thumb = hero_image_url(hero, vurl)
                    with col:
                        st.markdown(avatar_div(hero, thumb), unsafe_allow_html=True)
                        if st.button(hero, key=f"nav-roster-{role}-{hero}", use_container_width=True):
                            go_to_hero(hero)
        st.divider()

    if not snapshots.empty:
        st.subheader("Season snapshot (from in-game Statistics screen)")
        latest_date = snapshots["snapshot_date"].max()
        latest = snapshots[snapshots["snapshot_date"] == latest_date]
        scols = st.columns(len(latest))
        for col, (_, row) in zip(scols, latest.iterrows()):
            with col:
                st.markdown(f"**{row['scope'].replace('_', ' ').title()}**")
                stat_html = f"""
                <div class="mlbb-stat-row">
                  <div class="mlbb-stat"><div class="label">Matches</div><div class="value">{int(row['matches']) if pd.notna(row['matches']) else '-'}</div></div>
                  <div class="mlbb-stat"><div class="label">Win rate</div><div class="value win">{f"{row['win_rate']:.1f}%" if pd.notna(row['win_rate']) else '-'}</div></div>
                  <div class="mlbb-stat"><div class="label">KDA</div><div class="value gold">{f"{row['kda']:.2f}" if pd.notna(row['kda']) else '-'}</div></div>
                </div>
                """
                st.markdown(stat_html, unsafe_allow_html=True)
                st.caption(
                    f"MVP {int(row['mvp_count']) if pd.notna(row['mvp_count']) else '-'} · "
                    f"Teamfight {row['teamfight_participation']}% · "
                    f"Gold/min {int(row['gold_per_min']) if pd.notna(row['gold_per_min']) else '-'}"
                )
        st.caption(f"Snapshot date: {latest_date}")
        st.divider()

    if not favorites.empty:
        st.subheader("Favorite heroes (in-game)")
        fav_scopes = [s for s in ["current_season", "all_time"] if s in favorites["scope"].unique()]
        scope_choice = st.radio("Scope", fav_scopes, horizontal=True,
                                 format_func=lambda s: s.replace("_", " ").title()) if len(fav_scopes) > 1 else fav_scopes[0]
        fav_current = favorites[favorites["scope"] == scope_choice].sort_values("matches", ascending=False).copy()
        fav_current["label"] = fav_current.apply(lambda r: f"{r['win_rate']:.1f}%<br>({int(r['matches'])}g)", axis=1)
        fig = px.bar(
            fav_current, x="hero", y="win_rate", hover_data=["matches", "hero_power"],
            text="label",
            labels={"hero": "Hero", "win_rate": "Win rate (%)"},
            title=f"{scope_choice.replace('_', ' ').title()} — win rate & matches by favorite hero",
        )
        fig.update_traces(textposition="outside", textfont_size=11)
        fig.update_yaxes(range=[0, max(fav_current["win_rate"].max() * 1.25, 20)])
        st.plotly_chart(style_fig(fig), use_container_width=True)
        st.dataframe(
            fav_current[["hero", "matches", "win_rate", "hero_power"]],
            use_container_width=True, hide_index=True,
        )
        st.divider()

    if matches.empty:
        st.info("No matches logged yet. Send a post-match screenshot to Claude to log your first game.")
        st.stop()

    with st.sidebar:
        st.header("Filters")
        modes = sorted(matches["mode"].dropna().unique().tolist())
        mode_filter = st.multiselect("Mode", modes, default=modes)
        heroes = sorted(matches["my_hero"].dropna().unique().tolist())
        hero_filter = st.multiselect("Hero", heroes, default=[])
        if st.button("Refresh data"):
            st.cache_data.clear()
            st.rerun()

    df = matches[matches["mode"].isin(mode_filter)] if mode_filter else matches
    if hero_filter:
        df = df[df["my_hero"].isin(hero_filter)]

    total_games = len(df)
    wins = int((df["result"] == "win").sum())
    win_rate = wins / total_games * 100 if total_games else 0
    avg_kda = df["kda"].mean() if total_games else 0
    avg_kills = df["kills"].mean() if total_games else 0
    avg_deaths = df["deaths"].mean() if total_games else 0
    avg_assists = df["assists"].mean() if total_games else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Games", total_games)
    c2.metric("Win rate", f"{win_rate:.1f}%")
    c3.metric("Avg KDA", f"{avg_kda:.2f}")
    c4.metric("Avg K/D/A", f"{avg_kills:.1f} / {avg_deaths:.1f} / {avg_assists:.1f}")
    c5.metric("MVPs", int(df["mvp"].sum()))

    st.divider()

    # --- Win / loss tracker ---
    st.subheader("Win / loss tracker")
    wl = df.sort_values("played_at")
    if wl.empty:
        st.caption("No matches to show yet.")
    else:
        results = wl["result"].tolist()
        chips = "".join(result_chip(r) for r in results)
        st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:0.6rem;">{chips}</div>', unsafe_allow_html=True)

        cur_streak_result = results[-1]
        cur_streak = 0
        for r in reversed(results):
            if r == cur_streak_result:
                cur_streak += 1
            else:
                break
        best_win_streak, cur = 0, 0
        for r in results:
            cur = cur + 1 if r == "win" else 0
            best_win_streak = max(best_win_streak, cur)

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Wins", int((wl["result"] == "win").sum()))
        s2.metric("Losses", int((wl["result"] == "loss").sum()))
        s3.metric("Current streak", f"{cur_streak} {'W' if cur_streak_result == 'win' else 'L'}")
        s4.metric("Best win streak", best_win_streak)

        badges = []
        if cur_streak >= 2:
            badges.append(badge_chip(
                "\U0001F525", f"{cur_streak} {'win' if cur_streak_result == 'win' else 'loss'} streak",
                glow=(cur_streak_result == "win" and cur_streak >= 3),
            ))
        if best_win_streak >= 2:
            badges.append(badge_chip("\U0001F3C6", f"Best streak {best_win_streak}W"))
        mvp_n = int(df["mvp"].sum())
        if mvp_n:
            badges.append(badge_chip("\U00002B50", f"{mvp_n} MVPs"))
        if not snapshots.empty:
            latest_snap = snapshots[snapshots["snapshot_date"] == snapshots["snapshot_date"].max()]
            season_snap = latest_snap[latest_snap["scope"] == "current_season"]
            srow = season_snap.iloc[0] if not season_snap.empty else (latest_snap.iloc[0] if not latest_snap.empty else None)
            if srow is not None:
                if pd.notna(srow.get("savage")) and srow["savage"] > 0:
                    badges.append(badge_chip("\U0001F480", f"{int(srow['savage'])} Savage"))
                if pd.notna(srow.get("maniac")) and srow["maniac"] > 0:
                    badges.append(badge_chip("\U000026A1", f"{int(srow['maniac'])} Maniac"))
                if pd.notna(srow.get("legendary")) and srow["legendary"] > 0:
                    badges.append(badge_chip("\U0001F451", f"{int(srow['legendary'])} Legendary"))
        if badges:
            st.markdown("".join(badges), unsafe_allow_html=True)

        if cur_streak_result == "loss" and cur_streak >= 2:
            follow_wr, n = compute_streak_followup_wr(results, streak_len=2, streak_result="loss")
            if follow_wr is not None:
                small_sample = " Small sample — take this as a nudge, not gospel." if n < 5 else " Worth considering a short break before queuing again."
                st.markdown(
                    f'<div class="mlbb-tip" style="border-left-color:{LOSS_RED};">'
                    f'<b>\U000026D4 Stop-loss check</b><br>'
                    f"You're on a {cur_streak}-loss streak. Historically, your win rate on the next game after "
                    f'2+ straight losses is <b>{follow_wr:.0f}%</b> (from {n} occurrence{"s" if n != 1 else ""} in your history).'
                    f"{small_sample}"
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.divider()

    render_activity_heatmap(df)
    st.divider()
    render_time_patterns(df)
    st.divider()
    render_team_strength(df)
    st.divider()
    render_rank_ladder(df)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Win rate by hero")
        known_hero = df.dropna(subset=["my_hero"])
        unknown_count = len(df) - len(known_hero)
        if known_hero.empty:
            st.caption("No hero identified yet for these matches — tell Claude which hero you played per match to unlock this chart.")
        else:
            hero_stats = (
                known_hero.groupby("my_hero")
                .agg(games=("result", "count"), wins=("result", lambda s: (s == "win").sum()))
                .reset_index()
            )
            hero_stats["win_rate"] = (hero_stats["wins"] / hero_stats["games"] * 100).round(1)
            hero_stats = hero_stats.sort_values("games", ascending=False)
            hero_stats["label"] = hero_stats.apply(lambda r: f"{r['win_rate']:.1f}% ({int(r['games'])}g)", axis=1)
            fig = px.bar(hero_stats, x="my_hero", y="win_rate", hover_data=["games", "wins"], text="label",
                         labels={"my_hero": "Hero", "win_rate": "Win rate (%)"})
            fig.update_traces(textposition="outside", textfont_size=11)
            fig.update_yaxes(range=[0, max(hero_stats["win_rate"].max() * 1.25, 20)])
            st.plotly_chart(style_fig(fig), use_container_width=True)
            if unknown_count:
                st.caption(f"{unknown_count} match(es) have no hero identified yet.")

    with col2:
        st.subheader("Win rate by lane")
        role_stats = None
        source_note = ""
        if df["my_role"].notna().any():
            role_stats = (
                df.dropna(subset=["my_role"])
                .groupby("my_role")
                .agg(games=("result", "count"), wins=("result", lambda s: (s == "win").sum()))
                .reset_index()
                .rename(columns={"my_role": "role"})
            )
            role_stats["win_rate"] = (role_stats["wins"] / role_stats["games"] * 100).round(1)
            source_note = "From your logged matches."
        elif not pool.empty and not favorites.empty:
            fav_cs = favorites[favorites["scope"] == "current_season"]
            merged = pool.merge(fav_cs[["hero", "matches", "win_rate"]], on="hero", how="left").dropna(subset=["matches"])
            if not merged.empty:
                merged["wins"] = merged["matches"] * merged["win_rate"] / 100
                role_stats = merged.groupby("role").agg(games=("matches", "sum"), wins=("wins", "sum")).reset_index()
                role_stats["win_rate"] = (role_stats["wins"] / role_stats["games"] * 100).round(1)
                source_note = "Estimated from your favorite-hero stats (no per-match lane logged yet)."

        if role_stats is None or role_stats.empty:
            st.caption("No lane data yet.")
        else:
            role_stats["role_label"] = role_stats["role"].map(lambda r: ROLE_LABEL.get(r, r))
            role_stats["label"] = role_stats.apply(lambda r: f"{r['win_rate']:.1f}% ({int(r['games'])}g)", axis=1)
            fig = px.bar(role_stats, x="role_label", y="win_rate", hover_data=["games"], text="label",
                         labels={"role_label": "Lane", "win_rate": "Win rate (%)"})
            fig.update_traces(textposition="outside", textfont_size=11)
            fig.update_yaxes(range=[0, max(role_stats["win_rate"].max() * 1.25, 20)])
            st.plotly_chart(style_fig(fig), use_container_width=True)
            st.caption(source_note)

    st.subheader("KDA & win rate over time")
    trend = df.sort_values("played_at").copy()
    trend["rolling_wr"] = trend["result"].eq("win").rolling(5, min_periods=1).mean() * 100
    marker_colors = trend["result"].map({"win": WIN_GREEN, "loss": LOSS_RED})
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=trend["played_at"], y=trend["kda"], mode="lines+markers", name="KDA",
            line=dict(color=ACCENT_GOLD, width=2),
            marker=dict(color=marker_colors, size=10, line=dict(width=1, color="#0a0e1a")),
            hovertext=trend["result"], hovertemplate="%{x}<br>KDA %{y:.2f}<br>%{hovertext}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=trend["played_at"], y=trend["rolling_wr"], mode="lines", name="Win rate (5-game rolling)",
            line=dict(color=ACCENT_CYAN, width=2, dash="dot"),
        ),
        secondary_y=True,
    )
    fig.update_yaxes(title_text="KDA", secondary_y=False)
    fig.update_yaxes(title_text="Win rate % (rolling)", range=[0, 100], secondary_y=True)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(style_fig(fig), use_container_width=True)
    st.caption("Marker color = win (green) / loss (red). Dotted line = rolling win rate over the last 5 games.")

    if df["rank_tier"].notna().any():
        st.subheader("Rank progression")
        rank_trend = df.dropna(subset=["rank_points"]).sort_values("played_at")
        if not rank_trend.empty:
            fig = px.line(rank_trend, x="played_at", y="rank_points", markers=True, hover_data=["rank_tier"],
                          labels={"played_at": "Date", "rank_points": "Rank points"})
            st.plotly_chart(style_fig(fig), use_container_width=True)

    st.divider()
    st.subheader("Match history")

    display_cols = ["played_at", "mode", "result", "my_hero", "my_role", "kills", "deaths",
                     "assists", "kda", "gold_earned", "damage_dealt", "mvp", "rank_tier", "notes"]
    display_cols = [c for c in display_cols if c in df.columns]
    history = df[display_cols].copy()
    history["played_at"] = history["played_at"].dt.strftime("%Y-%m-%d %H:%M")
    history["kda"] = history["kda"].round(2)
    st.dataframe(style_match_table(history), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Match detail")

    match_options = df.apply(
        lambda r: f"{r['played_at'].strftime('%Y-%m-%d %H:%M')} — {r['my_hero'] if pd.notna(r['my_hero']) else 'unknown hero'} ({r['result']})",
        axis=1,
    )
    selected = st.selectbox("Pick a match", options=list(match_options), index=0 if len(match_options) else None)
    if selected is not None:
        sel_idx = match_options[match_options == selected].index[0]
        match_row = df.loc[sel_idx]
        match_id = match_row["id"]

        if pd.notna(match_row.get("commentary")):
            result_color = WIN_GREEN if match_row["result"] == "win" else LOSS_RED
            st.markdown(
                f'<div class="mlbb-tip" style="border-left-color:{result_color};">'
                f'<b>\U0001F9E0 Coach\'s take</b><br>{match_row["commentary"]}'
                f'</div>',
                unsafe_allow_html=True,
            )
            if pd.notna(match_row.get("tip")):
                st.markdown(f'<div class="mlbb-tip"><b>\U0001F4A1 Try this next time</b><br>{match_row["tip"]}</div>', unsafe_allow_html=True)
        else:
            st.caption(
                "No commentary logged for this match yet"
                + ("" if pd.notna(match_row.get("my_hero")) else " — hero wasn't recorded for it either")
                + ". Send Claude the hero you played and it'll get added."
            )

        picks = match_heroes_df[match_heroes_df["match_id"] == match_id] if not match_heroes_df.empty else pd.DataFrame()
        if not picks.empty:
            ally = picks[picks["team"] == "ally"]
            enemy = picks[picks["team"] == "enemy"]
            pc1, pc2 = st.columns(2)
            with pc1:
                st.markdown("**Ally team**")
                st.table(ally[["hero", "role", "is_me"]].reset_index(drop=True))
            with pc2:
                st.markdown("**Enemy team**")
                st.table(enemy[["hero", "role"]].reset_index(drop=True))
