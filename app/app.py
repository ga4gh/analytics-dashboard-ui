from dash import Dash
import dash_bootstrap_components as dbc
from dash import html, page_container
from app.callbacks.pypi_callbacks import register_pypi_callbacks
from app.callbacks.github_callbacks import register_github_callbacks
from app.callbacks.home_callbacks import register_home_callbacks

def create_app():
    app = Dash(__name__,
               use_pages=True, 
               suppress_callback_exceptions=True,
               external_stylesheets=[dbc.themes.BOOTSTRAP],
               health_endpoint="/health",
               title="GA4GH Analytics Dashboard",
               description="Welcome to the GA4GH Analytics Dashboard")
    
    app.layout = html.Div([
        page_container
    ])
    
    register_home_callbacks(app)
    register_pypi_callbacks(app)
    register_github_callbacks(app)
    
    return app

app = create_app()
server = app.server
