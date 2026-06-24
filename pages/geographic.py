import dash
import dash_mantine_components as dmc
from dash import callback, Output, Input, dcc, State
from functools import lru_cache
import json
from data_geo import (
    load_data, get_state_rates, get_national_trend, get_state_trend,
    get_summary_stats, get_state_scatter, get_state_ranking, get_previous_stats, 
    get_choropleth_ranges, get_trend_all_populations
)
from plots import plot_choropleth, plot_hypertension_trend, plot_state_scatter, plot_mental_health_trend

dash.register_page(__name__, path="/", title="Geographic Overview")

df = load_data()
YEARS = sorted(df["Year"].unique().tolist())
STATES = sorted(df["State_Name"].dropna().unique().tolist())
CHORO_RANGES = get_choropleth_ranges(df)

with open("assets/data/states.json") as f:
    geojson = json.load(f)

METRICS = [
    {"value": "Hypertension_Rate", "label": "Hypertension"},
    {"value": "Depression_Rate", "label": "Depression"},
    {"value": "Freq_Distress_Rate", "label": "Freq Mental Distress"},
]

layout = dmc.Stack([

    # ---------------- SUMMARY CARDS ----------------
    dcc.Loading(
        dmc.Group(id="summary-cards", grow=True),
    ),
    
    dmc.Space(h=5),
    dmc.Divider(
        label=dmc.Text("Where Is Health Burden The Highest?", size="lg", fw=600),
        size='md'),

    # ---------------- MAP / TABLE RANKING ----------------
    dmc.Stack([

        dmc.Flex(
            justify="space-between",
            align='center',
            children=[
                dmc.Switch(
                    id="show-ranking-toggle",
                    label="Show Ranking",
                    checked=False,
                    size="sm"
                ),
            ]
        ),

        dmc.Grid([
            dmc.GridCol(
                dmc.Paper(
                    dcc.Loading(dcc.Graph(id="geo-choropleth")),
                    p="sm",
                    withBorder=True,
                ),
                id="map-col",
                span=12  
            ),
            dmc.GridCol(
                dmc.Paper(
                    dcc.Loading(
                        dmc.ScrollArea(
                            h=420,
                            type="auto",
                            offsetScrollbars=True,
                            children=dmc.Table(
                                id="geo-table",
                                striped=True,
                                highlightOnHover=True,
                                withTableBorder=False,
                                withColumnBorders=True,
                                style={"backgroundColor": "white"}
                            ),
                        )
                    ),
                    p="sm",
                    withBorder=True,
                ),
                id="table-col",
                span=5,
                style={"display": "none"}  
            ),
        ]),

    ], gap="xs"),
    
    dmc.Space(h=5),
    dmc.Divider(
        label=dmc.Text("How Does This State Compare to the Nation?", size="lg", fw=600),
        size="md"),

    dmc.Tabs(
        value="trend",
        allowTabDeactivation=True,
        variant='outline',
        children=[
            dmc.TabsList(
                [
                    dmc.TabsTab("Trends", value="trend"),
                    dmc.TabsTab("Correlation", value="scatter"),
                ]
            ),
            
            # ---------------- SCATTER ----------------
            dmc.TabsPanel(
                value="scatter",
                children=[
                    dmc.Space(h=10),
                    dmc.Flex(
                        justify="space-between",
                        align="center",
                        gap="sm",
                        children=[
                            dmc.Flex(
                                justify="flex-start",
                                align="center",
                                gap="sm",
                                children=[
                                    dmc.Text("Y-Axis:", fw=500),
                                    dmc.Select(
                                        id="geo-scatter-y",
                                        size="xs",
                                        value="Depression_Rate",
                                        data=[
                                            {"label": "Depression", "value": "Depression_Rate"},
                                            {"label": "Mental Distress", "value": "Freq_Distress_Rate"},
                                        ],
                                        w=150,
                                        allowDeselect=False
                                    ),
                                ],
                            ),
                            dmc.Switch(
                                id="show-quadrants-toggle",
                                label="National Averages",
                                checked=False,
                                size="sm"
                            ),
                        ]
                    ),
                    dmc.Space(h=10),
                    dmc.Paper(
                        dcc.Loading(dcc.Graph(id="geo-scatter")),
                        p="sm",
                        withBorder=True,
                    ),
                    dmc.Text(id="geo-scatter-note", size="sm", c="dimmed", mt=8), 
                ],
            ),
            # ---------------- TREND ----------------
            dmc.TabsPanel(
                value="trend",
                children=[
                    dmc.Paper(
                        dcc.Loading(
                            dcc.Graph(id="geo-trend"),
                        ),
                        p="sm",
                        withBorder=True,
                    )
                ],
            ),
        ]
    )

], gap="md", p="lg")


# ── HELPERS ───────────────────────────────────────────────────────────────────
def fmt(n):
    if n >= 1_000_000: return f"{n / 1_000_000:.1f}M"
    if n >= 1_000: return f"{n / 1_000:.1f}K"
    return f"{n:,.0f}"

def delta(curr, prev, prev_year=None, is_rate=False):
    if prev is None:
        return "", "#7f8c8d"
    diff = curr - prev
    year_label = f'{prev_year}' if prev_year else "previous year"
    if abs(diff) < 0.001:
        return "— No change", "#7f8c8d"
    text = f"{abs(diff):.1f}%" if is_rate else fmt(abs(diff))
    arrow, color = ("▲", "#27ae60") if diff > 0 else ("▼", "#e74c3c")
    return f"{arrow} {text} since {year_label}", color

def card(label, value, delta_text="", delta_color="#7f8c8d", color="#2c3e50"):
    return dmc.Paper([
        dmc.Text(label, size="xs", c="dimmed", mb=4),
        dmc.Text(value, size="xl", fw=700, c=color),
        dmc.Text(delta_text, size="xs", c=delta_color) if delta_text else None,
    ], p="md", radius="md", shadow="xs", style={"textAlign": "center"})

CONDITION_MAP = {
    "Hypertension_Rate": ("Est. Adults w/ Hypertension", "hypertension_est", "hypertension_rate", "#d92a18"),
    "Depression_Rate": ("Est. Adults w/ Depression", "depression_est", "depression_rate", "#3498db"),
    "Freq_Distress_Rate": ("Est. Adults w/ Frequent Mental Distress", "mh_distress_est", "mh_distress_rate", "#e67e22"),
}

# ── CACHE ───────────────────────────────────────────────────────────────────
@lru_cache(maxsize=32)
def get_state_rates_cached(year, bp_status):
    return get_state_rates(df, year, bp_status=bp_status)

@lru_cache(maxsize=64)  
def get_summary_stats_cached(year, state, bp_status):
    return get_summary_stats(df, year, state=state, bp_status=bp_status)

@lru_cache(maxsize=5)
def get_state_scatter_cached(year):
    return get_state_scatter(df, year)


# ── CALLBACKS ─────────────────────────────────────────────────────────────────
@callback(
    Output("summary-cards", "children"),
    Input("global-filters", "data"),
)
def update_summary(filters):
    year = int(filters["year"]) if filters["year"] else None
    state = filters["state"]
    condition = filters["condition"]
    bp_status = filters["compare_to"] or "with_hypertension"

    year_label = str(year) if year else "All Years"

    stats = get_summary_stats_cached(year, state, bp_status)
    prev, prev_year = get_previous_stats(df, year, state=state, bp_status=bp_status)

    cond_label, est_key, rate_key, color = CONDITION_MAP.get(condition, CONDITION_MAP["Hypertension_Rate"])
    label_suffix = f"— {state}" if state else "— National"

    rate_d, rate_c = delta(stats[rate_key], prev[rate_key] if prev else None, prev_year, is_rate=True)
    est_d, est_c   = delta(stats[est_key],  prev[est_key] if prev else None, prev_year)
    pop_d, pop_c   = delta(stats["population_est"], prev["population_est"] if prev else None, prev_year)

    pop_label_map = {
        "all": "Total Adult Population",
        "with_hypertension": "Adults With Hypertension",
        "without_hypertension": "Adults Without Hypertension",
    }
    pop_label = pop_label_map.get(bp_status, "Total Adult Population")

    return [
        card(f"Weighted Prevalence Rate ({year_label})", f"{stats[rate_key]:.1f}%", rate_d, rate_c, color),
        card(cond_label, fmt(stats[est_key]), est_d, est_c, color),
        card(f"Est. {pop_label} {label_suffix} ({year_label})", fmt(stats["population_est"]), pop_d, pop_c, "#2c3e50"),
    ]


@callback(
    Output("geo-choropleth", "figure"),
    Input("global-filters", "data"),
)
def update_map(filters):
    year = int(filters["year"]) if filters["year"] else None
    state = filters["state"]
    metric = filters["condition"]
    bp_status = filters["compare_to"] or "all"

    state_df = get_state_rates_cached(year, bp_status=bp_status)
    return plot_choropleth(state_df, geojson, metric, year, color_range=CHORO_RANGES[metric], state=state)


@callback(
    Output("map-col", "span"),
    Output("table-col", "style"),
    Input("show-ranking-toggle", "checked")
)
def toggle_ranking(show_ranking):
    if show_ranking:
        return 7, {"display": "block"}
    return 12, {"display": "none"}


@callback(
    Output("geo-table", "children"),
    Input("global-filters", "data"),
)
def update_ranking_table(filters):
    year = int(filters["year"]) if filters["year"] else None
    state = filters["state"]
    metric = filters["condition"]
    bp_status = filters["compare_to"] or "all"

    ranking_df = get_state_ranking(df, year, metric, selected_state=state, bp_status=bp_status) \
        .sort_values(metric, ascending=False).reset_index(drop=True)

    header = dmc.TableThead(dmc.TableTr([dmc.TableTh(c) for c in ("Rank", "State", "Rate (%)")]))

    body = dmc.TableTbody([
        dmc.TableTr(
            [dmc.TableTd(i + 1), dmc.TableTd(row["State_Name"]), dmc.TableTd(f"{row[metric]:.2f}%")],
            style={"backgroundColor": "#fff9ab", "fontWeight": "600"} if row["State_Name"] == state else {}
        )
        for i, row in ranking_df.iterrows()
    ])
    return [header, body]


@callback(
    Output("geo-scatter", "figure"),
    Output("geo-scatter-note", "children"),
    Input("global-filters", "data"),
    Input("geo-scatter-y", "value"),
    Input("show-quadrants-toggle", "checked")
)
def update_scatter(filters, y_metric, show_quadrants=False):
    year = int(filters["year"]) if filters["year"] else None
    state = filters["state"]

    scatter_df = get_state_scatter_cached(year)
    fig, note = plot_state_scatter(scatter_df, year, y_metric or "Depression_Rate",
                                    selected_state=state, show_quadrants=show_quadrants)
    return fig, note or ""


@callback(
    Output("geo-trend", "figure"),
    Input("global-filters", "data"),
)
def update_trend(filters):
    state = filters["state"]
    metric = filters["condition"]

    if metric == "Hypertension_Rate":
        # single mode: all adults only, national + optional state
        national_df = get_national_trend(df, bp_status="all")
        state_df = get_state_trend(df, state, bp_status="all") if state else None
        return plot_hypertension_trend(national_df, state_df=state_df, state=state)
    else:
        # split mode: all three populations always shown
        national_df = get_trend_all_populations(df, state=None)
        state_df = get_trend_all_populations(df, state=state) if state else None
        return plot_mental_health_trend(
            national_df, state_df=state_df, state=state, metric=metric
        )