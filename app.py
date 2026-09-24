import re
import hashlib
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

ACCENT_GOLD = "#f0b429"
ACCENT_CYAN = "#4fd1ff"
BG_DEEP = "#0a0e1a"
BG_PANEL = "#111a2e"
WIN_GREEN = "#4ade80"
LOSS_RED = "#f87171"

TIER_COLORS = {"S": "#ff4d6d", "A": "#ff9f43", "B": "#f2c94c", "C": "#6fcf97", "D": "#9099a8"}
ROLE_ICON = {"exp": "⚔️", "jungle": "\U0001F332", "mid": "\U0001F52E", "roam": "\U0001F6E1️", "gold": "\U0001F3F9"}
ROLE_LABEL = {"exp": "EXP Lane", "jungle": "Jungle", "mid": "Mid Lane", "roam": "Roam", "gold": "Gold Lane"}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}
.stApp {{
    background: radial-gradient(circle at 10% 0%, #14213d 0%, {BG_DEEP} 45%) fixed;
}}
h1, h2, h3, .mlbb-title {{
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 0.02em;
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {BG_PANEL} 0%, {BG_DEEP} 100%);
    border-right: 1px solid rgba(240,180,41,0.15);
}}
.mlbb-hero {{
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.2rem;
    border-radius: 16px;
    background: linear-gradient(120deg, rgba(240,180,41,0.10), rgba(79,209,255,0.06));
    border: 1px solid rgba(240,180,41,0.25);
}}
.mlbb-hero h1 {{
    margin: 0;
    font-size: 2.4rem;
    background: linear-gradient(90deg, {ACCENT_GOLD}, {ACCENT_CYAN});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.mlbb-hero p {{
    margin: 0.3rem 0 0 0;
    color: #9fb0c9;
    font-size: 0.95rem;
}}
.mlbb-card {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.9rem;
}}
.mlbb-stat-row {{ display: flex; gap: 0.9rem; flex-wrap: wrap; }}
.mlbb-stat {{
    flex: 1 1 140px;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 0.8rem 1rem;
}}
.mlbb-stat .label {{ color: #8b9bb4; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }}
.mlbb-stat .value {{ font-family: 'Rajdhani', sans-serif; font-size: 1.7rem; font-weight: 700; color: #f2f5fa; }}
.mlbb-stat .value.gold {{ color: {ACCENT_GOLD}; }}
.mlbb-stat .value.cyan {{ color: {ACCENT_CYAN}; }}
.mlbb-stat .value.win {{ color: {WIN_GREEN}; }}

.tier-badge {{
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 30px; height: 26px; padding: 0 8px;
    border-radius: 7px; font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 0.95rem;
    color: #10131c; margin-right: 6px;
}}
.role-chip {{
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    background: rgba(79,209,255,0.12); border: 1px solid rgba(79,209,255,0.35);
    color: {ACCENT_CYAN}; font-size: 0.78rem; margin-right: 6px;
}}
.result-chip {{
    display: inline-flex; align-items:center; justify-content:center;
    width: 26px; height: 26px; border-radius: 50%; font-size: 0.72rem; font-weight: 700;
}}
.result-win {{ background: rgba(74,222,128,0.18); color: {WIN_GREEN}; border: 1px solid rgba(74,222,128,0.5); }}
.result-loss {{ background: rgba(248,113,113,0.18); color: {LOSS_RED}; border: 1px solid rgba(248,113,113,0.5); }}

.mlbb-tip {{
    border-left: 3px solid {ACCENT_GOLD};
    background: rgba(240,180,41,0.06);
    padding: 0.7rem 1rem;
    border-radius: 0 10px 10px 0;
    margin-bottom: 0.6rem;
}}
.mlbb-aspire {{
    border-left: 3px solid {ACCENT_CYAN};
    background: rgba(79,209,255,0.07);
    padding: 0.9rem 1.1rem;
    border-radius: 0 10px 10px 0;
    margin-bottom: 0.8rem;
}}
[data-testid="stMetric"] {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 0.6rem 0.8rem 0.3rem 0.8rem;
}}
.streamlit-expanderHeader {{
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
}}

.hero-card {{
    position: relative;
    display: block;
    height: 150px;
    border-radius: 14px;
    overflow: hidden;
    background-size: cover;
    background-position: center 15%;
    border: 1px solid rgba(255,255,255,0.10);
    text-decoration: none;
    margin-bottom: 0.5rem;
    transition: border-color 0.15s ease, transform 0.15s ease;
}}
.hero-card:hover {{
    border-color: rgba(240,180,41,0.55);
    transform: translateY(-2px);
}}
.hero-card::after {{
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(to top, rgba(6,9,17,0.96) 0%, rgba(6,9,17,0.25) 55%, rgba(6,9,17,0.0) 100%);
}}
.hero-card .hc-label {{
    position: absolute; left: 10px; right: 10px; bottom: 8px; z-index: 2;
}}
.hero-card .hc-name {{
    font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 1.05rem; color: #f5f7fb;
    text-shadow: 0 1px 4px rgba(0,0,0,0.6);
}}
.hero-card .hc-sub {{ font-size: 0.72rem; color: #b9c4d6; }}
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
    border: 2px solid rgba(255,255,255,0.12);
    margin-bottom: 4px;
}}
.stButton > button {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.14);
    color: #dbe3f0;
    border-radius: 8px;
    font-size: 0.78rem;
    padding: 0.15rem 0.4rem;
}}
.stButton > button:hover {{
    border-color: rgba(240,180,41,0.6);
    color: {ACCENT_GOLD};
}}
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
    play_html = '<div class="hc-play">▶</div>' if video_url else ""
    if thumb_url:
        style = f'background-image:url({thumb_url});'
        inner = ""
    else:
        color = hero_avatar_color(hero)
        style = f"background: radial-gradient(circle at 50% 35%, {color}33, #10131c 75%);"
        initials = "".join([w[0] for w in hero.replace("-", " ").split()][:2]).upper()
        inner = (
            f'<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;'
            f'font-family:\'Rajdhani\',sans-serif;font-weight:700;font-size:2.2rem;color:{color};opacity:0.85;">{initials}</div>'
        )
    tag = "a" if video_url else "div"
    href = f'href="{video_url}" target="_blank"' if video_url else ""
    return (
        f'<{tag} class="hero-card" style="{style}" {href}>'
        f'{inner}{play_html}<div class="hc-tier">{tier_html}</div>'
        f'<div class="hc-label"><div class="hc-name">{hero}</div><div class="hc-sub">{sub}</div></div>'
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


matches = load_matches()
snapshots = load_career_snapshots()
favorites = load_hero_favorites()
tips = load_coaching_tips()
pool = load_hero_pool()
builds = load_hero_builds()
tiers = load_tier_list()
reports = load_coaching_reports()
portraits = load_hero_portraits()
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
        st.dataframe(hm, use_container_width=True, hide_index=True)
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

# ---------------------------------------------------------------------------
# Coach
# ---------------------------------------------------------------------------
with tab_coach:
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
            st.warning(f"**{tip['title']}{hero_tag}** — {tip['body']}")
        st.divider()

    st.subheader("Coaching tips")
    st.caption("Generated from your NotebookLM coach — grounded in your own stats plus current meta/community sources.")
    if tips.empty:
        st.info("No coaching tips yet.")
    else:
        cat_filter = st.multiselect("Filter by category", sorted(tips["category"].unique().tolist()))
        shown = tips[tips["category"].isin(cat_filter)] if cat_filter else tips
        for _, tip in shown.iterrows():
            hero_tag = f" · {tip['hero']}" if pd.notna(tip.get("hero")) else ""
            with st.expander(f"{tip['title']}  ({tip['category']}{hero_tag})"):
                st.write(tip["body"])
                st.caption(f"Source: {tip['source']} · {pd.to_datetime(tip['created_at']).strftime('%Y-%m-%d')}")

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
with tab_tierlist:
    st.subheader("Current meta tier list")
    if tiers.empty:
        st.info("No tier list data yet. Send a tier-list screenshot to Claude and it'll be added here.")
    else:
        st.caption(f"Source(s): {', '.join(sorted(tiers['source'].dropna().unique().tolist()))} · patch {tiers['patch'].dropna().iloc[0] if tiers['patch'].notna().any() else '—'}")
        pool_heroes = set(pool["hero"].unique().tolist()) if not pool.empty else set()
        only_pool = st.checkbox("Show only heroes in my pool", value=True)
        tv = tiers.copy()
        if only_pool and pool_heroes:
            tv = tv[tv["hero"].isin(pool_heroes)]

        tier_order = ["S", "A", "B", "C", "D"]
        roles_present = [r for r in ["exp", "jungle", "mid", "roam", "gold"] if r in tv["role"].dropna().unique()] or [None]
        role_pick = st.selectbox("Role", ["All"] + [ROLE_LABEL.get(r, r) for r in roles_present if r], index=0) if any(roles_present) else "All"
        if role_pick != "All":
            inv_label = {v: k for k, v in ROLE_LABEL.items()}
            tv = tv[tv["role"] == inv_label.get(role_pick, role_pick)]

        for t in tier_order:
            tier_rows = tv[tv["tier"].str.upper() == t] if not tv.empty else pd.DataFrame()
            if tier_rows.empty:
                continue
            st.markdown(tier_badge(t) + f"&nbsp;&nbsp;**{len(tier_rows)} heroes**", unsafe_allow_html=True)
            chips = "".join(
                f'<span class="role-chip" style="color:#eaeef5;border-color:rgba(255,255,255,0.18);background:rgba(255,255,255,0.04)">'
                f'{r["hero"]}{" · " + str(r["win_rate"]) + "%" if pd.notna(r["win_rate"]) else ""}</span>'
                for _, r in tier_rows.sort_values("hero").iterrows()
            )
            st.markdown(f'<div style="margin-bottom:1rem">{chips}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
with tab_dashboard:
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
    st.dataframe(history, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Match detail (draft)")

    match_options = df.apply(
        lambda r: f"{r['played_at'].strftime('%Y-%m-%d %H:%M')} — {r['my_hero']} ({r['result']})",
        axis=1,
    )
    selected = st.selectbox("Pick a match", options=list(match_options), index=0 if len(match_options) else None)
    if selected is not None:
        sel_idx = match_options[match_options == selected].index[0]
        match_id = df.loc[sel_idx, "id"]
        picks = match_heroes_df[match_heroes_df["match_id"] == match_id] if not match_heroes_df.empty else pd.DataFrame()
        if picks.empty:
            st.caption("No draft data logged for this match.")
        else:
            ally = picks[picks["team"] == "ally"]
            enemy = picks[picks["team"] == "enemy"]
            pc1, pc2 = st.columns(2)
            with pc1:
                st.markdown("**Ally team**")
                st.table(ally[["hero", "role", "is_me"]].reset_index(drop=True))
            with pc2:
                st.markdown("**Enemy team**")
                st.table(enemy[["hero", "role"]].reset_index(drop=True))
