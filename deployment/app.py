import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Chess Openings Dashboard", layout="wide")
st.title("♟️ Chess Openings & Skill Level")
st.caption("Data: Lichess games dataset (Kaggle, datasnaek/chess)")


@st.cache_data
def load():
    df = pd.read_csv("games.csv")
    df["avg_rating"] = (df["white_rating"] + df["black_rating"]) / 2
    df["opening_family"] = (df["opening_name"].str.split(":").str[0]
                            .str.split("|").str[0].str.strip())
    return df


df = load()

# Sidebar filter that updates every chart
lo, hi = st.sidebar.slider("Average rating range", 700, 2700, (700, 2700), step=100)
df = df[df["avg_rating"].between(lo, hi)]

sns.set_theme(style="whitegrid")

row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

# --- Chart 1: Slope graph of openings by skill group ---
with row1_col1:
    st.subheader("1. Which Openings Do Beginners, Novices, and Experts Play?")

    chart_df = df.copy()
    chart_df["group"] = "Novice (1100–2100)"
    chart_df.loc[chart_df["avg_rating"] < 1100, "group"] = "Beginner (<1100)"
    chart_df.loc[chart_df["avg_rating"] > 2100, "group"] = "Expert (>2100)"
    group_order = ["Beginner (<1100)", "Novice (1100–2100)", "Expert (>2100)"]

    share = (chart_df.groupby("group")["opening_family"].value_counts(normalize=True)
               .rename("pct").reset_index())

    if share.empty:
        st.warning("No games in the selected rating range.")
    else:
        # Keep openings that are top 5 in any group
        top = share.groupby("group").head(5)["opening_family"].unique()
        share = share[share["opening_family"].isin(top)]

        sns.set_theme(style="whitegrid")
        g = sns.catplot(data=share, x="group", y="pct", hue="opening_family",
                        kind="point", order=group_order,
                        height=5, aspect=1.0, markersize=8, linewidth=2)
        g.set_axis_labels("", "% of Games in Group")
        g.set(title="Which Openings Do Beginners, Novices, and Experts Play?")
        ticks = [i / 100 for i in range(0, int(share["pct"].max() * 100) + 3, 2)]
        g.set(yticks=ticks, yticklabels=[f"{int(t*100)}%" for t in ticks])
        g.tick_params(axis="x", labelsize=8)
        st.pyplot(g.figure)
        plt.close(g.figure)

# --- Chart 2: Sicilian Defense win share by rating ---
with row1_col2:
    st.subheader("2. Sicilian Defense: Who Wins?")

    sicilian = df[df["opening_name"].str.contains("Sicilian Defense", na=False)].copy()

    if sicilian.empty:
        st.warning("No Sicilian Defense games in the selected rating range.")
    else:
        # Line the bins up on round hundreds (1200, 1300, ...)
        s_lo = int(sicilian["black_rating"].min() // 100 * 100 + 100)
        s_hi = int(sicilian["black_rating"].max() // 100 * 100 + 100)

        sns.set_theme(style="darkgrid")

        g = sns.displot(
            data=sicilian,
            x="black_rating",
            hue="winner",
            hue_order=["white", "draw", "black"],
            palette={"white": "#FFFDD0", "black": "#B58863", "draw": "#D3D3D3"},
            kind="hist",
            binwidth=100,
            binrange=(s_lo, s_hi),
            multiple="fill",       # each bin sums to 100%
            edgecolor="black",
            alpha=1,
            height=5,
            aspect=1.3,
        )

        g.refline(y=.5, color="black", linestyle="--", linewidth=2)
        for y in [0.25, 0.75]:
            g.refline(y=y, color="black", linestyle="--", linewidth=1)

        g.set_axis_labels("Black's Rating  (100-point bins)", "% of Games")
        g.set(
            title="Sicilian Defense: Share of Wins by Color Across Rating Levels",
            xticks=range(s_lo, s_hi + 1, 100),
            yticks=[0, 0.25, 0.5, 0.75, 1],
            yticklabels=["0%", "25%", "50%", "75%", "100%"],
        )
        g.tick_params(axis="x", rotation=45, labelsize=8)
        st.pyplot(g.figure)
        plt.close(g.figure)

# --- Chart 3: Do stronger players follow opening theory longer? ---
with row2_col1:
    st.subheader("3. Do Stronger Players Follow Opening Theory Longer?")

    df["rating_bin"] = (df["avg_rating"] // 100 * 100).astype(int)

    sns.set_theme(style="darkgrid")
    g = sns.relplot(
        data=df,
        x="rating_bin",
        y="opening_ply",
        kind="line",
        marker="o",
        color="#B58863",
        height=5,
        aspect=1.3,
    )
    g.set_axis_labels("Average Game Rating (100-point bins)", "Average Opening Ply")
    g.set(title="Do Stronger Players Follow Opening Theory Longer?")
    g.tick_params(axis="x", labelsize=8)
    st.pyplot(g.figure)
    plt.close(g.figure)

# --- Chart 4: Which openings favor White vs. Black? ---
with row2_col2:
    st.subheader("4. Which Openings Favor White vs. Black?")

    top10 = df["opening_family"].value_counts().head(10).index
    sub = df[df["opening_family"].isin(top10)]

    if sub.empty:
        st.warning("No games in the selected rating range.")
    else:
        edge = (sub.groupby("opening_family")["winner"]
                  .value_counts(normalize=True).unstack(fill_value=0))
        edge["advantage"] = edge.get("white", 0) - edge.get("black", 0)
        edge = edge.sort_values("advantage", ascending=False).reset_index()
        edge["favors"] = edge["advantage"].apply(lambda x: "White" if x > 0 else "Black")

        sns.set_theme(style="whitegrid")
        g = sns.catplot(
            data=edge,
            x="advantage",
            y="opening_family",
            hue="favors",
            kind="bar",
            order=edge["opening_family"],
            palette={"White": "#F0D9B5", "Black": "#5C3A21"},
            edgecolor="black",
            dodge=False,
            height=5,
            aspect=1.0,
        )
        g.refline(x=0, color="black", linewidth=1.5)
        g.set_axis_labels("White Win % − Black Win %", "")
        g.set(title="Which Openings Favor White vs. Black? (10 Most Played)")

        lim = round(edge["advantage"].abs().max() + 0.05, 1)
        ticks = [i / 100 for i in range(int(-lim * 100), int(lim * 100) + 1, 5)]
        g.set(xticks=ticks, xticklabels=[f"{int(t*100):+d}%" for t in ticks])
        g.tick_params(axis="y", labelsize=8)
        st.pyplot(g.figure)
        plt.close(g.figure)

