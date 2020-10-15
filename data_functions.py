import state_const
import numpy as np
import pandas as pd
import pyarrow as pa


def serialize_pd(df):
    return pa.serialize(df).to_buffer().to_pybytes()


def deserialize_pd(pybytes):
    return pa.deserialize(pybytes)


def load_data(csv_filenames):
    elections_data = pd.concat([pd.read_csv(p) for p in csv_filenames], ignore_index=True)
    states_dem_share = elections_data[state_const.states].to_numpy()
    ec_vote_size_np = np.array([[state_const.ec_vote_size[s]] for s in state_const.states])

    with_dem05 = (states_dem_share >= 0.5) @ ec_vote_size_np
    # let 0.5 tie be resolved in favour of Democratic party
    # alternative: without_dem05 = (states_dem_share > 0.5) @ ec_vote_size_np

    elections_data["dem_ec"] = with_dem05
    return elections_data


def point_lead_to_vote_share(lead):
    _l = lead / 100
    v = 0.5 + _l / 2
    return v


def vote_share_to_point_lead(share):
    other = 1 - share
    v = (share - other) * 100
    return v


def get_chance_dem_win(data):
    return (data[state_const.states] >= 0.5).mean()


def get_mean_dem_results(data):
    return data[state_const.states].mean()


def get_dem_number_state_wins(data):
    return (data[state_const.states] >= 0.5).sum(axis=1)


def get_rep_number_state_wins(data):
    return (data[state_const.states] < 0.5).sum(axis=1)


def win_statistics(data):
    dem_win_data = data.loc[data["dem_ec"] >= 270]
    rep_win_data = data.loc[data["dem_ec"] < 270]
    n = len(data)
    n_r = len(rep_win_data)
    n_d = len(dem_win_data)

    if n == 0:
        n = np.nan

    return (
        data["dem_ec"].mean(),
        (n_d / n, dem_win_data["dem_ec"].mean()),
        (n_r / n, 538 - rep_win_data["dem_ec"].mean())
    )
