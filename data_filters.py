from data_functions import get_dem_number_state_wins


def filter_dem_state_win(data,  dem_win):
    return data.loc[data[dem_win] > 0.5]


def filter_rep_state_win(data,  rep_win):
    return data.loc[data[rep_win] < 0.5]


def filter_rep_states_wins(data, rep_wins):
    for w in rep_wins:
        data = filter_rep_state_win(data, w)
    return data


def filter_dem_states_wins(data, dem_wins):
    for w in dem_wins:
        data = filter_dem_state_win(data, w)
    return data


def filter_dem_electoral_college_range(data, f=0, t=538):
    data = data.loc[f <= data["dem_ec"]]
    data = data.loc[data["dem_ec"] <= t]
    return data


def filter_rep_electoral_college_range(data, f=0, t=538):
    data = data.loc[f <= (538 - data["dem_ec"])]
    data = data.loc[(538 - data["dem_ec"]) <= t]
    return data


def filter_dem_electoral_college(data, ec):
    return filter_dem_electoral_college_range(data, ec, ec)


def filter_rep_electoral_college(data, ec):
    return filter_rep_electoral_college_range(data, ec, ec)


def filter_dem_natl_vote_range(data, f=0, t=1):
    data = data.loc[f <= data["natl_pop_vote"]]
    data = data.loc[data["natl_pop_vote"] <= t]
    return data


def filter_rep_natl_vote_range(data, f=0, t=1):
    data = data.loc[f <= (1 - data["natl_pop_vote"])]
    data = data.loc[(1 - data["natl_pop_vote"]) <= t]
    return data


def filter_dem_n_states_win_range(data, n_min=0, n_max=51):
    n_dem_states_won = get_dem_number_state_wins(data)
    data = data.loc[n_min <= n_dem_states_won]
    data = data.loc[n_dem_states_won <= n_max]
    return data


def filter_rep_n_states_win_range(data, n_min=0, n_max=51):
    n_rep_states_won = 51 - get_dem_number_state_wins(data)
    data = data.loc[n_min <= n_rep_states_won]
    data = data.loc[n_rep_states_won <= n_max]
    return data


def filter_dem_n_states_win(data, n):
    return filter_dem_n_states_win_range(data, n, n)


def filter_rep_n_states_win(data, n):
    return filter_rep_n_states_win_range(data, n, n)


def filter_dem_state_vote_range(data, state, f=0, t=1):
    data = data.loc[f <= data[state]]
    data = data.loc[data[state] <= t]
    return data


def filter_rep_state_vote_range(data, state, f=0, t=1):
    data = data.loc[f <= (1 - data[state])]
    data = data.loc[(1 - data[state]) <= t]
    return data


def filter_dem_states_vote_range(data, ranges_dict):
    for s, (f, t) in ranges_dict.items():
        data = filter_dem_state_vote_range(s, f, t)
    return data


def filter_rep_states_vote_range(data, ranges_dict):
    for s, (f, t) in ranges_dict.items():
        data = filter_rep_state_vote_range(s, f, t)
    return data
