import dash
import dash_mantine_components as dmc
from dash import callback, Output, Input, dcc, State
from functools import lru_cache
from data_demogr import (load_data, get_top_group_for_condition, get_states_for_year, get_breakdown_by_race,
                        get_breakdown_by_age, get_breakdown_by_gender, get_trend_by_age, get_trend_by_gender, 
                        get_trend_by_race)
from plots import plot_by_race, plot_by_age, plot_by_gender, plot_trend_age, plot_trend_gender, plot_trend_race

dash.register_page(__name__, path="/demographics", title="Demographics")

df = load_data()
YEARS = sorted(df["Year"].unique().tolist())
STATES = sorted(df["State_Name"].dropna().unique().tolist())

METRICS = [
    {"value": "Hypertension_Rate", "label": "Hypertension"},
    {"value": "Depression_Rate", "label": "Depression"},
    {"value": "Freq_Distress_Rate", "label": "Freq Mental Distress"},
]

layout = dmc.Stack([

    dcc.Loading(
        dmc.Group(id='demogr-summary-cards', grow=True)
    ),

    dmc.Space(h=5),
    dmc.Divider(size='md'),

    dmc.Tabs(
        value="age",
        variant="outline",
        children=[
            dmc.TabsList(
                [
                    dmc.TabsTab("Age", value="age"),
                    dmc.TabsTab("Gender", value="gender"),
                    dmc.TabsTab("Race", value="race")
                ]
            ),
            # ---- AGE ------------------------------------------------------------
            dmc.TabsPanel(
                value="age",
                children=[
                    dmc.Flex(
                        justify="space-between",
                        align="center",
                        mt="sm", mb="sm",
                        children=[
                            dmc.Switch(
                                id='gender-age-toggle',
                                labelPosition="right",
                                label='Show Gender'
                            ),
                        ]
                    ),
                    # ------------------------- BAR CHART -------------------------
                    dmc.Paper(
                        dcc.Loading(
                            dcc.Graph(id='demogr-age')
                        ),
                        p='sm',
                        withBorder=True,
                    ),
                    dmc.Space(h=25),
                    dmc.Divider(
                        label=dmc.Text("Over the Years", size="lg", fw=600),
                        size='md'),
                    dmc.Space(h=15),
                    
                    # ------------------------- LINE CHART -------------------------
                    dmc.Paper(
                        dcc.Loading(
                            dcc.Graph(id='demogr-age-trend')
                        ),
                        p='sm',
                        withBorder=True
                    ),
                ]
            ),
            # ---- GENDER ---------------------------------------------------------
            dmc.TabsPanel(
                value="gender",
                children=[
                    # ------------------------- BAR CHART -------------------------
                    dmc.Paper(
                        dcc.Loading(
                            dcc.Graph(id='demogr-gender')
                        ),
                        p='sm',
                        withBorder=True,
                    ),
                    dmc.Space(h=25),
                    dmc.Divider(
                        label=dmc.Text("Over the Years", size="lg", fw=600),
                        size='md'),
                    dmc.Space(h=15),
                    
                    # ------------------------- LINE CHART -------------------------
                    dmc.Paper(
                        dcc.Loading(
                            dcc.Graph(id='demogr-gender-trend')
                        ),
                        p='sm',
                        withBorder=True
                    ),
                ]
            ),
            # ---- RACE -----------------------------------------------------------
            dmc.TabsPanel(
                value="race",
                children=[
                    dmc.Flex(
                        justify="space-between",
                        align="center",
                        mt="sm", mb="sm",
                        children=[
                            dmc.Switch(
                                id='gender-race-toggle',
                                labelPosition="right",
                                label='Show Gender'
                            ),
                        ]
                    ),
                    # ------------------------- BAR CHART -------------------------
                    dmc.Paper(
                        dcc.Loading(
                            dcc.Graph(id='demogr-race')
                        ),
                        p='sm',
                        withBorder=True,                     
                    ),

                    dmc.Space(h=25),
                    dmc.Divider(
                        label=dmc.Text("Over the Years", size="lg", fw=600),
                        size='md'),
                    dmc.Space(h=15),

                    # ------------------------- LINE CHART -------------------------
                    dmc.Paper(
                        dcc.Loading(
                            dcc.Graph(id='demogr-race-trend')
                        ),
                        p='sm',
                        withBorder=True
                    ),
                ],
            ),
        ]
    )
], gap='md', p='lg')

# ── CACHE ───────────────────────────────────────────────────────────────────

@lru_cache(maxsize=64)  
def get_top_group_cached(year, demographic_col, condition, state, bp_status):
    return get_top_group_for_condition(df, year, demographic_col=demographic_col, 
                                       condition=condition, state=state, bp_status=bp_status)

@lru_cache(maxsize=16)
def get_breakdown_age_cached(year, state, bp_status, by_gender):
    return get_breakdown_by_age(df, year, state=state, bp_status=bp_status, by_gender=by_gender)

@lru_cache(maxsize=16)
def get_breakdown_gender_cached(year, state, bp_status):
    return get_breakdown_by_gender(df, year, state=state, bp_status=bp_status)

@lru_cache(maxsize=16)
def get_trend_age_cached(state, bp_status):
    return get_trend_by_age(df, state=state, bp_status=bp_status)

@lru_cache(maxsize=16)
def get_trend_gender_cached(state, bp_status):
    return get_trend_by_gender(df, state=state, bp_status=bp_status)

@lru_cache(maxsize=16)
def get_trend_race_cached(state, bp_status):
    return get_trend_by_race(df, state=state, bp_status=bp_status)

# ── CALLBACKS ─────────────────────────────────────────────────────────────────
@callback(
        Output("demogr_bp_status_container", "style"),
        Input("global-filters", "data"),
)
def toggle_demogr_hbp_filter(filters):
    condition = filters["condition"]
    if condition == "Hypertension_Rate":
        return {"display": "none"}
    return {"display": "block"}


@callback(
    Output("demogr-summary-cards", "children"),
    Input("global-filters", "data"),
)
def update_demo_cards(filters):
    year = int(filters["year"]) if filters["year"] else None
    state = filters["state"]
    condition = filters["condition"]
    bp_status = filters["compare_to"] or "with_hypertension"

    year_label = str(year) if year else "All Years"

    condition_map = {
        "Hypertension_Rate": ("Hypertension"),
        "Depression_Rate": ("Depression"),
        "BP_Depress_Rate": ("Hypertension & Depression"),
        "BP_Distress_Rate": ("Hypertension & Mental Distress"),
        "Freq_Distress_Rate": ("Frequent Mental Distress")
    }
    cond_label = condition_map.get(condition, condition_map['Hypertension_Rate'])

    age_group,  age_rate  = get_top_group_cached(year, "Age",  condition, state=state, bp_status=bp_status)
    sex_group,  sex_rate  = get_top_group_cached(year, "Sex",  condition, state=state, bp_status=bp_status)
    race_group, race_rate = get_top_group_cached(year, "Race", condition, state=state, bp_status=bp_status)

    def card(label, group, rate, color):
        return dmc.Paper([
            dmc.Text(label, size="xs", c="dimmed", mb=4),
            dmc.Text(group if group else "—", size="lg", fw=700, c=color),
            dmc.Text(f"{rate:.1f}%" if rate is not None else "—", size="sm", c="dimmed")
        ], p="md", radius="md", shadow="xs", style={"textAlign": "center"})

    return [
        card(f"Highest {cond_label} Rate by Age ({year_label})",  age_group,  age_rate,  "#e74c3c"),
        card(f"Highest {cond_label} Rate by Sex ({year_label})",  sex_group,  sex_rate,  "#3498db"),
        card(f"Highest {cond_label} Rate by Race ({year_label})", race_group, race_rate, "#8e44ad"),
    ]


@callback(
    Output("demogr-age", "figure"),
    Input("global-filters", "data"),
    Input("gender-age-toggle", "checked"),
)
def update_age_chart(filters, by_gender):
    year = int(filters["year"]) if filters["year"] else None
    state = filters["state"]
    condition = filters["condition"]
    bp_status = filters["compare_to"] or "with_hypertension"

    data = get_breakdown_age_cached(year, state=state, bp_status=bp_status, by_gender=by_gender)
    return plot_by_age(data, condition, by_gender=by_gender)


@callback(
    Output("demogr-gender", "figure"),
    Input("global-filters", "data"),
)
def update_gender_chart(filters):
    year = int(filters["year"]) if filters["year"] else None
    state = filters["state"]
    condition = filters["condition"]
    bp_status = filters["compare_to"] or "with_hypertension"

    data = get_breakdown_gender_cached(year, state=state, bp_status=bp_status)
    return plot_by_gender(data, condition)


@callback(
    Output("demogr-race", "figure"),
    Input("global-filters", "data"),
    Input("gender-race-toggle", "checked"),
)
def update_race_chart(filters, by_gender):
    year = int(filters["year"]) if filters["year"] else None
    state = filters["state"]
    condition = filters["condition"]
    bp_status = filters["compare_to"] or "with_hypertension"

    data = get_breakdown_by_race(df, year, state=state, by_gender=by_gender, bp_status=bp_status)
    return plot_by_race(data, condition, by_gender=by_gender)


@callback(
    Output("demogr-age-trend", "figure"),
    Input("global-filters", "data"),
)
def update_age_trend(filters):
    state = filters["state"]
    condition = filters["condition"]
    bp_status = filters["compare_to"] or "with_hypertension"

    data = get_trend_age_cached(state=state, bp_status=bp_status)
    return plot_trend_age(data, condition)


@callback(
    Output("demogr-gender-trend", "figure"),
    Input("global-filters", "data"),
)
def update_gender_trend(filters):
    state = filters["state"]
    condition = filters["condition"]
    bp_status = filters["compare_to"] or "with_hypertension"

    data = get_trend_gender_cached(state=state, bp_status=bp_status)
    return plot_trend_gender(data, condition)


@callback(
    Output("demogr-race-trend", "figure"),
    Input("global-filters", "data"),
)
def update_race_trend(filters):
    state = filters["state"]
    condition = filters["condition"]
    bp_status = filters["compare_to"] or "with_hypertension"

    data = get_trend_race_cached(state=state, bp_status=bp_status)
    return plot_trend_race(data, condition)