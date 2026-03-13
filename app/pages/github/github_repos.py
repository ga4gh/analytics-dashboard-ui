import dash
from dash import html
from app.layouts.github_layout import get_github_layout
dash.register_page(__name__, path="/github/github_repos", name="GitHub Repos Graph")

def layout():
    pass