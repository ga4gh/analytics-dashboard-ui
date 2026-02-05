from dash import Input, Output
import pandas as pd
import plotly.express as px

def register_pypi_callbacks(app, df):

    # -----------------------
    # Search box filtering
    # -----------------------
    @app.callback(
        Output('projects-table', 'data'),
        Input('table-search', 'value')
    )
    def update_table(search_value):
        """
        Filters the DataFrame rows based on the search input.
        Runs on every keystroke unless debounce=True.
        """
        if not search_value:
            return df.reset_index().to_dict('records')
        filtered = df.reset_index()[df.reset_index().apply(
            lambda row: row.astype(str).str.contains(search_value, case=True).any(), axis=1
        )]
        return filtered.to_dict('records')

    # -----------------------
    # Update bar chart
    # -----------------------
    @app.callback(
        Output("datatable-bar", "figure"),
        Input("projects-table", "derived_virtual_data"),
        Input("projects-table", "page_current"),
        Input("projects-table", "page_size")
    )
    def update_bar(rows, page_current, page_size):
        # If DataTable rows exist, use them; else fallback to original DataFrame
        dff = pd.DataFrame(rows) if rows else df.copy()

        # If "project_name" missing, rename index
        if "project_name" not in dff.columns:
            if "index" in dff.columns:
                dff = dff.rename(columns={"index": "project_name"})

        # Provide safe defaults for paging
        page_current = page_current or 0
        page_size = page_size or 10

        # Slice the data for the current page
        start = page_current * page_size
        end = start + page_size
        page_data = dff.iloc[start:end]

        # Create hover text: shorten long description
        hover_texts = [
            f"<b>{row['project_name']}</b><br>"
            f"Category: {row.get('category', '')}<br>"
            f"Versions: {str(row.get('versions_count', ''))}"
            for _, row in page_data.iterrows()
        ]

        fig = {
            "data": [
                {
                    "x": page_data["project_name"],      # X-axis: package names
                    "y": page_data["versions_count"],    # Y-axis: version counts
                    "type": "bar",                       # Bar chart
                    "marker": {"color": "#2E86C1"},    # Bar color
                    "hovertext": hover_texts,            # Custom hover info
                    "hoverinfo": "text"                  # Only show hover text
                }
            ],
            "layout": {
                "title": {
                    "text": "Package Versions Count (Current Page)",
                    "x": 0.5,          # center title
                    "xanchor": "center",
                    "yanchor": "top",
                    "font": {"size": 20, "color": "#2C3E50"}
                },
                "xaxis": {"title": "project_name", "tickangle": -45},
                "yaxis": {"title": "versions_count"},
                "plot_bgcolor": "#f9f9f9",
                "paper_bgcolor": "#ffffff",
                "margin": {"b": 120}
            }
        }
        return fig


    # -----------------------
    # Update category pie chart
    # -----------------------
    @app.callback(
        Output("category-distribution", "figure"),
        Input("projects-table", "derived_virtual_data")
    )
    def update_category_distribution(rows):
        dff = pd.DataFrame(rows) if rows is not None else df.reset_index()

        if "category" not in dff.columns or dff.empty:
            return {"data": [], "layout": {"title": "No category data available"}}

        # Count categories
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
                "title": {
                    "text": "Category Distribution",
                    "x": 0.5,          # center title
                    "xanchor": "center",
                    "yanchor": "top",
                    "font": {"size": 20, "color": "#2C3E50"}
                },
                "plot_bgcolor": "#f9f9f9",
                "paper_bgcolor": "#ffffff"
            }
        }
        return fig
