from dash import Input, Output
import pandas as pd
import plotly.express as px

from app.services.pypi_client import get_pypi_details
import dash_bootstrap_components as dbc
from dash import html, dcc

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
            color_discrete_sequence=px.colors.qualitative.Safe,
            category_orders={
                "project_name": dff["project_name"].tolist()  # 👈 THIS FIXES IT
            }
        )

        # Customize layout
        fig.update_layout(
            title={
                "text": f"Top {top_n} Package Versions Count",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": "#2C3E50"}
            },
            xaxis={"title": "Project Name", "tickangle": -45},
            yaxis={"title": "Versions Count"},
            plot_bgcolor="#f9f9f9",
            paper_bgcolor="#ffffff",
            margin={"b": 120},
            legend={
                "title": "Category",
                "orientation": "v",  # vertical
                "yanchor": "top",
                "y": 1,
                "xanchor": "right",
                "x": 1.02,
                "bordercolor": "#ccc",
                "borderwidth": 1
            }
        )

        return fig

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
                "hole": 0.4,
                "textinfo": "label+percent",
                "hoverinfo": "label+value+percent"
            }],
            "layout": {
                "title": {"text": "Category Distribution", "x": 0.5, "xanchor": "center", "font": {"size": 20, "color": "#2C3E50"}},
                "plot_bgcolor": "#f9f9f9",
                "paper_bgcolor": "#ffffff"
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

                dbc.Button(
                    "View on PyPI",
                    href=project.get("package_url"),
                    target="_blank",
                    color="primary",
                    className="me-2"
                ),

                dbc.Button(
                    "Latest Release",
                    href=project.get("release_url"),
                    target="_blank",
                    color="secondary",
                    className="me-2"
                ),

                dbc.Button(
                    "View on GitHub",
                    href=github_url,
                    target="_blank",
                    color="dark",
                    className="me-2",
                    disabled=not github_url
                )

            ])

        ], style={"boxShadow": "0 4px 10px rgba(0,0,0,0.1)"})
        
    