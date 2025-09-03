"""
Main layout definition for the MOO Dashboard
"""
import dash_bootstrap_components as dbc
from dash import dcc, html
from layouts.components import create_file_input_row, create_data_stores


def create_main_layout() -> html.Div:
    """
    Create the main layout for the MOO Dashboard.
    
    Returns:
        Dash HTML Div containing the complete layout
    """
    # File input components
    csv_file_input = create_file_input_row(
        'CSV File', 'csv', 
        'Load the CSV file from the given path and enter this button'
    )
    
    yaml_file_input = create_file_input_row(
        'YAML File', 'yaml',
        'Load the YAML file from the given path and enter this button'
    )
    
    # Configuration panel
    cfg_graph_input = dbc.Row([
        dbc.Col([
            dbc.Label("Channels to display:", className="fw-bold mb-2"),
            html.Div(id='channels', children=[
                dbc.Alert("Load YAML file to see variable options", color="info", className="text-center")
            ]),
        ]),
    ], className="mb-3")
    
    # Main layout
    layout = html.Div([
        dbc.Container([
            # File Loaders
            dbc.Row([
                dbc.Col(csv_file_input, width=12),
                dbc.Col(yaml_file_input, width=12)
            ], className="mt-4"),
            
            # Plot Renderers
            dbc.Row([
                dbc.Col(cfg_graph_input, width=4),
                dbc.Col(dcc.Graph(id='splom'), width=8)
            ], className="mt-4"),

            # Data Table
            dbc.Row([
                dbc.Col(dcc.Graph(id='data-table'), width=12)
            ])
        ]),
        # Data stores
        *create_data_stores()
    ])
    
    return layout
