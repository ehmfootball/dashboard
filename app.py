
import streamlit as st
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

st.set_page_config(
    page_title="Football Recruitment Dashboard",
    page_icon="⚽",
    layout="wide"
)

# ---------- DASHBOARD STYLE ----------
st.markdown("""
<style>
.stApp {
    background-color: #080E1A;
    color: #F1F5F9;
}
</style>
""", unsafe_allow_html=True)

st.title("⚽ Football Recruitment Dashboard")
st.caption("World Cup 2026 | Shot Location Analysis")

DATA_URL = ("https://huggingface.co/datasets/"
            "ehxnbuilds/world-cup-2026-events/"
            "resolve/main/world_cup_events_master.csv"
)

# ---------- LOAD AND PREPARE DATA ----------
@st.cache_data
def load_shots(path):
    df = pd.read_csv(
        path,
        usecols=lambda col: col in [
            "type", "team", "player", "x", "y", "isOwnGoal"
        ],
        low_memory=False
    )

    df["event_name"] = df["type"].str.extract(
        r"'displayName': '([^']+)'"
    )

    shot_types = [
        "Goal", "SavedShot", "MissedShots", "ShotOnPost"
    ]

    shots = df[df["event_name"].isin(shot_types)].copy()

    labels = {
        "Goal": "Goal",
        "SavedShot": "Saved",
        "MissedShots": "Missed",
        "ShotOnPost": "Woodwork"
    }

    shots["shot_outcome"] = shots["event_name"].map(labels)

    shots["is_own_goal"] = (
        shots["isOwnGoal"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("true")
    )

    shots["x"] = pd.to_numeric(shots["x"], errors="coerce")
    shots["y"] = pd.to_numeric(shots["y"], errors="coerce")

    shots = shots.dropna(subset=["x", "y"])

    return shots


with st.spinner("Downloading and loading World Cup shot data"):
    shots = load_shots(DATA_URL)

# Keep all records in memory, but exclude own goals from this analysis.
analysis_shots = shots[~shots["is_own_goal"]].copy()

# ---------- FILTERS ----------
st.subheader("Shot Map")

filter_col1, filter_col2 = st.columns(2)

teams = sorted(
    analysis_shots["team"].dropna().astype(str).unique().tolist()
)

with filter_col1:
    selected_team = st.selectbox(
        "Select team",
        ["All teams"] + teams
    )

if selected_team != "All teams":
    team_shots = analysis_shots[
        analysis_shots["team"].astype(str) == selected_team
    ].copy()
else:
    team_shots = analysis_shots.copy()

players = sorted({
    str(player)
    for player in team_shots["player"].dropna()
    if str(player).strip()
})

with filter_col2:
    selected_player = st.selectbox(
        "Select player",
        options=["All players"] + players,
        key="player_filter"
    )

if selected_player != "All players":
    filtered_shots = team_shots[
        team_shots["player"].astype(str) == selected_player
    ].copy()
else:
    filtered_shots = team_shots.copy()

# ---------- SUMMARY METRICS ----------
total_shots = len(filtered_shots)
total_goals = int((filtered_shots["shot_outcome"] == "Goal").sum())

conversion_rate = (
    total_goals / total_shots * 100
    if total_shots > 0 else 0
)

metric1, metric2, metric3 = st.columns(3)

metric1.metric("Total Shots", f"{total_shots:,}")
metric2.metric("Goals", f"{total_goals:,}")
metric3.metric("Shot Conversion", f"{conversion_rate:.1f}%")

st.caption(
    "Shot conversion = goals divided by recorded shots. "
    "Flagged own goals are excluded."
)

# ---------- DRAW SHOT MAP ----------
if filtered_shots.empty:
    st.warning("No shot records match these filters.")
else:
    pitch = VerticalPitch(
        pitch_type="opta",
        pitch_color="#0B1220",
        line_color="#52647A",
        linewidth=1.2
    )

    fig, ax = pitch.draw(figsize=(8, 10))

    outcome_colours = {
        "Goal": "#00E5A8",
        "Saved": "#36A2FF",
        "Missed": "#FF647C",
        "Woodwork": "#FFD166"
    }

    for outcome, colour in outcome_colours.items():
        selected = filtered_shots[
            filtered_shots["shot_outcome"] == outcome
        ]

        if not selected.empty:
            pitch.scatter(
                selected["x"],
                selected["y"],
                ax=ax,
                s=65,
                c=colour,
                edgecolors="white",
                linewidth=0.6,
                alpha=0.9,
                label=outcome,
                zorder=3
            )

    ax.legend(
        loc="upper left",
        bbox_to_anchor=(0.0, 1.02),
        ncol=2,
        frameon=False,
        labelcolor="white"
    )

    fig.patch.set_facecolor("#080E1A")
    ax.set_title(
        "Shot Locations by Outcome",
        color="white",
        fontsize=15,
        pad=18
    )

    st.pyplot(fig)
    plt.close(fig)

    # ---------- OUTCOME TABLE ----------
    st.subheader("Shot Outcome Breakdown")

    outcome_counts = (
        filtered_shots["shot_outcome"]
        .value_counts()
        .reindex(
            ["Goal", "Saved", "Missed", "Woodwork"],
            fill_value=0
        )
    )

    st.dataframe(
        outcome_counts.rename("Number of shots"),
        use_container_width=True
    )

