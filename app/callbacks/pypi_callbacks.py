from dash import Input, Output
import pandas as pd
import plotly.express as px

from app.services.pypi_client import get_pypi_details
import dash_bootstrap_components as dbc
from dash import html, dcc

from app.utils.ga4gh_theme import PYPI_COLORWAY, COLORS


PYPI_CATEGORY_COLORS = {
    "Implementation": PYPI_COLORWAY[0],
    "GA4GH Standard": PYPI_COLORWAY[1],
    "GA4GH mentions": PYPI_COLORWAY[2],
}

def register_pypi_callbacks(app):

    # Cache PyPI data once at registration time
    _pypi_df = get_pypi_details()

    # -----------------------
    # DataTable search (unchanged)
    # -----------------------
    @app.callback(
        Output('projects-table', 'data'),
        Input('table-search', 'value')
    )
    def update_table(search_value):
        df = _pypi_df
        if not search_value:
            return df.reset_index().to_dict('records')
        indexed = df.reset_index()
        mask = indexed.apply(
            lambda col: col.astype(str).str.contains(search_value, case=False, na=False)
        ).any(axis=1)
        return indexed[mask].to_dict('records')

    # -----------------------
    # Update bar chart based on filters
    # -----------------------
    @app.callback(
        Output("datatable-bar", "figure"),
        Output("datatable-bar-title", "children"),
        Input("filter-author", "value"),
        Input("filter-email", "value"),
        Input("filter-category", "value"),
        Input("top-n-slider", "value")
    )
    def update_bar(author_filter, email_filter, category_filter, top_n):
        df = _pypi_df
        dff = df.copy()

        # Apply filters
        if author_filter:
            dff = dff[dff["author_name"].isin(author_filter)]
        if email_filter:
            dff = dff[dff["author_email"].isin(email_filter)]
        if category_filter:
            dff = dff[dff["category"].isin(category_filter)]

        # Take top N packages by version count
        dff = dff.nlargest(top_n, "versions_count")

        # Assign colors automatically by category
        fig = px.bar(
            dff,
            x="project_name",
            y="versions_count",
            color="category",
            hover_data=["project_name", "category", "versions_count"],
            color_discrete_map=PYPI_CATEGORY_COLORS,
            category_orders={
                "project_name": dff["project_name"].tolist()  # 👈 THIS FIXES IT
            }
        )

        # Customize layout
        fig.update_layout(
            xaxis={"title": "Project Name", "tickangle": -45, "automargin": True},
            yaxis={"title": "Versions Count", "showgrid": True, "gridcolor": COLORS["lightgrey"]},
            plot_bgcolor=COLORS["white"],
            paper_bgcolor=COLORS["white"],
            margin={"t": 20, "b": 300},
            legend={
                # px.bar auto-titles the legend from the color= column name
                # ("category") — an explicit "" overrides that default,
                # merely omitting a "title" key here does not.
                "title": {"text": ""},
                "orientation": "h",
                "yanchor": "top",
                "y": -0.55,
                "xanchor": "center",
                "x": 0.5,
            },
            hoverlabel={"font": {"color": "white"}},
        )

        return fig, f"Top {top_n} Package Versions Count"

    # -----------------------
    # Update pie chart based on filters
    # -----------------------
    @app.callback(
        Output("category-distribution", "figure"),
        Input("filter-author", "value"),
        Input("filter-email", "value"),
        Input("filter-category", "value")
    )
    def update_category_distribution(author_filter, email_filter, category_filter):
        df = _pypi_df
        dff = df.copy()

        # Apply filters
        if author_filter:
            dff = dff[dff["author_name"].isin(author_filter)]
        if email_filter:
            dff = dff[dff["author_email"].isin(email_filter)]
        if category_filter:
            dff = dff[dff["category"].isin(category_filter)]

        if dff.empty:
            return {"data": [], "layout": {"title": "No category data available"}}

        cat_counts = dff["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]

        fig = {
            "data": [{
                "labels": cat_counts["category"],
                "values": cat_counts["count"],
                "type": "pie",
                "hole": 1/3,
                "textinfo": "label+percent",
                # Without this, Plotly's default "auto" placement can push
                # a thin slice's label outside the pie, which combined with
                # the template's automargin:true shrinks the pie itself to
                # make room — exactly what broke the mobile auto-fit's
                # width assumption in assets/pie_autofit.js (it sizes the
                # pie to fill the card's width exactly, which only holds if
                # automargin never kicks in). Matches the other pies.
                "textposition": "inside",
                "textfont": {"color": "white"},
                "hoverinfo": "label+value+percent",
                "marker": {
                    "colors": [
                        PYPI_CATEGORY_COLORS.get(cat, COLORS["grey"])
                        for cat in cat_counts["category"]
                    ]
                },
            }],
            "layout": {
                "plot_bgcolor": COLORS["white"],
                "paper_bgcolor": COLORS["white"],
                "legend": {"orientation": "h", "yanchor": "top", "y": -0.1, "xanchor": "center", "x": 0.5},
                # autosize (not a fixed height) — paired with config={"responsive":
                # True} on the dcc.Graph and .chart-aspect-tall in style.css so this
                # scales with the card's actual width at any viewport.
                "autosize": True,
                "hoverlabel": {"font": {"color": "white"}},
            }
        }
        return fig
    
    @app.callback(
        Output("pypi-project-details", "children"),
        Input("projects-table", "selected_rows")
    )
    def show_project_details(selected_rows):

        if not selected_rows:
            return dbc.Alert("Select a project to see details", color="info")
        pypi_details = _pypi_df
        project = pypi_details.iloc[selected_rows[0]]
        github_url = project.get("github_url")
        versions_count = project.get("versions_count")

        return dbc.Card([

            dbc.CardHeader(html.H4(project["project_name"])),

            dbc.CardBody([

                html.P(project.get("description", "No description available")),

                html.Hr(),

                html.P(f"Category: {project.get('category','N/A')}"),
                html.P(f"Author: {project.get('author_name','N/A')}"),
                html.P(f"Email: {project.get('author_email','N/A')}"),
                html.P(f"Versions Published: {versions_count}"),

                html.Br(),

                html.Div([
                    dbc.Button(
                        html.Span("View on PyPI", className="btn-text"),
                        href=project.get("package_url"),
                        target="_blank",
                        className="ga4gh-btn-dark",
                        disabled=not project.get("package_url"),
                    ),

                    dbc.Button(
                        html.Span("Latest Release", className="btn-text"),
                        href=project.get("release_url"),
                        target="_blank",
                        className="ga4gh-btn-dark",
                        disabled=not project.get("release_url"),
                    ),

                    dbc.Button(
                        html.Span("View on GitHub", className="btn-text"),
                        href=github_url,
                        target="_blank",
                        className="ga4gh-btn-dark",
                        disabled=not github_url,
                    ),
                ], className="pypi-details-buttons")

            ])

        ], style={"boxShadow": "0 4px 10px rgba(0,0,0,0.1)"})
        
    