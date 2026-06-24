import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

YEARS = [2015, 2017, 2019, 2021, 2023]

TREND_COLORS = {
    "Hypertension_Rate": "#e74c3c",
    "Depression_Rate": "#3498db",
    "Freq_Distress_Rate": "#e67e22",
}

TREND_LABELS = {
    "Hypertension_Rate": "Hypertension",
    "Depression_Rate": "Depression",
    "Freq_Distress_Rate": "Frequent Mental Distress",
}

BG = "rgba(0,0,0,0)"

pio.templates["custom"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Outfit, sans-serif", size=12, color="#2c2c2a"),
        title=dict(font=dict(family="Outfit, sans-serif", size=18, color="#1a1a1a", weight=600)),

        xaxis=dict(showgrid=False, zeroline=False, showline=True,
            linecolor="#d9d9d4", ticks="outside",tickcolor="#d9d9d4", title=dict(standoff=25)
        ),
        yaxis=dict(showgrid=True, gridcolor="#ececec", gridwidth=1,
                   zeroline=False, showline=False, title=dict(standoff=10)
        ),

        legend=dict(font=dict(size=11), bgcolor=BG, bordercolor=BG),

        hoverlabel=dict(
            font=dict(family="Outfit, sans-serif", size=12, color="#ffffff"),
            bgcolor="#4f433f", bordercolor="#d9d9d4",
        ),

        margin=dict(t=60, r=20, b=40, l=50),
    )
)
pio.templates.default = "custom"

# ── GEOGRAPHIC ────────────────────────────────────────────────────────────────
# ── CHOROPLETH MAP ────────────────────────────────────────────────────────────
def plot_choropleth(state_df, geojson, metric, year, color_range, state=None):
    METRIC_LABELS = {
        "Hypertension_Rate": "Hypertension Rate (%)",
        "Depression_Rate":   "Depression Rate (%)",
        "BP_Depress_Rate":     "Hypertension & Depression Rate (%)",
        "Freq_Distress_Rate": "Frequent Mental Distress Rate (%)",
        "BP_Distress_Rate": "Hypetension & Mental Distress Rate (%)"
    }
    METRIC_SCALES = {
        "Hypertension_Rate": "Reds",
        "Depression_Rate":   "Blues",
        "BP_Depress_Rate":     "Purples",
        "BP_Distress_Rate": "Redor",
        "Freq_Distress_Rate": "Oranges"
    }

    label = METRIC_LABELS[metric]
    scale = METRIC_SCALES[metric]
    plot_df = state_df.copy()

    year_label = str(year) if year else "All Years"

    fig = px.choropleth(
        plot_df,
        geojson=geojson,
        locations="State_Name",
        featureidkey="properties.NAME",
        color=metric,
        color_continuous_scale=scale,
        range_color=color_range,
        labels={metric: label},
        custom_data=["State_Name"],
        title=f"{label} — {state if state else ''} ({year_label})"
    )

    # ── default marker styling ─────────────────────────────────────────────
    fig.update_traces(
        marker_line_width=0.5,
        marker_line_color="white",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            f"{label}: %{{z:.1f}}%<extra></extra>"
        )
    )

    # ── overlay thick outline on selected state ────────────────────────────
    if state and state in plot_df["State_Name"].values:
        selected_df = plot_df[plot_df["State_Name"] == state]

        fig.add_trace(
            go.Choropleth(
                geojson=geojson,
                locations=selected_df["State_Name"],
                featureidkey="properties.NAME",
                z=selected_df[metric],           
                colorscale=scale,
                zmin=color_range[0], 
                zmax=color_range[1],
                showscale=False,               
                marker_line_width=2,         
                marker_line_color="black",   
                hovertemplate=(
                    f"<b>{state}</b><br>"
                    f"{label}: %{{z:.1f}}%<extra></extra>"
                )
            )
        )

    fig.update_geos(
        scope="usa",
        visible=True,
        showland=True,
        landcolor="#f7f7f7",
        showlakes=False,
        showframe=False,
        framecolor=BG,
        bgcolor=BG
    )
    fig.update_layout(
        geo=dict(
            bgcolor=BG,
            lakecolor=BG,
            landcolor="#f7f7f7",
            subunitcolor="white",
            framecolor=BG,
            framewidth=0,
        ),
        height=420,
        coloraxis_colorbar=dict(
            title=dict(text=""),
            outlinewidth=0, 
            outlinecolor="rgba(0,0,0,0)", 
        ),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        paper_bgcolor=BG,
    )

    return fig


ALL_METRICS = ["Hypertension_Rate", "Depression_Rate", "Freq_Distress_Rate"]

# ── HYPERTENSION TREND (all adults only, single/state pair) ──────────────────
def plot_hypertension_trend(national_df, state_df=None, state=None):
    """
    Simple two-line chart for hypertension rate — national (all adults),
    plus state (all adults) if a state is selected.
    Not split by population filter since that would make the rate trivial.
    """
    fig = go.Figure()
    color = TREND_COLORS["Hypertension_Rate"]

    fig.add_trace(go.Scatter(
        x=national_df["Year"],
        y=national_df["Hypertension_Rate"],
        name="National — All Adults",
        mode="lines+markers",
        line=dict(color=color, width=2.5, dash="dash" if state else "solid"),
        marker=dict(size=6),
        opacity=0.4 if state else 1.0,
    ))

    if state and state_df is not None:
        fig.add_trace(go.Scatter(
            x=state_df["Year"],
            y=state_df["Hypertension_Rate"],
            name=f"{state} — All Adults",
            mode="lines+markers",
            line=dict(color=color, width=3.5),
            marker=dict(size=8, symbol="diamond"),
            opacity=1.0,
        ))

    fig.update_layout(
        title=f"Hypertension Rate — National Average" if not state
              else f"Hypertension Rate — National vs {state}",
        xaxis=dict(tickvals=YEARS, title="Year"),
        yaxis=dict(title="Rate (%)"),
        height=460,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        legend=dict(orientation="h", yanchor="top", y=-0.2,
                    xanchor="center", x=0.5, font=dict(size=10)),
        margin={"t": 50, "b": 30, "l": 60, "r": 10},
        hovermode="x unified"
    )
    return fig

# ── MENTAL HEALTH TREND (all three populations, always shown) ─────────────────
POP_COLORS = {
    "All Adults": "#5c5c5c",
    "With Hypertension": "#e74c3c",
    "Without Hypertension": "#3498db",
}
POP_DASH = {
    "All Adults": "dash",
    "With Hypertension": "solid",
    "Without Hypertension": "solid",
}

def plot_mental_health_trend(national_df, state_df=None, state=None, metric="Depression_Rate"):
    """
    Three-line chart for Depression or Freq Distress — always shows All Adults,
    With Hypertension, and Without Hypertension simultaneously so the viewer
    can immediately see which group has the highest burden.
    If a state is selected, adds three more lines for that state (lighter/thinner).
    """
    fig = go.Figure()
    populations = ["All Adults", "With Hypertension", "Without Hypertension"]

    for pop in populations:
        color = POP_COLORS[pop]
        dash  = POP_DASH[pop]
        d = national_df[national_df["Population"] == pop]

        fig.add_trace(go.Scatter(
            x=d["Year"],
            y=d[metric],
            name=f"National — {pop}",
            mode="lines+markers",
            line=dict(color=color, width=2.5, dash=dash),
            marker=dict(size=6),
            opacity=0.55 if state else 1.0,
            legendgroup=pop,
            hovertemplate=(
                f"<b>National — {pop}</b><br>"
                f"{TREND_LABELS[metric]}: %{{y:.1f}}%<extra></extra>"
            )
        ))

    if state and state_df is not None:
        for pop in populations:
            color = POP_COLORS[pop]
            dash  = POP_DASH[pop]
            d = state_df[state_df["Population"] == pop]

            fig.add_trace(go.Scatter(
                x=d["Year"],
                y=d[metric],
                name=f"{state} — {pop}",
                mode="lines+markers",
                line=dict(color=color, width=3.5, dash=dash),
                marker=dict(size=8, symbol="diamond"),
                opacity=1.0,
                legendgroup=pop,
                hovertemplate=(
                    f"<b>{state} — {pop}</b><br>"
                    f"{TREND_LABELS[metric]}: %{{y:.1f}}%<extra></extra>"
                )
            ))

    title = (
        f"{TREND_LABELS[metric]} Rate — Adults With vs. Without Hypertension"
        if not state else
        f"{TREND_LABELS[metric]} Rate — National vs {state} (All Populations)"
    )

    subtitle = (
        f"The weighted prevalence of adults diagnosed with a depressive disorder."
        if not metric == "Freq_Distress_Rate" else
        "The weighted prevalence of adults who experience 14 or more days of poor mental health per month."
    )

    fig.update_layout(
        title=title,
        title_subtitle_text=subtitle if not state else "",
        xaxis=dict(tickvals=YEARS, title="Year"),
        yaxis=dict(title="Rate (%)"),
        height=460,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        legend=dict(orientation="h", yanchor="top", y=-0.25,
                    xanchor="center", x=0.5, font=dict(size=10)),
        margin={"t": 50, "b": 30, "l": 60, "r": 10},
        hovermode="x unified"
    )
    return fig


# ── SCATTER PLOT ─────────────────────────────────────────────────────────────
def plot_state_scatter(df, year, y_metric, selected_state=None, show_quadrants=False):
    labels = {
        "Depression_Rate": "Depression",
        "Freq_Distress_Rate": "Freq Mental Distress",
    }
    y_metric = y_metric or "Depression_Rate"
    df = df.copy()
    nat_x = df["Hypertension_Rate"].mean()
    nat_y = df[y_metric].mean()
    x_min, x_max = df["Hypertension_Rate"].min(), df["Hypertension_Rate"].max()
    y_min, y_max = df[y_metric].min(), df[y_metric].max()
    custom_colors = {'Southeast': '#207faf', 'West': '#7994c4', 'Southwest': '#b1acd4',
        'Northeast': '#da9ac3', 'U.S. Territory': '#db668d', 'Midwest': '#ce2e47'}

    fig = px.scatter(
        df, x="Hypertension_Rate", y=y_metric,
        hover_name="State_Name", color="Region",
        color_discrete_map=custom_colors,
        size="Total_Respondents", size_max=30,
        custom_data=['State_Name', 'Region']
    )
    fig.update_traces(opacity=0.8, marker=dict(sizemin=4, line=dict(width=0)),
                      hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]})<br>" 
                      f"Hypertension: %{{x:.2f}}%<br>{labels[y_metric]}: %{{y:.2f}}<extra></extra>")

    if selected_state:
        selected = df[df["State_Name"] == selected_state]
        max_resp = df["Total_Respondents"].max()
        size_val = (selected["Total_Respondents"].iloc[0] / max_resp) * 35 + 8
        fig.add_scatter(
            x=selected["Hypertension_Rate"], y=selected[y_metric],
            mode="markers", name="Selected State",
            text=selected["State_Name"],
            hovertemplate=f"<b>%{{text}}</b><br>Hypertension: %{{x:.2f}}%<br>{labels[y_metric]}: %{{y:.2f}}<extra></extra>",
            marker=dict(size=size_val, color="rgba(0,0,0,0)", line=dict(width=3, color="black")),
        )

    quadrant_note = None  

    if show_quadrants:
        fig.add_trace(go.Scatter(
            x=[x_min, x_max], y=[nat_y, nat_y],
            mode="lines", line=dict(dash="dot", color="black", width=1.5),
            opacity=0.7, showlegend=False,
            hovertemplate=f"National {labels[y_metric]} Average: {nat_y:.1f}%<extra></extra>"
        ))
        fig.add_trace(go.Scatter(
            x=[nat_x, nat_x], y=[y_min, y_max],
            mode="lines", line=dict(dash="dot", color="black", width=1.5),
            opacity=0.7, showlegend=False,
            hovertemplate=f"National Hypertension Average: {nat_x:.1f}%<extra></extra>"
        ))
        fig.add_annotation(x=x_min, y=nat_y, text=f"{labels[y_metric]}: {nat_y:.1f}%",
                            showarrow=False, xanchor="left", yanchor="bottom", font=dict(size=11, color="#262626"))
        fig.add_annotation(x=nat_x, y=y_max, text=f"Hypertension: {nat_x:.1f}%",
                            showarrow=False, xanchor="right", yanchor="top", font=dict(size=11, color="#262626"))

        y_label = labels[y_metric]
        quadrant_note = (
            f"TOP LEFT — Below National Average Hypertension, Above National Average {y_label}  •  "
            f"TOP RIGHT — Above National Average for Hypertension and {y_label}  •  "
            f"BOTTOM LEFT — Below National Average for Both  •  "
            f"BOTTOM RIGHT — Above National Average Hypertension, Below National Average {y_label}"
        )

    year_label = str(year) if year else "All Years"

    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5, font=dict(size=11)),
        xaxis_title="Hypertension Rate (%)",
        yaxis_title=f'{labels[y_metric]} Rate (%)',
        title=f"Hypertension vs {labels[y_metric]} Rate (%) — {year_label}",
        height=460, paper_bgcolor=BG, plot_bgcolor=BG,
    )

    return fig, quadrant_note

# ── DEMOGRAPHICS ────────────────────────────────────────────────────────────────
gender_colors={"Male": "#6088d1", "Female":"#e68398"}

rate_to_est = {
    "Hypertension_Rate": "Hypertension_Est",
    "Depression_Rate": "Depression_Est",
    "Freq_Distress_Rate": "Freq_Distress_Est",
}

NEUTRAL_GRAY = "#6e6e6e"

# ── BAR CHARTS ────────────────────────––─────────────────────────────────────────
def plot_by_age(df, condition, by_gender=False):
    title_suffix=" (Colored by Gender)" if by_gender else ""
    est_col=rate_to_est[condition]
    custom_order=["18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54",
                  "55-59", "60-64", "65-69", "70-74", "75-79", "80+"]

    fig = px.bar(
        df,
        x="Age",
        y=condition,
        color="Sex" if by_gender else None,
        barmode="group" if by_gender else None,
        title=f"{TREND_LABELS[condition]} by Age{title_suffix}",
        labels={condition: f"{TREND_LABELS[condition]} Rate (%)", "Race": ""},
        category_orders={"Age": custom_order},
        color_discrete_map=gender_colors if by_gender else None,
        color_discrete_sequence=None if by_gender else [NEUTRAL_GRAY],
        custom_data=[est_col, "Population_Est"],
        text=df[condition].round(1).astype(str) + "%",
        template="custom"
    )

    hover = (
        f"<b>%{{x}}</b><br>"
        f"{TREND_LABELS[condition]} Rate: %{{y:.1f}}%<br>"
        "Est. Count: %{customdata[0]:,.0f}<br>"
        "Est. Population: %{customdata[1]:,.0f}"
        "<extra></extra>"
    )

    fig.update_traces(
        hovertemplate=hover,
        textposition="inside",
        textfont=dict(size=11, color="white"),
        insidetextanchor="end",
    )
    fig.update_layout(height=480, paper_bgcolor=BG, plot_bgcolor=BG)
    return fig


def plot_by_gender(df, condition):
    est_col=rate_to_est[condition]
    custom_order=["Male", "Female"]

    fig = px.bar(
        df,
        x="Sex",
        y=condition,
        color="Sex",
        title=f"{TREND_LABELS[condition]} by Gender",
        labels={condition: f"{TREND_LABELS[condition]} Rate (%)", "Gender": ""},
        category_orders={"Sex": custom_order},
        color_discrete_map=gender_colors,
        custom_data=[est_col, "Population_Est"],
        text=df[condition].round(1).astype(str) + "%",
        template="custom"
    )

    hover = (
        f"<b>%{{x}}</b><br>"
        f"{TREND_LABELS[condition]} Rate: %{{y:.1f}}%<br>"
        "Est. Count: %{customdata[0]:,.0f}<br>"
        "Est. Population: %{customdata[1]:,.0f}"
        "<extra></extra>"
    )

    fig.update_traces(
        hovertemplate=hover,
        textposition="inside",
        textfont=dict(size=11, color="white"),
        insidetextanchor="end",
    )
    fig.update_layout(height=480, paper_bgcolor=BG, plot_bgcolor=BG)
    return fig


def plot_by_race(df, condition, by_gender=False):
    title_suffix=" (Colored by Gender)" if by_gender else ""
    est_col=rate_to_est[condition]
    custom_order=["White", "Hispanic", "Black", "Asian", "AI/AN", "NH/PI", "Multiracial", "Other"]

    fig = px.bar(
        df,
        x="Race",
        y=condition,
        color="Sex" if by_gender else None,
        barmode="group" if by_gender else None,
        title=f"{TREND_LABELS[condition]} Rate by Race{title_suffix}",
        labels={condition: f"{TREND_LABELS[condition]} Rate (%)", "Race": ""},
        category_orders={"Race": custom_order},
        color_discrete_map=gender_colors if by_gender else None,
        color_discrete_sequence=None if by_gender else [NEUTRAL_GRAY],
        custom_data=[est_col, "Population_Est"],
        text=df[condition].round(1).astype(str) + "%",
        template="custom"
    )

    hover = (
        f"<b>%{{x}}</b><br>"
        f"{TREND_LABELS[condition]} Rate: %{{y:.1f}}%<br>"
        "Est. Count: %{customdata[0]:,.0f}<br>"
        "Est. Population: %{customdata[1]:,.0f}"
        "<extra></extra>"
    )

    fig.update_traces(
        hovertemplate=hover,
        textposition="inside",
        textfont=dict(size=11, color="white"),
        insidetextanchor="end",
    )
    fig.update_layout(height=480, paper_bgcolor=BG, plot_bgcolor=BG)
    return fig

# ── TREND CHARTS ─────────────────────────────────────────────────────────────────
def plot_trend_age(df, condition):
    est_col=rate_to_est[condition]
    
    fig = px.line(
        df,
        x="Year",
        y=condition,
        color="Age",
        title=f"{TREND_LABELS[condition]} Trend by Age",
        custom_data=["Age", est_col, "Population_Est"],
        template="custom"
    )

    default_visible = {"18-24", "40-44", "65-69", "80+"}

    for trace in fig.data:
        if trace.name not in default_visible:
            trace.visible = "legendonly"

    hover = (
        "<b>%{customdata[0]}</b><br>"
        f"{TREND_LABELS[condition]} Rate: %{{y:.1f}}%<br>"
        "Est. Count: %{customdata[1]:,.0f}<br>"
        "Est. Population: %{customdata[2]:,.0f}"
        "<extra></extra>"
    )
        
    fig.update_traces(hovertemplate=hover, mode="lines+markers", marker=dict(size=6))
    fig.update_layout(height=480, xaxis=dict(tickvals=YEARS, title="Year"),
                      paper_bgcolor=BG, plot_bgcolor=BG)
    return fig


def plot_trend_gender(df, condition):
    est_col=rate_to_est[condition]
    
    fig = px.line(
        df,
        x="Year",
        y=condition,
        color="Sex",
        title=f"{TREND_LABELS[condition]} Trend by Gender",
        custom_data=["Sex", est_col, "Population_Est"],
        template="custom"
    )

    hover = (
        "<b>%{customdata[0]}</b><br>"
        f"{TREND_LABELS[condition]} Rate: %{{y:.1f}}%<br>"
        "Est. Count: %{customdata[1]:,.0f}<br>"
        "Est. Population: %{customdata[2]:,.0f}"
        "<extra></extra>"
    )
        
    fig.update_traces(hovertemplate=hover, mode="lines+markers", marker=dict(size=6))
    fig.update_layout(height=480, xaxis=dict(tickvals=YEARS, title="Year"),
                      paper_bgcolor=BG, plot_bgcolor=BG)
    return fig


def plot_trend_race(df, condition):
    est_col=rate_to_est[condition]
    
    fig = px.line(
        df,
        x="Year",
        y=condition,
        color="Race",
        title=f"{TREND_LABELS[condition]} Trend by Race",
        custom_data=["Race", est_col, "Population_Est"],
        template="custom"
    )

    hover = (
        "<b>%{customdata[0]}</b><br>"
        f"{TREND_LABELS[condition]} Rate: %{{y:.1f}}%<br>"
        "Est. Count: %{customdata[1]:,.0f}<br>"
        "Est. Population: %{customdata[2]:,.0f}"
        "<extra></extra>"
    )
        
    fig.update_traces(hovertemplate=hover, mode="lines+markers", marker=dict(size=6))
    fig.update_layout(height=480, xaxis=dict(tickvals=YEARS, title="Year"),
                      paper_bgcolor=BG, plot_bgcolor=BG)
    return fig