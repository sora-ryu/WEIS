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
            html.Div(
                id='channels', 
                children=[
                    dbc.Alert("Load YAML file to see variable options", color="info", className="text-center")
                ],
                style={
                    'maxHeight': '70vh',
                    'overflowY': 'auto',
                    'padding': '10px',
                    'border': '1px solid #dee2e6',
                    'borderRadius': '0.375rem',
                    'backgroundColor': '#f8f9fa'
                }
            ),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Clear Highlighting", 
                        id='clear-highlight-btn', 
                        color='secondary', 
                        outline=True, 
                        size='sm',
                        className='mb-2 me-2'
                    ),
                    dbc.Button(
                        "Show Pareto Front", 
                        id='pareto-toggle-btn', 
                        color='success', 
                        outline=True, 
                        size='sm',
                        className='mb-2'
                    )
                ])
            ])
        ]),
    ])
    
    # Simple layout with full width
    layout = html.Div([
        # File Loaders - Full width
        dbc.Row([
            dbc.Col(csv_file_input, width=12),
            dbc.Col(yaml_file_input, width=12)
        ], className="mt-4", style={'margin': '0', 'padding': '0 15px'}),
        
        # Main content - Channel panel (1/3) + Plot (2/3)
        dbc.Row([
            dbc.Col([
                # From same column, stack vertically.
                dbc.Row(cfg_graph_input),  # 1/3 of width
                dbc.Row(dcc.Graph(id='data-table'))
            ], width=4),
            dbc.Col(dcc.Graph(id='splom'), width=8)  # 2/3 of width
        ], className="mt-4", style={'margin': '0', 'padding': '0 15px'}),

        # # Data Table - Full width
        # dbc.Row([
        #     dbc.Col(dcc.Graph(id='data-table'), width=12)
        # ], className="mt-4", style={'margin': '0', 'padding': '0 15px'}),
        
        # Data stores
        *create_data_stores()
    ], style={'width': '100%', 'margin': '0', 'padding': '0'})
    
    return layout
