from flask import Flask, session
import dash
import dash_bootstrap_components as dbc
from app.dash_callbacks import set_app_callbacks
from app.dash_layout import DashLayout
from app.config import SessionConfig
from data_model import DataModel
from flask_session import Session
from state_const import states
import pandas as pd


class DashAppWrapper(dash.Dash):
    def index(self, *args, **kwargs):
        print("index", session.keys(), "clear")
        session.clear()
        return super().index(*args, **kwargs)


def build_server():
    server = Flask(__name__)
    server.config.from_object(SessionConfig)
    Session(server)

    app = DashAppWrapper(
        __name__,
        server=server,
        external_stylesheets=[dbc.themes.BOOTSTRAP]
    )

    empty_data = pd.DataFrame(columns=states+["natl_pop_vote", "dem_ec"])
    app.layout = DashLayout(DataModel(empty_data)).get_layout()
    set_app_callbacks(app)
    return server
