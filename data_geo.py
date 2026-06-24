import pandas as pd
from mapping import STATE_REGION_MAP

def load_data(path="assets/data/BRFSS.parquet"):
    cols = [
        "Year", "State_Name", "LLCPWT",
        "High_BP", "Depression", "Mental_Hlth",
        "Race", "Age", "Sex", 
        #"Income", "Employ", "Health_Insurance", "Med_Cost"
    ]
    df = pd.read_parquet(path, columns=cols)

    df["Year"] = df["Year"].astype("int16")
    df["Mental_Hlth"] = df["Mental_Hlth"].astype("int8")
    df["LLCPWT"] = df["LLCPWT"].astype("float32")

    for col in ["State_Name", "High_BP", "Depression", "Race", "Age", "Sex"]:
        if col in df.columns:
            df[col] = df[col].astype("category")
    
    return df

# ── shared helpers ────────────────────────────────────────────────────────────

def _filter(df, year, state=None) -> pd.DataFrame:
    """Filter by year and optionally by state."""
    filtered = df if year is None else df[df["Year"] == year]
    if state:
        filtered = filtered[filtered["State_Name"] == state]
    return filtered


def _weighted_rate(g, mask) -> float:
    """Calculate the condition's (weighted) prevalence rate."""
    total = g["LLCPWT"].sum()
    return (
        g.loc[mask, "LLCPWT"].sum() / total * 100
    )


def _weighted_est(g, mask) -> float:
    """Calculate the condition's (weighted) estimated count."""
    return g.loc[mask, "LLCPWT"].sum()


def _condition_group(row):
    """Label each row by hypertension + depression status."""
    has_bp  = row["High_BP"]    == "Yes"
    has_dep = row["Depression"] == "Yes"
    if has_bp and has_dep:  return "Both"
    elif has_bp:            return "Hypertension Only"
    elif has_dep:           return "Depression Only"
    else:                   return "Neither"

def _apply_bp_filter(filtered, bp_status):
    if bp_status == "with_hypertension":
        return filtered[filtered['High_BP'] == 'Yes']
    elif bp_status == "without_hypertension":
        return filtered[filtered['High_BP'] == 'No']
    return filtered  # "all" / national — no filter


# ── summary stats (cards) ─────────────────────────────────────────────────────
def get_summary_stats(df, year, state=None, bp_status="with_hypertension"):
    """Summary card stats — national or state level, optionally filtered by hypertension status."""
    filtered = _filter(df, year, state)
    filtered = _apply_bp_filter(filtered, bp_status)
    pop_est = filtered["LLCPWT"].sum()

    return {
        "hypertension_est": round(
            _weighted_est(filtered, filtered['High_BP'] == 'Yes'), 1
        ),
        "hypertension_rate": round(
            _weighted_rate(filtered, filtered['High_BP'] == 'Yes'), 1
        ),
        "depression_est": round(
            _weighted_est(filtered, filtered['Depression'] == 'Yes'), 1
        ),
        "depression_rate": round(
            _weighted_rate(filtered, filtered['Depression'] == 'Yes'), 1
        ),
        "bp_depress_est": round(
            _weighted_est(filtered, (
                filtered['High_BP'] == 'Yes') & (filtered['Depression'] == 'Yes')), 1
        ),
        "bp_depress_rate": round(
            _weighted_rate(filtered, (
                filtered['High_BP'] == 'Yes') & (filtered['Depression'] == 'Yes')), 1
        ),
        "bp_distress_est": round(
            _weighted_est(filtered, (
                filtered['High_BP'] == 'Yes') & (filtered['Mental_Hlth'] >= 14)), 1
        ),
        "bp_distress_rate": round(
            _weighted_rate(filtered, (
                filtered['High_BP'] == 'Yes') & (filtered['Mental_Hlth'] >= 14)), 1
        ),
        "mh_distress_est": round(
            _weighted_est(filtered, filtered['Mental_Hlth'] >= 14), 1
        ),
        "mh_distress_rate": round(
            _weighted_rate(filtered, filtered['Mental_Hlth'] >= 14), 1
        ),
        "population_est": round(
            pop_est, 1
        ),
        "label": state if state else "National"
    }

def get_previous_stats(df, year, state=None, bp_status="with_hypertension"):
    if year is None:
        return None, None
    
    years = sorted(df["Year"].unique())
    if year not in years:
        return None, None

    idx = years.index(year)
    if idx == 0:
        return None, None

    for prev_year in reversed(years[:idx]):
        if state:
            available_states = df[df["Year"] == prev_year]["State_Name"].dropna().unique()
            if state not in available_states:
                continue
        return get_summary_stats(df, prev_year, state=state, bp_status=bp_status), prev_year

    return None, None

def get_states_for_year(df, year):
    return sorted(df[df["Year"] == year]["State_Name"].dropna().unique().tolist())

# ── GEOGRAPHIC ────────────────────────────────────────────────────────────────

def get_choropleth_ranges(df):
    """
    Precompute global min/max per metric across the default (with hypertension)
    population and both comparison options, so the choropleth color scale stays consistent.
    """
    metrics = {
        "Hypertension_Rate": ("High_BP", None),
        "Depression_Rate":   ("Depression", None),
        "Freq_Distress_Rate": ("Mental_Hlth", 14),
    }
    bp_statuses = ["with_hypertension", "all", "without_hypertension"]
    years = df["Year"].unique()

    ranges = {}
    for metric, (col, threshold) in metrics.items():
        vmin, vmax = 100, 0
        for bp in bp_statuses:
            if metric == "Hypertension_Rate" and bp != "all":
                continue

            filtered = _apply_bp_filter(df, bp)
            for year in years:
                year_df = filtered[filtered["Year"] == year]
                rates = (
                    year_df.groupby("State_Name")
                    .apply(lambda g: (
                        g.loc[g[col] >= threshold, "LLCPWT"].sum() / g["LLCPWT"].sum() * 100
                        if threshold is not None else
                        g.loc[g[col] == "Yes", "LLCPWT"].sum() / g["LLCPWT"].sum() * 100
                    ))
                )
                if not rates.empty:
                    vmin = min(vmin, rates.min())
                    vmax = max(vmax, rates.max())

        ranges[metric] = (round(vmin / 5) * 5, round(vmax / 5) * 5)
    return ranges

def get_state_rates(df, year, bp_status="with_hypertension"):
    """
    Weighted hypertension, depression, comorbidity rates +
    avg poor MH days by state — drives choropleth maps.
    """
    filtered = _apply_bp_filter(df if year is None else df[df["Year"] == year], bp_status)

    return (
        filtered.groupby("State_Name")
        .apply(lambda g: pd.Series({
            "Hypertension_Rate": round(_weighted_rate(g, g['High_BP'] == 'Yes'), 2),
            "Depression_Rate": round(_weighted_rate(g, g['Depression'] == 'Yes'), 2),
            "Freq_Distress_Rate": round(_weighted_rate(g, g['Mental_Hlth'] >= 14), 2),
            # "BP_Depress_Rate": round((
            #     _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes'))
            # ), 2),
            # "BP_Distress_Rate": round((
            #     _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14))
            # ), 2)
            #"Avg_Poor_MH_Days":  _weighted_avg(g, "Mental_Hlth"),
            #"Total_Respondents": len(g)
        }))
        .reset_index()
    )

def get_state_ranking(df, year, metric, selected_state=None, bp_status="with_hypertension"):
    """
    Full yearly ranking of all states.
    Will highlight selected state but does NOT filter dataset.
    """
    state_df = get_state_rates(df, year, bp_status=bp_status) \
        .sort_values(metric, ascending=False).reset_index(drop=True)

    state_df["Rank"] = state_df.index + 1

    state_df[metric] = state_df[metric].round(2)
    state_df["is_selected"] = state_df["State_Name"] == selected_state

    return state_df[["Rank", "State_Name", metric, "is_selected"]]


def get_national_trend(df, bp_status="all"):
    """
    Weighted national rates across all years.
    """
    filtered = _apply_bp_filter(df, bp_status)

    return (
        filtered.groupby("Year")
        .apply(lambda g: pd.Series({
            "Hypertension_Rate": round(_weighted_rate(g, g['High_BP'] == 'Yes'), 2),
            "Depression_Rate": round(_weighted_rate(g, g['Depression'] == 'Yes'), 2),
            "Freq_Distress_Rate": round(_weighted_rate(g, g['Mental_Hlth'] >= 14), 2),
            "BP_Depress_Rate": round((
                _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes'))
            ), 2),
            "BP_Distress_Rate": round((
                _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14))
            ), 2),
        }))
        .reset_index()
    )

def get_trend_all_populations(df, state=None):
    """
    Returns trend data for all three population groups in one dataframe,
    with a 'Population' column identifying each group.
    Used for the Depression / Freq Distress trend chart where all three
    lines are always shown simultaneously.
    """
    groups = [
        ("all", "All Adults"),
        ("with_hypertension", "With Hypertension"),
        ("without_hypertension", "Without Hypertension"),
    ]

    frames = []
    for bp_status, label in groups:
        filtered = _apply_bp_filter(df, bp_status)
        if state:
            filtered = filtered[filtered["State_Name"] == state]

        result = (
            filtered.groupby("Year")
            .apply(lambda g: pd.Series({
                "Depression_Rate": round(_weighted_rate(g, g['Depression'] == 'Yes'), 2),
                "Freq_Distress_Rate": round(_weighted_rate(g, g['Mental_Hlth'] >= 14), 2),
            }))
            .reset_index()
        )
        result["Population"] = label
        frames.append(result)

    return pd.concat(frames, ignore_index=True)

def get_state_trend(df, state, bp_status="with_hypertension"):
    filtered = _apply_bp_filter(df[df["State_Name"] == state], bp_status)

    return(
        filtered.groupby('Year')
        .apply(lambda g: pd.Series({
            "Hypertension_Rate": round(_weighted_rate(g, g['High_BP'] == 'Yes'), 2),
            "Depression_Rate": round(_weighted_rate(g, g['Depression'] == 'Yes'), 2),
            "Freq_Distress_Rate": round(_weighted_rate(g, g['Mental_Hlth'] >= 14), 2),
            "BP_Depress_Rate": round((
                _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes'))
            ), 2),
            "BP_Distress_Rate": round((
                _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14))
            ), 2)
        }))
        .reset_index()
    )


def get_state_scatter(df, year, bp_status="all"):
    """
    State-level hypertension rate vs poor mental health rate.
    """
    filtered = _apply_bp_filter(df if year is None else df[df["Year"] == year], bp_status)

    result = (
        filtered.groupby("State_Name")
        .apply(lambda g: pd.Series({
            "Hypertension_Rate": round(_weighted_rate(g, g['High_BP'] == 'Yes'), 2),
            "Depression_Rate": round(_weighted_rate(g, g['Depression'] == 'Yes'), 2),
            "Freq_Distress_Rate": round(_weighted_rate(g, g['Mental_Hlth'] >= 14), 2),
            "Total_Respondents": round(g["LLCPWT"].sum(), 1),
            "Region": STATE_REGION_MAP.get(g.name, "U.S. Territory"),
        }))
        .reset_index()
    )

    return result