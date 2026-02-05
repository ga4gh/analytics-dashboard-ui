from dash import Dash
import dash_bootstrap_components as dbc
from app.layouts.pypi_layout import get_pypi_layout
from app.callbacks.pypi_callbacks import register_pypi_callbacks
from app.services.pypi_client import get_all_packages, get_pypi_details, get_total_packages
from app.normalizers.pypi_normalizer import normalize_pypi_packages

def create_app():
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    all_packages = get_all_packages()
    pypi_version_details = get_pypi_details()
    total_packages = get_total_packages()
    
    app.layout = get_pypi_layout(pypi_version_details, total_packages)
    register_pypi_callbacks(app, pypi_version_details)

    return app

app = create_app()
server = app.server
