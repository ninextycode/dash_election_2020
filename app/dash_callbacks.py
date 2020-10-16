from data_model import DataModel
from data_functions import serialize_pd, deserialize_pd
from app.dash_layout import DashLayout
import random
import dash
from dash.dependencies import Input, Output, State, MATCH, ALL
import state_const
import numpy as np
import json
from datetime import datetime as DateTime
from flask import session
from glob import glob
import data_functions
import os


data_folder = os.environ["ELECTION_DATA_FOLDER"]
data_size = int(os.environ.get("DATA_SIZE", 100000))


no_update_interval = [dash.no_update, dash.no_update]


def get_session_dict():
    if not session.get("initialized", False):
        return init_session_data()

    print("get", sorted(session.keys()))
    session_dict = dict(
        random_data_sample=deserialize_pd(session["random_data_sample"]),
        random_sample_mode=session["random_sample_mode"],
        new_random_538_map=session["new_random_538_map"],
        new_average_538_map=session["new_average_538_map"],
        reset_button_pressed=session["reset_button_pressed"],
        data_model=DataModel.from_json(session["data_model_json"])
    )
    return session_dict


def set_session_dict(session_dict):
    session["data_model_json"] = session_dict["data_model"].to_json()
    session["random_data_sample"] = serialize_pd(session_dict["random_data_sample"])
    session["random_sample_mode"] = session_dict["random_sample_mode"]
    session["new_random_538_map"] = session_dict["new_random_538_map"]
    session["new_average_538_map"] = session_dict["new_average_538_map"]
    session["reset_button_pressed"] = session_dict["reset_button_pressed"]
    session["initialized"] = True
    print("set", sorted(session.keys()))


def init_session_data():
    csv_filenames = glob(f"{data_folder}/*.csv")
    elections_data = data_functions.load_data(csv_filenames)
    new_session_dict = dict(
        data_model=DataModel(
            elections_data.iloc[random.sample(range(len(elections_data)), data_size)]
        ),
        random_data_sample=None,
        random_sample_mode=False,
        new_random_538_map=False,
        new_average_538_map=False,
        reset_button_pressed=False
    )
    set_session_dict(new_session_dict)
    return new_session_dict


def get_dash_layout_builder(session_dict):
    return DashLayout(
        data_model=session_dict["data_model"],
        random_data_sample=session_dict["random_data_sample"],
        random_sample_mode=session_dict["random_sample_mode"],
        new_random_538_map=session_dict["new_random_538_map"],
        new_average_538_map=session_dict["new_average_538_map"]
    )


def set_app_callbacks(app):

    def interval_from_callback_context(context, data_l, btn_vals):
        changed_props = context.triggered
        interval = None

        for p in changed_props:
            id_dict_str, value_str = p["prop_id"].split(".")
            try:
                id_dict = json.loads(id_dict_str)
            except json.JSONDecodeError:
                print("interval_from_callback_context failed", p)
                continue

            val = p["value"]
            if val is None:
                continue

            if id_dict["type"] in btn_vals:
                interval = btn_vals[id_dict["type"]]
            elif id_dict["type"] in data_l:
                interval = val["range"]["x"]

        return interval

    def was_reset_button_pressed(context):
        changed_props = context.triggered
        id_dicts = []
        for p in changed_props:
            id_dict_str, value_str = p["prop_id"].split(".")
            try:
                id_dict = json.loads(id_dict_str)
            except json.JSONDecodeError:
                print("interval_from_callback_context failed", p)
                continue
            if p["value"] is not None:
                id_dicts.append(id_dict)
        return "natl_reset_button" in [id_dict["type"] for id_dict in id_dicts]

    @app.callback(
        [Output(dict(type="natl_histograms"), "is_open")],
        [Input(dict(type="natl_toggle_button"), "n_clicks")],
        [State(dict(type="natl_histograms"), "is_open")]
    )
    def toggle_collapse(n, is_open):
        if n:
            return [not is_open]
        return [is_open]

    @app.callback(
        [Output(dict(type="rep_state_vote_lower_limit", state=MATCH), "value"),
         Output(dict(type="rep_state_vote_upper_limit", state=MATCH), "value")],
        [Input(dict(type="natl_reset_button"), "n_clicks"),
         Input(dict(type="state_vote_hist", state=MATCH), "selectedData"),
         Input(dict(type="dem_win_button", state=MATCH), "n_clicks"),
         Input(dict(type="rep_win_button", state=MATCH), "n_clicks"),
         Input(dict(type="reset_state_button", state=MATCH), "n_clicks")])
    def state_vote_select_update_labels(*args):
        context = dash.callback_context
        interval = interval_from_callback_context(
            context,
            ["state_vote_hist"],
            dict(
                dem_win_button=[0, 50], rep_win_button=[50.01, 100],
                reset_state_button=[0, 100], natl_reset_button=[0, 100]
            )
        )
        session_dict = get_session_dict()
        session_dict["reset_button_pressed"] = was_reset_button_pressed(context)
        set_session_dict(session_dict)
        if interval is not None:
            return np.floor(interval[0] * 100) / 100, np.ceil(interval[1] * 100) / 100
        else:
            return no_update_interval

    @app.callback(
        [Output(dict(type="rep_natl_vote_lower_limit"), "value"),
         Output(dict(type="rep_natl_vote_upper_limit"), "value")],
        [Input(dict(type="natl_reset_button"), "n_clicks"),
         Input(dict(type="natl_vote_hist"), "selectedData"),
         Input(dict(type="dem_natl_vote_win_button"), "n_clicks"),
         Input(dict(type="rep_natl_vote_win_button"), "n_clicks"),
         Input(dict(type="reset_natl_vote_button"), "n_clicks")])
    def natl_vote_select_update_labels(*args):
        context = dash.callback_context
        interval = interval_from_callback_context(
            context,
            ["natl_vote_hist"],
            dict(
                dem_natl_vote_win_button=[0, 50], rep_natl_vote_win_button=[50.01, 100],
                reset_natl_vote_button=[0, 100], natl_reset_button=[0, 100]
            )
        )
        session_dict = get_session_dict()
        session_dict["reset_button_pressed"] = was_reset_button_pressed(context)
        set_session_dict(session_dict)
        if interval is not None:
            return np.floor(interval[0] * 100) / 100, np.ceil(interval[1] * 100) / 100
        else:
            return no_update_interval

    @app.callback(
        [Output(dict(type="rep_ec_vote_lower_limit"), "value"),
         Output(dict(type="rep_ec_vote_upper_limit"), "value")],
        [Input(dict(type="natl_reset_button"), "n_clicks"),
         Input(dict(type="ec_vote_hist"), "selectedData"),
         Input(dict(type="dem_ec_vote_win_button"), "n_clicks"),
         Input(dict(type="rep_ec_vote_win_button"), "n_clicks"),
         Input(dict(type="reset_ec_vote_button"), "n_clicks")])
    def ec_vote_select_update_labels(*args):
        context = dash.callback_context
        interval = interval_from_callback_context(
            context,
            ["ec_vote_hist"],
            dict(
                dem_ec_vote_win_button=[0, 268], rep_ec_vote_win_button=[269, 538],
                reset_ec_vote_button=[0, 538], natl_reset_button=[0, 538]
            )
        )
        session_dict = get_session_dict()
        session_dict["reset_button_pressed"] = was_reset_button_pressed(context)
        set_session_dict(session_dict)
        if interval is not None:
            return np.floor(interval[0]), np.ceil(interval[1])
        else:
            return no_update_interval

    @app.callback(
        [Output(dict(type="rep_n_states_win_lower_limit"), "value"),
         Output(dict(type="rep_n_states_win_upper_limit"), "value")],
        [Input(dict(type="natl_reset_button"), "n_clicks"),
         Input(dict(type="n_states_win_hist"), "selectedData"),
         Input(dict(type="reset_n_states_win_button"), "n_clicks")])
    def n_states_win_select_update_labels(*args):
        context = dash.callback_context
        interval = interval_from_callback_context(
            context,
            ["n_states_win_hist"],
            dict(
                reset_n_states_win_button=[0, 51], natl_reset_button=[0, 51]
            )
        )
        session_dict = get_session_dict()
        session_dict["reset_button_pressed"] = was_reset_button_pressed(context)
        set_session_dict(session_dict)
        if interval is not None:
            return np.floor(interval[0]), np.ceil(interval[1])
        else:
            return no_update_interval

    @app.callback(
        Output(dict(type="states_control_block"), "children"),
        Input(dict(type="states_selector"), "value"))
    def state_selector_update(selected_states):
        session_dict = get_session_dict()
        data_model = session_dict["data_model"]
        for s in state_const.states:
            if s not in selected_states:
                data_model.add_state_vote_constraint(s, 0, 1)
        layout_builder = get_dash_layout_builder(session_dict)
        blocks = [layout_builder.get_state_block(s) for s in selected_states]
        set_session_dict(session_dict)
        return blocks

    @app.callback(
        [Output(dict(type="map_538"), "figure"),
         Output(dict(type="bar_538"), "figure"),
         Output(dict(type="summary"), "children"),

         Output(dict(type="state_vote_hist", state=ALL), "figure"),

         Output(dict(type="natl_vote_hist"), "figure"),
         Output(dict(type="ec_vote_hist"), "figure"),
         Output(dict(type="n_states_win_hist"), "figure")],
        [Input(dict(type="rep_state_vote_lower_limit", state=ALL), "value"),
         Input(dict(type="rep_state_vote_upper_limit", state=ALL), "value"),

         Input(dict(type="rep_natl_vote_lower_limit"), "value"),
         Input(dict(type="rep_natl_vote_upper_limit"), "value"),

         Input(dict(type="rep_ec_vote_lower_limit"), "value"),
         Input(dict(type="rep_ec_vote_upper_limit"), "value"),

         Input(dict(type="rep_n_states_win_lower_limit"), "value"),
         Input(dict(type="rep_n_states_win_upper_limit"), "value"),

         Input(dict(type="random_result_button"), "n_clicks"),
         Input(dict(type="average_result_button"), "n_clicks"),

         Input(dict(type="states_control_block"), "children")])
    def update_figure(*args):
        session_dict = get_session_dict()

        changed_props = dash.callback_context.triggered
        update_data_start_time = DateTime.now()
        data_model = session_dict["data_model"]

        if session_dict["reset_button_pressed"]:
            data_model.reset_data()
            session_dict["reset_button_pressed"] = False
            if session_dict["random_sample_mode"]:
                session_dict["random_sample_mode"] = False
                session_dict["new_average_538_map"] = True

        for p in changed_props:
            id_dict_str, value_str = p["prop_id"].split(".")
            try:
                id_dict = json.loads(id_dict_str)
            except json.JSONDecodeError:
                print("json error", p)
                continue

            print(id_dict)

            val = p["value"]
            if val is None:
                print("changed_prop value is None")
                continue

            if id_dict["type"] == "rep_state_vote_lower_limit":
                data_model.add_state_vote_constraint(id_dict["state"], f=float(val) / 100)
            elif id_dict["type"] == "rep_state_vote_upper_limit":
                data_model.add_state_vote_constraint(id_dict["state"], t=float(val) / 100)

            elif id_dict["type"] == "rep_natl_vote_lower_limit":
                data_model.add_natl_vote_constraint(f=float(val) / 100)
            elif id_dict["type"] == "rep_natl_vote_upper_limit":
                data_model.add_natl_vote_constraint(t=float(val) / 100)

            elif id_dict["type"] == "rep_ec_vote_lower_limit":
                data_model.add_ec_vote_constraint(f=float(val))
            elif id_dict["type"] == "rep_ec_vote_upper_limit":
                data_model.add_ec_vote_constraint(t=float(val))

            elif id_dict["type"] == "rep_n_states_win_lower_limit":
                data_model.add_states_win_constraint(f=float(val))
            elif id_dict["type"] == "rep_n_states_win_upper_limit":
                data_model.add_states_win_constraint(t=float(val))

            elif id_dict["type"] == "random_result_button":
                session_dict["new_random_538_map"] = True
                session_dict["random_sample_mode"] = True
                session_dict["random_data_sample"] = data_model.get_random_sample()
            elif id_dict["type"] == "average_result_button":
                session_dict["new_average_538_map"] = True
                session_dict["random_sample_mode"] = False

            elif id_dict["type"] == "states_control_block":
                # data updated was already handled in state_selector callback
                pass

            else:
                print("no match", id_dict)
                continue

        # if random data mode and data changed
        if data_model.data_changed and session_dict["random_sample_mode"]:
            session_dict["random_data_sample"] = data_model.get_random_sample()

        dash_payout_builder = get_dash_layout_builder(session_dict)
        print("data update took", DateTime.now() - update_data_start_time)
        update_figures_start_time = DateTime.now()
        output = [dash_payout_builder.get_output_item(outp) for outp in dash.callback_context.outputs_list]

        print("figures update took", DateTime.now() - update_figures_start_time)

        data_model.data_changed = False
        session_dict["new_random_538_map"] = False
        session_dict["new_average_538_map"] = False

        set_session_dict(session_dict)
        return output
