import pandas as pd

def load_data(path="assets/data/BRFSS.parquet"):
    cols = [
        "Year", "State_Name", "LLCPWT",
        "High_BP", "Depression", "Mental_Hlth",
        "Race", "Age", "Sex", "Income",
        "Employ", "Health_Insurance", "Med_Cost"
    ]
    df = pd.read_parquet(path, columns=cols)

    df["Year"] = df["Year"].astype("int16")
    df["Mental_Hlth"] = df["Mental_Hlth"].astype("int8")
    df["LLCPWT"] = df["LLCPWT"].astype("float32")

    for col in ["State_Name", "High_BP", "Depression", "Race", "Age", "Sex",
                "Income", "Employ", "Health_Insurance", "Med_Cost"]:
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


def _apply_bp_filter(filtered, bp_status):
    if bp_status == "with_hypertension":
        return filtered[filtered['High_BP'] == 'Yes']
    elif bp_status == "without_hypertension":
        return filtered[filtered['High_BP'] == 'No']
    return filtered  # all (no filter)

def get_states_for_year(df, year):
    return sorted(df[df["Year"] == year]["State_Name"].dropna().unique().tolist())

# ── DEMOGRAPHIC ────────────────────────────────────────────────────────────────
# def get_yaxis_ranges(df):
#     conditions = {
#         "Hypertension_Rate": ("High_BP", None),
#         "Depression_Rate":   ("Depression", None),
#         "Freq_Distress_Rate": ("Mental_Hlth", 14),
#     }
#     bp_statuses = ["all", "with_hypertension", "without_hypertension"]
#     all_groupings = [["Age"], ["Race"], ["Sex"], ["Age", "Sex"], ["Race", "Sex"]]

#     def compute_max(filtered_df, cond, col, threshold):
#         max_val = 0
#         for bp in bp_statuses:
#             if cond == "Hypertension_Rate" and bp != "all":
#                 continue
#             filtered = _apply_bp_filter(filtered_df, bp)
#             for grp_cols in all_groupings:
#                 rates = (
#                     filtered.groupby(grp_cols)
#                     .apply(lambda g: (
#                         g.loc[g[col] >= threshold, "LLCPWT"].sum() / g["LLCPWT"].sum() * 100
#                         if threshold is not None else
#                         g.loc[g[col] == "Yes", "LLCPWT"].sum() / g["LLCPWT"].sum() * 100
#                     ))
#                 )
#                 local_max = rates.max()
#                 if local_max > max_val:
#                     max_val = local_max
#         return max_val

#     national_ranges = {}
#     state_ranges = {}  # state_ranges[state][cond] = y_max

#     for cond, (col, threshold) in conditions.items():
#         max_val = compute_max(df, cond, col, threshold)
#         national_ranges[cond] = round(max_val / 5 + 1) * 5

#     for state in df["State_Name"].dropna().unique():
#         state_df = df[df["State_Name"] == state]
#         state_ranges[state] = {}
#         for cond, (col, threshold) in conditions.items():
#             max_val = compute_max(state_df, cond, col, threshold)
#             state_ranges[state][cond] = round(max_val / 5 + 1) * 5

#     return national_ranges, state_ranges


# ── SUMMARY CARDS ──────────────────────────────────────────────────────────────
def get_highest_prevalence_group(df, year, condition_col, demographic_col, state=None, threshold=None, 
                                 bp_status="all"):
    df = df if year is None else df[df["Year"] == year]
    filtered = _apply_bp_filter(df, bp_status)

    if state:
        filtered = filtered[filtered['State_Name'] == state]

    rates = (
        filtered.groupby(demographic_col)
        .apply(lambda g: pd.Series({
            "Rate": (
                g.loc[g[condition_col] >= threshold, "LLCPWT"].sum() / g["LLCPWT"].sum() * 100
                if threshold is not None else
                g.loc[g[condition_col] == 'Yes', 'LLCPWT'].sum() / g["LLCPWT"].sum() * 100
            ),
            "Count": (
                g.loc[g[condition_col] >= threshold, "LLCPWT"].sum()
                if threshold is not None else
                g.loc[g[condition_col] == 'Yes', 'LLCPWT'].sum()
            )
        }))
        .reset_index()
        .dropna()
    )

    if rates.empty:
        return None, None

    top = rates.loc[rates['Rate'].idxmax()]
    return top[demographic_col], round(top['Rate'], 1)


# def get_highest_prevalence_comorbid(df, year, demographic_col, comorbid_type, state=None):
#     """
#     comorbid_type: 'bp_depression' or 'bp_distress'
#     """
#     filtered = df[df["Year"] == year].copy()
#     if state:
#         filtered = filtered[filtered["State_Name"] == state]

#     if comorbid_type == "bp_depression":
#         filtered["Comorbid"] = (filtered["High_BP"] == "Yes") & (filtered["Depression"] == "Yes")
#     else:  # bp_mh
#         filtered["Comorbid"] = (filtered["High_BP"] == "Yes") & (filtered["Mental_Hlth"] >= 14)

#     rates = (
#         filtered.groupby(demographic_col)
#         .apply(lambda g: pd.Series({
#             "Rate": g.loc[g["Comorbid"], "LLCPWT"].sum() / g["LLCPWT"].sum() * 100
#         }))
#         .reset_index()
#         .dropna()
#     )

#     if rates.empty:
#         return None, None

#     top = rates.loc[rates["Rate"].idxmax()]
#     return top[demographic_col], round(top["Rate"], 1)


def get_top_group_for_condition(df, year, demographic_col, condition, state=None, bp_status="all"):
    filtered = df.copy()
    filtered = _apply_bp_filter(filtered, bp_status)

    if condition == "Hypertension_Rate":
        return get_highest_prevalence_group(filtered, year, "High_BP", demographic_col, state=state)
    elif condition == "Depression_Rate":
        return get_highest_prevalence_group(filtered, year, "Depression", demographic_col, state=state)
    elif condition == "Freq_Distress_Rate":
        return get_highest_prevalence_group(
            filtered, year, "Mental_Hlth", demographic_col,
            state=state, threshold=14
        )
    # elif condition == "BP_Depress_Rate":
    #     return get_highest_prevalence_comorbid(
    #         df, year, demographic_col,
    #         "bp_depression", state=state
    #     )
    # elif condition == "BP_Distress_Rate":
    #     return get_highest_prevalence_comorbid(
    #         df, year, demographic_col,
    #         "bp_mh", state=state
    #     )
    else:
        raise ValueError(f"Unknown condition: {condition}")


def get_breakdown_by_race(df, year, state=None, by_gender=False, bp_status="with_hypertension"):
    df = df if year is None else df[df["Year"] == year]
    filtered = _apply_bp_filter(df, bp_status)
    if state:
        filtered = filtered[filtered['State_Name'] == state]

    group_cols = ['Race', 'Sex'] if by_gender else ["Race"]

    result = (
        filtered
        .groupby(group_cols)
        .apply(lambda g: pd.Series({
            "Hypertension_Rate": _weighted_rate(g, g['High_BP'] == 'Yes'),
            "Depression_Rate": _weighted_rate(g, g["Depression"] == "Yes"),
            "Freq_Distress_Rate": _weighted_rate(g, g['Mental_Hlth'] >= 14),
            # 'BP_Depress_Rate': _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes')),
            # 'BP_Distress_Rate': _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14)),
            'Hypertension_Est': _weighted_est(g, g['High_BP'] == 'Yes'),
            'Depression_Est': _weighted_est(g, g["Depression"] == "Yes"),
            'Freq_Distress_Est': _weighted_est(g, g['Mental_Hlth'] >= 14),
            # 'BP_Depress_Est': _weighted_est(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes')),
            # 'BP_Distress_Est': _weighted_est(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14)),
            'Population_Est': g['LLCPWT'].sum(),
        }))
        .reset_index()
    )

    return result

def get_breakdown_by_age(df, year, state=None, bp_status="with_hypertension", by_gender=False):
    df = df if year is None else df[df["Year"] == year]
    filtered = _apply_bp_filter(df, bp_status)
    if state:
        filtered = filtered[filtered['State_Name'] == state]

    group_cols = ['Age', 'Sex'] if by_gender else ["Age"]

    result = (
        filtered
        .groupby(group_cols)
        .apply(lambda g: pd.Series({
            "Hypertension_Rate": _weighted_rate(g, g['High_BP'] == 'Yes'),
            "Depression_Rate": _weighted_rate(g, g["Depression"] == "Yes"),
            "Freq_Distress_Rate": _weighted_rate(g, g['Mental_Hlth'] >= 14),
            # 'BP_Depress_Rate': _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes')),
            # 'BP_Distress_Rate': _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14)),
            'Hypertension_Est': _weighted_est(g, g['High_BP'] == 'Yes'),
            'Depression_Est': _weighted_est(g, g["Depression"] == "Yes"),
            'Freq_Distress_Est': _weighted_est(g, g['Mental_Hlth'] >= 14),
            # 'BP_Depress_Est': _weighted_est(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes')),
            # 'BP_Distress_Est': _weighted_est(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14)),
            'Population_Est': g['LLCPWT'].sum(),
        }))
        .reset_index()
    )

    return result

def get_breakdown_by_gender(df, year, state=None, bp_status="with_hypertension"):
    df = df if year is None else df[df["Year"] == year]
    filtered = _apply_bp_filter(df, bp_status)
    if state:
        filtered = filtered[filtered['State_Name'] == state]

    result = (
        filtered
        .groupby("Sex")
        .apply(lambda g: pd.Series({
            "Hypertension_Rate": _weighted_rate(g, g['High_BP'] == 'Yes'),
            "Depression_Rate": _weighted_rate(g, g["Depression"] == "Yes"),
            "Freq_Distress_Rate": _weighted_rate(g, g['Mental_Hlth'] >= 14),
            # 'BP_Depress_Rate': _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes')),
            # 'BP_Distress_Rate': _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14)),
            'Hypertension_Est': _weighted_est(g, g['High_BP'] == 'Yes'),
            'Depression_Est': _weighted_est(g, g["Depression"] == "Yes"),
            'Freq_Distress_Est': _weighted_est(g, g['Mental_Hlth'] >= 14),
            # 'BP_Depress_Est': _weighted_est(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes')),
            # 'BP_Distress_Est': _weighted_est(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14)),
            'Population_Est': g['LLCPWT'].sum(),
        }))
        .reset_index()
    )

    return result

def get_trend_by_age(df, state=None, bp_status="all"):
    filtered = df.copy()
    filtered = _apply_bp_filter(filtered, bp_status)
    if state:
        filtered = filtered[filtered['State_Name'] == state]

    result = (
        filtered
        .groupby(["Year", "Age"])
        .apply(lambda g: pd.Series({
            "Hypertension_Rate": _weighted_rate(g, g['High_BP'] == 'Yes'),
            "Depression_Rate": _weighted_rate(g, g["Depression"] == "Yes"),
            "Freq_Distress_Rate": _weighted_rate(g, g['Mental_Hlth'] >= 14),
            # 'BP_Depress_Rate': _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes')),
            # 'BP_Distress_Rate': _weighted_rate(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14)),
            'Hypertension_Est': _weighted_est(g, g['High_BP'] == 'Yes'),
            'Depression_Est': _weighted_est(g, g["Depression"] == "Yes"),
            'Freq_Distress_Est': _weighted_est(g, g['Mental_Hlth'] >= 14),
            # 'BP_Depress_Est': _weighted_est(g, (g['High_BP'] == 'Yes') & (g['Depression'] == 'Yes')),
            # 'BP_Distress_Est': _weighted_est(g, (g['High_BP'] == 'Yes') & (g['Mental_Hlth'] >= 14)),
            'Population_Est': g['LLCPWT'].sum(),
        }))
        .reset_index()
    )

    return result


def get_trend_by_gender(df, state=None, bp_status="all"):
    filtered = df.copy()
    filtered = _apply_bp_filter(filtered, bp_status)
    if state:
        filtered = filtered[filtered['State_Name'] == state]

    result = (
        filtered
        .groupby(["Year", "Sex"])
        .apply(lambda g: pd.Series({
            "Hypertension_Rate": _weighted_rate(g, g['High_BP'] == 'Yes'),
            "Depression_Rate": _weighted_rate(g, g["Depression"] == "Yes"),
            "Freq_Distress_Rate": _weighted_rate(g, g['Mental_Hlth'] >= 14),
            'Hypertension_Est': _weighted_est(g, g['High_BP'] == 'Yes'),
            'Depression_Est': _weighted_est(g, g["Depression"] == "Yes"),
            'Freq_Distress_Est': _weighted_est(g, g['Mental_Hlth'] >= 14),
            'Population_Est': g['LLCPWT'].sum(),
        }))
        .reset_index()
    )

    return result


def get_trend_by_race(df, state=None, bp_status="all"):
    filtered = df.copy()
    filtered = _apply_bp_filter(filtered, bp_status)
    if state:
        filtered = filtered[filtered['State_Name'] == state]

    result = (
        filtered
        .groupby(["Year", "Race"])
        .apply(lambda g: pd.Series({
            "Hypertension_Rate": _weighted_rate(g, g['High_BP'] == 'Yes'),
            "Depression_Rate": _weighted_rate(g, g["Depression"] == "Yes"),
            "Freq_Distress_Rate": _weighted_rate(g, g['Mental_Hlth'] >= 14),
            'Hypertension_Est': _weighted_est(g, g['High_BP'] == 'Yes'),
            'Depression_Est': _weighted_est(g, g["Depression"] == "Yes"),
            'Freq_Distress_Est': _weighted_est(g, g['Mental_Hlth'] >= 14),
            'Population_Est': g['LLCPWT'].sum(),
        }))
        .reset_index()
    )

    return result