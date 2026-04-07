from dash import dash, Input, Output
import pandas as pd
import plotly.express as px

from app import app
from app.services.pypi_client import get_pypi_details
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc, dash_table
import pandas as pd
from app.pages.pypi.pypi import layout as pypi_layout
from app.pages.github.github import layout as github_layout

from dash import ctx
from app.layouts.pypi_layout import get_pypi_layout
from app.services.pypi_client import get_pypi_details, get_total_packages

from app.layouts.github_layout import get_github_layout
from app.services.github_client import prepare_github_data

from app.layouts.epmc_layout import get_epmc_layout
from app.services.epmc_client import prepare_epmc_data

def register_home_callbacks(app):

    @app.callback(
        Output("module-content", "children"),
        Output("open-pypi", "children"),
        Output("open-github", "children"),
        Output("open-epmc", "children"),
        Input("open-pypi", "n_clicks"),
        Input("open-github", "n_clicks"),
        Input("open-epmc", "n_clicks"),
        prevent_initial_call=True
    )
    def display_module(pypi_click, github_click, epmc_click):

        trigger = ctx.triggered_id

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        # Default button text
        pypi_text = "Open"
        github_text = "Open"
        epmc_text = "Open"
        
        if trigger == "open-pypi":
            content = get_pypi_layout(
                get_pypi_details(),
                get_total_packages()
            )
            pypi_text = "Close"

        elif trigger == "open-github":
            content = get_github_layout(
                prepare_github_data()[0],  # gh_df
                prepare_github_data()[4],   # total_repositories,
                prepare_github_data()[5]   # workstreams
            )
            github_text = "Close"

        elif trigger == "open-epmc":
            epmc_data = prepare_epmc_data()
            content = get_epmc_layout(
                epmc_data[0],  # entries_df
                epmc_data[1],  # countries_df
                epmc_data[2],  # authors_df
                epmc_data[3],  # total_entries,
                epmc_data[4],  # citations
            )
            epmc_text = "Close"
        
        return content, pypi_text, github_text, epmc_text