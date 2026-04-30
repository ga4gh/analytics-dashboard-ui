from dash import Input, Output, State, ctx
from dash import html
from app.services.pypi_client import get_pypi_details, get_total_packages
import dash_bootstrap_components as dbc

from app.layouts.pypi_layout import get_pypi_layout

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
            gh_data = prepare_github_data()
            content = get_github_layout(
                gh_data[0],  # gh_df
                gh_data[4],  # total_repositories,
                gh_data[5]   # workstreams
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

    @app.callback(
        Output("collapse", "is_open"),
        Output("collapse-button", "children"),
        Input("collapse-button", "n_clicks"),
        State("collapse", "is_open"),
    )
    def toggle_collapse(n, is_open):
        new_state = not is_open if n else is_open

        label = [
            html.Span("▼ " if new_state else "▶ ", style={"fontSize": "12px", "marginRight": "4px"}),
            html.Span("Show methods and terms "),
            html.Span("▼", style={"fontSize": "12px"}),
        ]

        return new_state, label