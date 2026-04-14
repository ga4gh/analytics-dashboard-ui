import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_indicators(pm_df, gh_df, pypi_df,
                    pm_last_year, gh_last_year, pypi_last_year):

    fig = make_subplots(
        rows=1,
        cols=3,
        specs=[[{"type": "indicator"},
                {"type": "indicator"},
                {"type": "indicator"}]],
        horizontal_spacing=0.08
    )

    # PyPI
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=pypi_df.shape[0],
            title={"text": "PyPI Packages"},
            delta={"reference": pypi_df.shape[0] - len(pypi_last_year)}
        ),
        row=1, col=1
    )

    # GitHub
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=gh_df.shape[0],
            title={"text": "GitHub Repositories"},
            delta={"reference": gh_df.shape[0] - len(gh_last_year)}
        ),
        row=1, col=2
    )
    
    # PubMed
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=pm_df.shape[0],
            title={"text": "PubMed Articles"},
            delta={"reference": pm_df.shape[0] - len(pm_last_year)}
        ),
        row=1, col=3
    )

    fig.update_layout(
        title={
            "text": "Total GA4GH Data Points Per Source (with 2025 Increases)",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24}
        },
        margin=dict(l=20, r=20, t=70, b=20),
        height=300
    )

    return fig