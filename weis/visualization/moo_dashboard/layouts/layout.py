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
    cfg_graph_input = dbc.Col([
            # dbc.Label("Channels to display:", className="fw-bold mb-2"),
            html.Div(
                id='channels', 
                children=[
                    dbc.Alert("Load YAML file to see variable options", color="info", className="text-center")
                ],
                style={
                    'maxHeight': 'calc(100% - 100px)',
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
        ], style={'height': '100%'})
    
    # Simple layout with full width
    layout = html.Div([
        # File Loaders - Full width
        dbc.Row([
            dbc.Col(csv_file_input, width=12),
        ], className="g-0"),
        dbc.Row([
            dbc.Col(yaml_file_input, width=12),
        ], className="g-0 mb-3"),
        
        # Main content - 2x2 grid layout
        # Left column: cfg_graph_input on top, data-table on bottom
        # Right column: splom spanning both rows (square aspect ratio)
        html.Div([
            # Left column with two stacked components
            html.Div([
                # Top left: cfg_graph_input
                html.Div(
                    cfg_graph_input,
                    style={
                        'height': '50%', 
                        'overflowY': 'auto',
                        'overflowX': 'hidden'
                    }
                ),
                # Bottom left: data-table (aligned with cfg_graph_input border)
                html.Div(
                    dcc.Graph(
                        id='data-table', 
                        style={'height': '100%'},
                        config={'responsive': True}
                    ),
                    style={
                        'height': '50%'
                    }
                )
            ], style={
                'width': '33%',
                'height': 'calc(100vh - 200px)',  # Dynamic height based on viewport
                'display': 'inline-block',
                'verticalAlign': 'top',
                'paddingRight': '10px',
                'boxSizing': 'border-box'
            }),
            # Right column: splom graph spanning full height with square aspect ratio
            html.Div(
                dcc.Graph(
                    id='splom', 
                    style={'height': '100%', 'width': '100%'},
                    config={'responsive': True}
                ),
                style={
                    'width': 'calc(min(67vw - 40px, 100vh - 200px))',  # Square: min of width and height
                    'height': 'calc(min(67vw - 40px, 100vh - 200px))',
                    'display': 'inline-block',
                    'verticalAlign': 'top',
                    'maxWidth': '67%'
                }
            )
        ], style={
            'width': '100%',
            'whiteSpace': 'nowrap'
        }),
        
        # Data stores
        *create_data_stores()
    ], style={
        'width': '100%',
        'maxWidth': '100%',
        'margin': '0',
        'padding': '15px',
        'boxSizing': 'border-box'
    })
    
    return layout
