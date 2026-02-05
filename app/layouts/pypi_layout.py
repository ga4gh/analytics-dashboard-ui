from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

def get_pypi_layout(pypi_details, total_packages):
    
    return dbc.Container(
        [
            html.H2(
                f"Total PyPI Packages: {total_packages}",
                style={'textAlign': 'center', 'margin-bottom': '20px', 'color': "#9DAAB8"}
            ),
            
            # Search box for global search - filters across all columns
            dcc.Input(
                id='table-search',
                type='text',
                placeholder='Search projects...',
                debounce=False,   # keystroke-based search (change to True for enter-based search)
                style={
                    'margin-bottom': '15px',
                    'width': '350px',
                    'padding': '8px',
                    'border-radius': '5px',
                    'border': '1px solid #ccc'
                }
            ),

            # Interactive DataTable
            dash_table.DataTable(
                id='projects-table',
                columns=[{"name": i, "id": i} for i in pypi_details.reset_index().columns],

                data=pypi_details.reset_index().to_dict('records'),
                page_size=10,
                sort_action='native', # enable sorting by column
                filter_action='native',  # native per-column filter

                # Styling options
                style_table={'overflowX': 'auto', 'border': '1px solid #ccc', 'border-radius': '5px'},
                style_header={'backgroundColor': '#34495E', 'color': 'white', 'fontWeight': 'bold'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px',
                    'minWidth': '100px', 'width': '150px', 'maxWidth': '250px',
                    'whiteSpace': 'nowrap',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'border-bottom': '1px solid #ddd'
                },
                style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}]
            ),

            # Graphs
            dcc.Graph(id='datatable-bar'),
            dcc.Graph(id='category-distribution')
        ],
        fluid=True,
    )
