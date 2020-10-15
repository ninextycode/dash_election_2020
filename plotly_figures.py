import plotly.graph_objects as go
import state_const
import data_functions
import numpy as np


r_red = "#DF0100"
d_blue = "#0071CF"

colorscale1 = [[0, r_red], [0.5, "#FFFFFF"], [1, d_blue]]
colorscale2 = [[0, "red"], [0.5, "white"], [1, "blue"]]


def fig_empty_us_map():
    fig = go.Figure(data=go.Choropleth(
        locations=state_const.states,
        locationmode='USA-states',
    ))
    fig.update_layout(geo_scope='usa')
    return fig


def fig_chance_dem_win(data):
    n = len(data)

    if n == 0:
        return fig_empty_us_map()

    chance_dem_win = data_functions.get_chance_dem_win(data)

    def state_text(s):
        lines = [
            f"Chance to win {s}",
            f"- Trump: {100 - chance_dem_win[s] * 100:.2f}%",
            f"- Biden: {chance_dem_win[s] * 100:.2f}%"
        ]
        return "<br>".join(lines)

    fig = go.Figure(data=go.Choropleth(
        text=[state_text(s) for s in state_const.states],
        hoverinfo="text",
        locations=state_const.states,
        z=chance_dem_win[state_const.states].to_list(),
        locationmode='USA-states',
        colorscale=colorscale1,
        zmin=0, zmid=0.5, zmax=1
    )
    )

    fig.update_traces(showscale=False)

    ec_vote_size_ = state_const.ec_vote_size.copy()
    ec_vote_size_.pop("DC")

    fig.add_trace(go.Scattergeo(
        text=[f"{s}" for s in ec_vote_size_.values()],
        locations=list(ec_vote_size_.keys()),
        mode="text",
        locationmode="USA-states",
        hoverinfo="skip",
        textfont=dict(size=14, color="black")
    )
    )

    fig.update_layout(geo_scope='usa')

    return fig


def fig_ec_bar(data):
    chance_dem_win = data_functions.get_chance_dem_win(data)
    sorted_chance_dem_win_keys = sorted(state_const.states, key=lambda k: (1 - chance_dem_win[k], k))
    sorted_chance_dem_win = np.array([chance_dem_win[s] for s in sorted_chance_dem_win_keys])
    winner_lbl = {}
    for s in state_const.states:
        p_b = 100 * chance_dem_win[s]
        p_t = 100 * (1 - chance_dem_win[s])
        if chance_dem_win[s] < 0.5:
            winner_lbl[s] = f"Trump {p_t:.0f}%"
        elif chance_dem_win[s] > 0.5:
            winner_lbl[s] = f"Biden {p_b:.0f}%"
        else:
            winner_lbl[s] = "Tie"

    fig = go.Figure(data=[
        go.Bar(
            name=s, orientation="h", x=[state_const.ec_vote_size[s]], y=[0], width=[1],
            hoverinfo="text",
            hovertext=f"{s}:{state_const.ec_vote_size[s]}<br>{winner_lbl[s]}",
            marker=dict(
                colorscale=colorscale1,
                color=[chance_dem_win[s]],
                cmin=0, cmid=0.5, cmax=1,
            )
        ) for s in sorted_chance_dem_win_keys
    ])

    ec_sizes = np.array([state_const.ec_vote_size[s] for s in sorted_chance_dem_win_keys])
    trump_win = ec_sizes @ (sorted_chance_dem_win < 0.5)
    biden_win = ec_sizes @ (sorted_chance_dem_win > 0.5)

    step = 60
    ticks = list(range(269 - step, -1, -step)) + list(range(269 + step, 538, step))
    ec_sizes_cumsum = np.cumsum(ec_sizes)
    for i, t in enumerate(ticks):
        # get existing closest electoral college value
        ticks[i] = ec_sizes_cumsum[np.abs(ec_sizes_cumsum - t).argsort()[0]]
    ticks.extend([0, 269, 538])
    tick_text = [f"{min(t, 538 - t)}" for t in ticks]

    # Change the bar mode
    fig.update_layout(
        barmode="stack",
        yaxis=dict(
            fixedrange=True, showticklabels=False, range=[-0.5, 0.5]
        ),
        xaxis=dict(
            fixedrange=True, range=[0, 538],
            tickvals=ticks,
            ticktext=tick_text,
            tickmode="array"
        ),
        title=dict(
            text=f"Biden <b>{biden_win}</b>" + "\t" * 7 + f"<b>{trump_win}</b> Trump",
            x=0.5, y=0.95,
            font=dict(size=24)
        ),
        dragmode=False
    )
    fig.update_layout(showlegend=False)

    fig.update_layout(shapes=[
        dict(
            type="line", line=dict(width=3, color="black"),
            yref="paper", y0=0, y1=1,
            xref="x", x0=269, x1=269
        )
    ])

    return fig


def _get_bins_dict(data, n_bins=None):
    nv_min = np.ceil(data.min() * 100) / 100
    nv_max = np.floor(data.max() * 100) / 100
    if n_bins is None:
        n_bins = min(50., max(10., len(data) / 1000))
    step = (nv_max - nv_min) / n_bins
    return dict(start=nv_min, end=nv_max, size=step)


def _fig_rep_dem_hist(dem_data, rep_data, bins_dict):
    fig = go.Figure(data=[
        go.Histogram(
            x=dem_data,
            xbins=bins_dict,
            marker=dict(color=r_red),
            hoverinfo="skip"
        ),
        go.Histogram(
            x=rep_data,
            xbins=bins_dict,
            marker=dict(color=d_blue),
            hoverinfo="skip"
        )],
        layout=dict(barmode="stack", showlegend=False, yaxis=dict(fixedrange=True, rangemode="tozero"))
    )

    return fig


def fig_rep_state_vote_hist(data, state, general_election_win_color=False):
    rep_state_pop_vote = 100 * (1 - data[state])
    bins_dict = _get_bins_dict(rep_state_pop_vote)

    if general_election_win_color:
        rep_idx = data["dem_ec"] < 270
        dem_idx = data["dem_ec"] >= 270
    else:
        rep_idx = rep_state_pop_vote > 50
        dem_idx = rep_state_pop_vote <= 50

    fig = _fig_rep_dem_hist(
        rep_state_pop_vote[rep_idx],
        rep_state_pop_vote[dem_idx],
        bins_dict
    )

    return fig


def fig_rep_n_states_win_hist(data):
    rep_n_states_won = data_functions.get_rep_number_state_wins(data)
    bins_dict = dict(start=rep_n_states_won.min() - 0.5, end=rep_n_states_won.max(), size=1)

    fig = _fig_rep_dem_hist(
        rep_n_states_won[data["dem_ec"] < 270],
        rep_n_states_won[data["dem_ec"] >= 270],
        bins_dict
    )
    return fig


def fig_rep_ec_vote_hist(data):
    rep_ec_vote = 538 - data["dem_ec"]

    a = rep_ec_vote.min() - 0.5
    b = rep_ec_vote.max()

    mid = 268.5
    size = 4

    k_left = np.ceil((mid - a) / size)
    bins_dict = dict(start=mid - size * k_left, end=b, size=size)

    fig = _fig_rep_dem_hist(
        rep_ec_vote[data["dem_ec"] < 270],
        rep_ec_vote[data["dem_ec"] >= 270],
        bins_dict
    )
    return fig


def fig_rep_natl_vote_hist(data):
    rep_natl_pop_vote = 100 * (1 - data["natl_pop_vote"])
    bins_dict = _get_bins_dict(rep_natl_pop_vote)

    fig = _fig_rep_dem_hist(
        rep_natl_pop_vote[data["dem_ec"] < 270],
        rep_natl_pop_vote[data["dem_ec"] >= 270],
        bins_dict
    )
    return fig
