import plotly_figures
import numpy as np
import dash


natl_hist_layout = dict(
    height=80,
    margin=dict(b=0, t=0, l=0, r=0),
    selectdirection="h",
    yaxis=dict(showticklabels=False),
    dragmode="select"
)
state_hist_layout = dict(
    height=80,
    margin=dict(b=0, t=0, l=0, r=0),
    selectdirection="h",
    yaxis=dict(showticklabels=False),
    dragmode="select"
)


class DashFigures:
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

    def fig_map_538(self):
        if self.data_model.data_changed or self.new_random_538_map or self.new_average_538_map:
            if self.random_sample_mode:
                fig = plotly_figures.fig_dem_vote_share(self.random_data_sample.iloc[0])
            else:
                fig = plotly_figures.fig_chance_dem_win(self.data_model.data)
        else:
            return dash.no_update

        fig.update_layout(
            margin=dict(b=0, t=0, l=0, r=0),
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True),
            height=400
        )
        return fig

    def fig_bar_538(self):
        if self.data_model.data_changed or self.new_random_538_map or self.new_average_538_map:
            if self.random_sample_mode:
                b_fig = plotly_figures.fig_ec_bar(self.random_data_sample)
            else:
                b_fig = plotly_figures.fig_ec_bar(self.data_model.data)
        else:
            return dash.no_update

        b_fig.update_layout(
            margin=dict(b=0, t=30, l=0, r=0),
            height=70
        )

        return b_fig

    def fig_natl_vote_hist(self):
        if not self.data_model.data_changed:
            return dash.no_update
        fig = plotly_figures.fig_rep_natl_vote_hist(self.data_model.data)
        fig.update_layout(**natl_hist_layout)
        return fig

    def fig_ec_vote_hist(self):
        if not self.data_model.data_changed:
            return dash.no_update
        fig = plotly_figures.fig_rep_ec_vote_hist(self.data_model.data)
        fig.update_layout(**natl_hist_layout)
        return fig

    def fig_n_states_win_hist(self):
        if not self.data_model.data_changed:
            return dash.no_update
        fig = plotly_figures.fig_rep_n_states_win_hist(self.data_model.data)
        fig.update_layout(**natl_hist_layout)
        return fig

    def fig_state_vote_hist(self, state, force=False):
        if not self.data_model.data_changed and not force:
            return dash.no_update

        h_fig = plotly_figures.fig_rep_state_vote_hist(self.data_model.data, state, True)
        h_fig.update_layout(state_hist_layout)

        x_min = np.inf
        x_max = -np.inf
        for trace_data in h_fig.data:
            if len(trace_data.x) == 0:
                continue
            data_min = min(trace_data.x)
            data_max = max(trace_data.x)
            x_min = min(x_min, data_min)
            x_max = max(x_max, data_max)

        # add vertical line
        if x_min <= 50 <= x_max:
            h_fig.update_layout(shapes=[
                dict(
                    type="line",
                    yref="paper", y0=0, y1=1,
                    xref="x", x0=50, x1=50
                )
            ])

        return h_fig

    def fig_by_id(self, id_value):
        id_type = id_value["type"]
        if id_type == "map_538":
            return self.fig_map_538()
        if id_type == "bar_538":
            return self.fig_bar_538()
        if id_type == "natl_vote_hist":
            return self.fig_natl_vote_hist()
        if id_type == "ec_vote_hist":
            return self.fig_ec_vote_hist()
        if id_type == "n_states_win_hist":
            return self.fig_n_states_win_hist()
        if id_type == "state_vote_hist":
            return self.fig_state_vote_hist(id_value["state"])
        else:
            raise Exception(f"Unexpected id {id_value}")
