import dash
from dash import html
from app.layouts.pypi_layout import get_pypi_layout
from app.services.pypi_client import get_pypi_details, get_total_packages, get_first_releases
from app.callbacks.pypi_callbacks import register_pypi_callbacks

layout = get_pypi_layout(get_pypi_details(), get_total_packages())
