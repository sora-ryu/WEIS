"""
Reusable UI components for the MOO Dashboard
"""
import dash_bootstrap_components as dbc
from dash import dcc, html
from config.settings import COLOR_SCALES


def create_file_input_row(file_type: str, file_id_prefix: str, tooltip_text: str) -> dbc.Row:
    """
    Create a reusable file input row for CSV or YAML files.
    
    Args:
        file_type: Display name for the file type (e.g., 'CSV File', 'YAML File')
        file_id_prefix: Prefix for component IDs (e.g., 'csv', 'yaml')
        tooltip_text: Tooltip text for the load button
        
    Returns:
        Dash Bootstrap Components Row
    """
    return dbc.Row([
        dbc.Col(
            dbc.Label(file_type, className="mb-0"), 
            width=1, 
            className="d-flex align-items-center"  # Vertically center label
        ),
        dbc.Col(
            dbc.Input(
                id=f'{file_id_prefix}-file-path',
                type='text',
                placeholder='Enter the absolute path for file to import'
            ),
            width=True  # Takes remaining space
        ),
        dbc.Col(
            dcc.Upload(
                id=f'{file_id_prefix}-upload-data',
                children=dbc.Button('Browse', n_clicks=0, color='secondary', className='me-1'),
                multiple=False
            ),
            width="auto"  # Only as wide as needed
        ),
        dbc.Col(
            dbc.Button('Load', id=f'{file_id_prefix}-load-btn', n_clicks=0, color='primary'),
            width="auto"  # Only as wide as needed
        ),
        dbc.Tooltip(tooltip_text, target=f'{file_id_prefix}-load-btn'),
    ], className="mb-3 g-2")  # g-2 adds small gutters between columns


def create_button_group(variables: list, category_name: str, color: str, selected_vars: list, array_columns: set = None) -> list:
    """
    Create a button group for variable selection.
    
    Args:
        variables: List of variable names
        category_name: Display name for the category
        color: Bootstrap color for the buttons
        selected_vars: List of currently selected variables
        array_columns: Set of column names that contain arrays
        
    Returns:
        List of HTML components
    """
    if not variables:
        return []
    
    array_columns = array_columns or set()
    all_components = []
    
    for var in variables:
        is_array = var in array_columns
        
        # Check if any form of this variable is selected
        is_selected = (var in selected_vars or 
                      f"{var}_min" in selected_vars or 
                      f"{var}_max" in selected_vars)
        
        # For regular variables, create normal button
        if not is_array:
            button = dbc.Button(
                var,
                id={'type': 'channel-btn', 'index': var},
                color=color,
                outline=not is_selected,
                size='sm',
                className='flex-shrink-0',  # Prevent button from shrinking
                style={'marginRight': '0.25rem', 'marginBottom': '0.25rem'},
                n_clicks=0,
            )
            all_components.append(button)
        else:
            # For array variables, create button that automatically uses separate mode
            button = dbc.Button(
                f"{var} (min/max)",
                id={'type': 'array-channel-btn', 'index': var},
                color=color,
                outline=not is_selected,
                size='sm',
                className='flex-shrink-0',
                style={'marginRight': '0.25rem', 'marginBottom': '0.25rem'},
                n_clicks=0,
            )
            
            all_components.append(button)
    
    return [
        html.Div([
            html.Small(category_name, className="text-muted fw-bold mb-2 d-block"),
            html.Div(
                all_components,
                className="d-flex flex-wrap gap-1"  # Responsive wrapping with gap
            )
        ], className="mb-3")
    ]


def create_data_stores() -> list:
    """
    Create dcc.Store components for data persistence.
    
    Returns:
        List of dcc.Store components
    """
    return [
        dcc.Store(id='csv-df'),
        dcc.Store(id='yaml-df'),
        dcc.Store(id='selected-channels', data=[]),
        dcc.Store(id='selected-iteration', data=""),  # Store for selected iteration (highlight)
        dcc.Store(id='pareto-front-enabled', data=False)  # Store for Pareto front toggle
    ]


def create_no_data_alert(message: str, color: str = "info") -> dbc.Alert:
    """
    Create a standardized alert for no data scenarios.
    
    Args:
        message: Alert message
        color: Bootstrap color for the alert
        
    Returns:
        Dash Bootstrap Alert component
    """
    return dbc.Alert(message, color=color, className="text-center")
