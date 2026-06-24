import dash
import dash_mantine_components as dmc
from dash import dcc, page_container, callback, Output, Input, State
from data_geo import load_data, get_states_for_year

dash._dash_renderer._set_react_version("18.2.0")

app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server

df = load_data()
YEARS = sorted(df["Year"].unique().tolist())
STATES = sorted(df["State_Name"].dropna().unique().tolist())

METRICS = [
    {'value': 'Hypertension_Rate', 'label': 'Hypertension'},
    {"value": "Depression_Rate", "label": "Depression"},
    {"value": "Freq_Distress_Rate", "label": "Freq Mental Distress"},
]

app.layout = dmc.MantineProvider(
    children=[
        dmc.Modal(
            id="info-modal",
            title=dmc.Text("About This Dashboard", fw=700, size="lg"),
            fullScreen=False,
            size="lg",                        
            styles={
                "content": {
                    "@media (max-width: 768px)": {
                        "width": "100vw",
                        "height": "100vh",
                        "margin": 0,
                        "borderRadius": 0,
                    }
                }
            },
            children=[
                dmc.Stack([
                    dmc.Text(
                        "This dashboard explores how mental health differs between U.S. adults "
                        "with and without hypertension, using data from the CDC's Behavioral Risk "
                        "Factor Surveillance System (BRFSS) across five survey years: "
                        "2015, 2017, 2019, 2021, and 2023.",
                        size="sm"
                    ),

                    dmc.Divider(),

                    dmc.Text("How to Use", fw=700, size="sm"),
                    dmc.Text(
                        "Use the filters at the top of each page to explore data by year, state, "
                        "and condition. The Population filter lets you compare mental health outcomes "
                        "specifically among adults with or without hypertension.",
                        size="sm"
                    ),

                    dmc.Divider(),

                    dmc.Text("Variable Definitions", fw=700, size="sm"),
                    dmc.Stack([
                        dmc.Group([
                            dmc.Badge("Hypertension", color="red", variant="light"),
                            dmc.Text(
                                "Refers to adults who have been told or diagnosed by a health "
                                "professional that they have high blood pressure or hypertension. "
                                "Self-reported; does not require clinical measurement.",
                                size="sm"
                            ),
                        ], align="flex-start", gap="sm"),

                        dmc.Group([
                            dmc.Badge("Depression", color="blue", variant="light"),
                            dmc.Text(
                                "Refers to adults who have ever been told by a doctor, nurse, or "
                                "other health professional that they have a depressive disorder, "
                                "including depression, major depression, dysthymia, or minor depression.",
                                size="sm"
                            ),
                        ], align="flex-start", gap="sm"),

                        dmc.Group([
                            dmc.Badge("Frequent Mental Distress", color="orange", variant="light"),
                            dmc.Text(
                                "Refers to adults who reported 14 or more days of poor mental health "
                                "in the past 30 days. This threshold follows the CDC's definition of "
                                "frequent mental distress and is used as a functional burden measure "
                                "distinct from a clinical diagnosis.",
                                size="sm"
                            ),
                        ], align="flex-start", gap="sm"),
                    ], gap="md"),

                    dmc.Divider(),

                    dmc.Text("Data Source", fw=700, size="sm"),
                    dmc.Text(
                        "All estimates are weighted using BRFSS survey weights (LLCPWT) to be "
                        "representative of the U.S. adult population. Data sourced from the CDC "
                        "Behavioral Risk Factor Surveillance System (BRFSS).",
                        size="sm", c="dimmed"
                    ),
                ], gap="md")
            ]
        ),

        dmc.AppShell(
            id="app-shell",
            children=[
                dcc.Store(id="global-filters", storage_type="session", data={
                    "year": "2023",
                    "state": None,
                    "condition": "Depression_Rate",
                    "compare_to": "national",
                }),

                dmc.AppShellHeader(
                    dmc.Group(
                        h="100%",
                        px="md",
                        justify="space-between",
                        children=[
                            dmc.Group(
                                children=[
                                    dmc.Burger(
                                        id="burger",
                                        size="sm",
                                        hiddenFrom="sm",
                                        opened=False
                                    ),
                                    dmc.Title(
                                        "Hypertension and Mental Health in U.S. Adults",
                                        visibleFrom="sm",
                                        order=2,
                                        style={'fontFamily': 'Outfit', 'color': 'white'}
                                    ),
                                ]
                            ),
                            # ── INFO BUTTON ────────────────────────────────
                            dmc.ActionIcon(
                                id="open-info-modal",
                                children=dmc.Text("?", fw=700, c="white", size="lg"),
                                variant="subtle",
                                size="lg",
                                radius="xl",
                                style={"border": "2px solid rgba(255,255,255,0.6)"}
                            ),
                        ]
                    ),
                    style={'backgroundColor': "#4f433fff", "border": "none"},
                ),

                dmc.AppShellNavbar(
                    p="sm",
                    children=[
                        dmc.NavLink(id="nav-geo", label="Geographic", href="/", active="exact", variant='filled', color='black'),
                        dmc.NavLink(id="nav-demo", label="Demographics", href="/demographics", active="exact", variant='subtle', color='black'),
                    ],
                    style={'backgroundColor': '#eae8e4ff'}
                ),

                dmc.AppShellMain([
                    dmc.Paper(
                        dmc.Flex(
                            justify="space-between",
                            align="center",
                            wrap="wrap",
                            gap="md",
                            children=[
                                dmc.Flex(
                                    gap="md",
                                    align="flex-end",
                                    children=[
                                        dmc.Select(
                                            id="global-year-dropdown",
                                            label="Year",
                                            data=[{"label": str(y), "value": str(y)} for y in YEARS],
                                            value="2023",
                                            allowDeselect=False,
                                            w=105
                                        ),
                                        dmc.Select(
                                            id="global-state-dropdown",
                                            label="State",
                                            data=[{"label": s, "value": s} for s in STATES],
                                            value=None,
                                            placeholder="All States (National)",
                                            searchable=True,
                                            w=180
                                        ),
                                    ]
                                ),
                                dmc.Flex(
                                    gap="md",
                                    align="flex-end",
                                    children=[
                                        dmc.Select(
                                            id="global-compare-dropdown",
                                            label="Population",
                                            data=[
                                                {"value": "all", "label": "All Adults"},
                                                {"value": "with_hypertension", "label": "Adults With Hypertension"},
                                                {"value": "without_hypertension", "label": "Adults Without Hypertension"},
                                            ],
                                            value="all",
                                            allowDeselect=False,
                                            w=210
                                        ),
                                        dmc.Select(
                                            id="global-condition-dropdown",
                                            label="Condition",
                                            data=METRICS,
                                            value="Hypertension_Rate",
                                            allowDeselect=False,
                                            w=170
                                        ),
                                    ]
                                ),
                            ],
                        ),
                        p="sm",
                        radius="md",
                        withBorder=False,
                        mb="md",
                    ),
                    page_container
                ]),
            ],
            header={"height": 55},
            navbar={
                "width": 150,
                "breakpoint": "sm",
                "collapsed": {"mobile": True}
            },
            padding="sm"
        )
    ]
)


@callback(
    Output("info-modal", "opened"),
    Input("open-info-modal", "n_clicks"),
    State("info-modal", "opened"),
    prevent_initial_call=True
)
def toggle_modal(n_clicks, is_open):
    return not is_open

@callback(
    Output("global-state-dropdown", "data"),
    Output("global-state-dropdown", "value"),
    Input("global-year-dropdown", "value"),
    State("global-state-dropdown", "value"),
)
def sync_state_options(year, current_state):
    year_int = int(year) if year else None 
    available = get_states_for_year(df, year_int)

    options = [{"label": s, "value": s} for s in available]
    new_value = current_state if current_state in available else None

    return options, new_value


@callback(
    Output("global-compare-dropdown", "data"),
    Output("global-compare-dropdown", "value"),
    Input("global-condition-dropdown", "value"),
    State("global-compare-dropdown", "value"),
)
def toggle_compare_options(condition, current_compare):
    is_hypertension = condition == "Hypertension_Rate"

    data = [
        {
            "value": "all",
            "label": "All Adults",
            "disabled": False,
        },
        {
            "value": "with_hypertension",
            "label": "Adults With Hypertension",
            "disabled": is_hypertension,
        },
        {
            "value": "without_hypertension",
            "label": "Adults Without Hypertension",
            "disabled": is_hypertension,
        },
    ]

    # if hypertension is selected and the current compare value is now disabled,
    # fall back to "all" so the dropdown isn't left in an invalid state
    new_value = "all" if (is_hypertension and current_compare != "all") else current_compare

    return data, new_value


@callback(
    Output("global-filters", "data"),
    Input("global-year-dropdown", "value"),
    Input("global-state-dropdown", "value"),
    Input("global-condition-dropdown", "value"),
    Input("global-compare-dropdown", "value"),
)
def sync_global_filters(year, state, condition, compare_to):
    return {
        "year": year,
        "state": state,
        "condition": condition,
        "compare_to": compare_to,
    }


@callback(
    Output("app-shell", "navbar"),
    Input("burger", "opened"),
    State("app-shell", "navbar"),
)
def toggle_navbar(opened, navbar):
    navbar["collapsed"] = {"mobile": not opened}
    return navbar


@callback(
    Output("nav-geo", "active"),
    Output("nav-demo", "active"),
    #Output("nav-socio", "active"),
    Input("_pages_location", "pathname")
)
def update_active_links(pathname):
    return (
        pathname == "/",
        pathname == "/demographics",
        #pathname == "/socioeconomic",
    )


if __name__ == "__main__":
    app.run(debug=False)