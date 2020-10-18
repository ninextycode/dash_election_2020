import dash_html_components as html
import dash_core_components as dcc
import dash
import dash_bootstrap_components as dbc
import data_functions
from app.dash_figures import DashFigures
import plotly_figures
import state_const
import numpy as np


natl_hist_config = dict(
    displayModeBar=False,
)
state_hist_config = dict(
    displayModeBar=False,
)
map_538_config = dict(
    scrollZoom=False,
    modeBarButtonsToRemove=["lasso2d", "select2d"]
)
bar_538_config = dict(
    scrollZoom=False,
    displayModeBar=False,
)
zero_hundred_pattern = r"0*(\d?\d(\.\d*)?|100)"
zero_538_pattern = r"0*(\d?\d|[1-4]\d\d|5[0-2]\d|53[0-8])"
zero_51 = r"0*(\d|[1-4]\d|5[0-1])"


def get_average_simulations_summary(data, total_simulations):
    n = len(data)
    av_d_ec, (d_win, d_ec), (r_win, r_ec) = data_functions.win_statistics(data)
    if total_simulations == 0:
        ratio = np.NaN
    else:
        ratio = n / total_simulations

    text = [
        f"2020 Election, {n} simulations out of {total_simulations} ({ratio * 100:.2f}%)",
        f"On average, Biden gets {av_d_ec:.2f} electoral college votes, Trump gets {538 - av_d_ec:.2f}",
        f"Trump has {100 * r_win:.2f}% chance of winning, with an average of {r_ec:.2f} electoral votes",
        f"Biden has {100 * d_win:.2f}% chance of winning, with an average of {d_ec:.2f} electoral votes"
    ]
    return text


def get_single_simulations_summary(data):
    data = data.iloc[[0]]
    av_d_ec, (d_win, d_ec), (r_win, r_ec) = data_functions.win_statistics(data)

    rep_n_states_won = data_functions.get_rep_number_state_wins(data).iloc[0]
    dem_n_states_won = data_functions.get_dem_number_state_wins(data).iloc[0]

    dem_natl_pop_vote = (100 * data["natl_pop_vote"]).iloc[0]
    rep_natl_pop_vote = 100 * (1 - data["natl_pop_vote"]).iloc[0]

    text = [
        f"2020 Election, random sample",
        f"Biden gets {av_d_ec:.0f} electoral college votes, Trump gets {538 - av_d_ec:.0f}",
        f"Trump gets {rep_natl_pop_vote:.2f}% of the popular vote and wins {rep_n_states_won} states",
        f"Biden gets {dem_natl_pop_vote:.2f}% of the popular vote and wins {dem_n_states_won} states"
    ]
    return text


def add_br(lines):
    if len(lines) == 0:
        return []
    lines_br = [lines[0]]
    for l in lines[1:]:
        lines_br.append(html.Br())
        lines_br.append(l)
    return lines_br


class DashLayout:
    def __init__(
        self,
        data_model,
        random_data_sample=None,
        random_sample_mode=False,
        new_random_538_map=False,
        new_average_538_map=False
    ):
        self.data_model = data_model
        self.random_data_sample = random_data_sample
        self.random_sample_mode = random_sample_mode
        self.new_random_538_map = new_random_538_map
        self.new_average_538_map = new_average_538_map
        self.dash_figures_builder = DashFigures(
            data_model,
            random_data_sample,
            random_sample_mode,
            new_random_538_map,
            new_average_538_map
        )

    def get_layout(self):
        layout = html.Div(
            html.Div([
                html.Div(
                    html.Div(
                        html.H1("2020 Presidential Election", className="m-2"),
                        className="col-12",
                        style={"text-align": "center"}
                    ),
                    className="row"
                ),
                html.Div([
                    html.Div(
                        self.get_states_selector_block(),
                        className="col-3 px-1"
                    ),
                    html.Div([
                        dcc.Graph(
                            figure=self.dash_figures_builder.fig_bar_538(),
                            id=dict(type="bar_538"),
                            config=bar_538_config,
                            className="mx-5 mt-3"
                        ),
                        dcc.Graph(
                            figure=self.dash_figures_builder.fig_map_538(),
                            id=dict(type="map_538"),
                            config=map_538_config,
                            className="mx-2 mb-2"
                        ),
                        self.get_national_controls(),
                        html.Div(self.get_summary(), id=dict(type="summary"))],
                        className="col-9 px-1"
                    )],
                    className="row"
                )
            ]),
            className="container-xl"
        )
        return layout

    def get_states_selector_block(self):
        layout = html.Div([
            html.H5("States:"),
            dcc.Dropdown(
                id=dict(type="states_selector"),
                options=[dict(label=s, value=s) for s in state_const.states],
                value=["AZ", "FL", "GA", "OH", "PA"],
                multi=True
            ),
            html.Div(
                html.Div([], id=dict(type="states_control_block"), style={"direction": "ltr"}),
                style={
                    "overflow-y": "auto",
                    "height": "780px",
                    "direction": "rtl",
                }
            )])
        return layout

    def get_state_block(self, state_name):
        layout = html.Div([
            html.H5(f"{state_const.state_names_short_to_long[state_name]} Vote"),
            dcc.Graph(
                figure=self.dash_figures_builder.fig_state_vote_hist(state_name, force=True),
                id=dict(state=state_name, type="state_vote_hist"),
                config=state_hist_config
            ),
            html.Div([
                "Trump: from ",
                dcc.Input(
                    value=0,
                    id=dict(type="rep_state_vote_lower_limit", state=state_name),
                    type="text", pattern=zero_hundred_pattern, debounce=True, size="3"
                ), " to ",
                dcc.Input(
                    value=100,
                    id=dict(type="rep_state_vote_upper_limit", state=state_name),
                    type="text", pattern=zero_hundred_pattern, debounce=True, size="3"
                )],
                className="mb-1"
            ),
            html.Div([
                dbc.Button(
                    "Trump",
                    id=dict(state=state_name, type="rep_win_button"),
                    className="state_button mx-1",
                    style={"background-color": plotly_figures.r_red}
                ),
                dbc.Button(
                    "Biden",
                    id=dict(state=state_name, type="dem_win_button"),
                    className="state_button mx-1",
                    style={"background-color": plotly_figures.d_blue}
                ),
                dbc.Button(
                    "Reset",
                    id=dict(state=state_name, type="reset_state_button"),
                    className="state_button mx-1"
                ),
            ])],
            className="my-1 px-2 py-2",
            style={
                "border-color": "black",
                "border": "1px",
                "border-style": "solid"
            },
            id=dict(type="state_block", state=state_name)
        )
        return layout

    def get_national_controls(self):
        layout = html.Div([
            self.get_national_buttons(),
            self.get_national_histograms()],
            className="container"
        )
        return layout

    def get_national_buttons(self):
        return html.Div(
            html.Div([
                dbc.Button(
                    "Random Result",
                    id=dict(type="random_result_button"),
                    className="mx-1 btn-info",
                ),
                dbc.Button(
                    "Average Result",
                    id=dict(type="average_result_button"),
                    className="mx-1 btn-info"
                ),
                dbc.Button(
                    "Reset",
                    id=dict(type="natl_reset_button"),
                    className="mx-1 btn-warning",
                ),
                dbc.Button(
                    "Toggle",
                    id=dict(type="natl_toggle_button"),
                    className="mx-1 btn-dark",
                )],
                className="col mb-1 mx-4"
            ),
            className="row"
        )

    def get_national_histograms(self):
        return dbc.Collapse([
            html.Div(
                self.get_natl_vote_block(),
                className="col px-1"
            ),
            html.Div(
                self.get_ec_vote_block(),
                className="col px-1"
            ),
            html.Div(
                self.get_n_states_win_block(),
                className="col px-1"
            )],
            is_open=True,
            className="row",
            id=dict(type="natl_histograms")
        )

    def get_natl_vote_block(self):
        layout = html.Div([
            html.H5("National Popular Vote"),
            dcc.Graph(
                figure=self.dash_figures_builder.fig_natl_vote_hist(),
                id=dict(type="natl_vote_hist"),
                config=natl_hist_config
            ),
            html.Div([
                "Trump limit: ",
                dcc.Input(
                    value=0,
                    id=dict(type="rep_natl_vote_lower_limit"),
                    type="text", pattern=zero_hundred_pattern, debounce=True, size="3"
                ), " to ",
                dcc.Input(
                    value=100,
                    id=dict(type="rep_natl_vote_upper_limit"),
                    type="text", pattern=zero_hundred_pattern, debounce=True, size="3"
                )],
                className="mb-1"
            ),
            html.Div([
                dbc.Button(
                    "Trump",
                    id=dict(type="rep_natl_vote_win_button"),
                    className="mx-1",
                    style={"background-color": plotly_figures.r_red}
                ),
                dbc.Button(
                    "Biden",
                    id=dict(type="dem_natl_vote_win_button"),
                    className="mx-1",
                    style={"background-color": plotly_figures.d_blue}
                ),
                dbc.Button(
                    "Reset",
                    id=dict(type="reset_natl_vote_button"),
                    className="mx-1"
                ),
            ])],
            className="my-1 px-2 py-2",
            style={
                "border-color": "black",
                "border": "1px",
                "border-style": "solid"
            },
            id=dict(type="natl_vote_block")
        )
        return layout

    def get_ec_vote_block(self):
        layout = html.Div([
            html.H5("Electoral College Vote"),
            dcc.Graph(
                figure=self.dash_figures_builder.fig_ec_vote_hist(),
                id=dict(type="ec_vote_hist"),
                config=natl_hist_config
            ),
            html.Div([
                "Trump limit: ",
                dcc.Input(
                    value=0,
                    id=dict(type="rep_ec_vote_lower_limit"),
                    type="text", pattern=zero_538_pattern, debounce=True, size="3"
                ), " to ",
                dcc.Input(
                    value=538,
                    id=dict(type="rep_ec_vote_upper_limit"),
                    type="text", pattern=zero_538_pattern, debounce=True, size="3"
                )],
                className="mb-1"
            ),
            html.Div([
                dbc.Button(
                    "Trump",
                    id=dict(type="rep_ec_vote_win_button"),
                    className="mx-1",
                    style={"background-color": plotly_figures.r_red}
                ),
                dbc.Button(
                    "Biden",
                    id=dict(type="dem_ec_vote_win_button"),
                    className="mx-1",
                    style={"background-color": plotly_figures.d_blue}
                ),
                dbc.Button(
                    "Reset",
                    id=dict(type="reset_ec_vote_button"),
                    className="mx-1"
                ),
            ])],
            className="my-1 px-2 py-2",
            style={
                "border-color": "black",
                "border": "1px",
                "border-style": "solid"
            },
            id=dict(type="ec_vote_block")
        )

        return layout

    def get_n_states_win_block(self):
        layout = html.Div([
            html.H5("Number Of States Won"),
            dcc.Graph(
                figure=self.dash_figures_builder.fig_n_states_win_hist(),
                id=dict(type="n_states_win_hist"),
                config=natl_hist_config
            ),
            html.Div([
                "Trump limit: ",
                dcc.Input(
                    value=0,
                    id=dict(type="rep_n_states_win_lower_limit"),
                    type="text", pattern=zero_51, debounce=True, size="2"
                ), " to ",
                dcc.Input(
                    value=51,
                    id=dict(type="rep_n_states_win_upper_limit"),
                    type="text", pattern=zero_51, debounce=True, size="2"
                )],
                className="mb-1"
            ),
            html.Div([
                dbc.Button(
                    "Reset",
                    id=dict(type="reset_n_states_win_button"),
                    className="mx-1"
                )]
            )],
            className="my-1 px-2 py-2",
            style={
                "border-color": "black",
                "border": "1px",
                "border-style": "solid"
            },
            id=dict(type="n_states_win_block")
        )

        return layout

    def get_output_item(self, outp):
        if isinstance(outp, dict):
            if outp["id"]["type"] == "summary":
                return self.get_summary()

            if outp["property"] == "figure":
                return self.dash_figures_builder.fig_by_id(outp["id"])

        elif isinstance(outp, list):
            return [self.get_output_item(_outp) for _outp in outp]
        else:
            raise Exception(f"Unexpected output item {outp}")

    def get_summary(self):
        if self.data_model.data_changed or self.new_random_538_map or self.new_average_538_map:
            if self.random_sample_mode:
                return self.get_random_sample_summary()
            else:
                return self.get_average_summary()
        else:
            return dash.no_update

    def get_average_summary(self):
        summary_lines = get_average_simulations_summary(self.data_model.data, len(self.data_model.original_data))
        summary_br = add_br(summary_lines)

        natl_vote_text = [
            html.Div([
                html.H4("Summary:"),
                html.Div(
                    summary_br, className="m-2"
                )
            ], className="m-2")
        ]
        return natl_vote_text

    def get_random_sample_summary(self):
        if len(self.random_data_sample) == 0:
            return []

        summary_lines = get_single_simulations_summary(self.random_data_sample)
        summary_br = add_br(summary_lines)

        states_summary_lines = []
        states_summary_line = []
        for s in state_const.states:
            dem_vote = self.random_data_sample[s].iloc[0]
            winner = "Trump" if dem_vote < 0.5 else "Biden"
            point_lead = np.abs(data_functions.vote_share_to_point_lead(dem_vote))
            states_summary_line.append(f"{s}: {winner}(+{point_lead:.1f})")
            if len(states_summary_line) == 5:
                states_summary_lines.append(", ".join(states_summary_line))
                states_summary_line = []
        states_summary_br = add_br(states_summary_lines)

        natl_vote_text = [
            html.Div([
                html.H4("Summary:"),
                html.Div(
                    summary_br, className="m-2"
                ),
                html.H5("State by state results:"),
                html.Div(
                    states_summary_br, className="m-2"
                ),
            ], className="m-2")
        ]
        return natl_vote_text
