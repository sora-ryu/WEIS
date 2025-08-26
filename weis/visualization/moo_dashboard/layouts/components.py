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
        dbc.Label(file_type, width=1),
        dbc.Col(
            dbc.Input(
                id=f'{file_id_prefix}-file-path',
                type='text',
                placeholder='Enter the absolute path for file to import'
            ),
            width=6
        ),
        dbc.Col(
            dcc.Upload(
                id=f'{file_id_prefix}-upload-data',
                children=dbc.Button('Browse', n_clicks=0, color='secondary', className='me-1'),
                multiple=False
            ),
            width='auto'
        ),
        dbc.Col(
            dbc.Button('Load', id=f'{file_id_prefix}-load-btn', n_clicks=0, color='primary'),
            width='auto'
        ),
        dbc.Tooltip(tooltip_text, target=f'{file_id_prefix}-load-btn'),
    ], className="mb-3")


def create_button_group(variables: list, category_name: str, color: str, selected_vars: list) -> list:
    """
    Create a button group for variable selection.
    
    Args:
        variables: List of variable names
        category_name: Display name for the category
        color: Bootstrap color for the buttons
        selected_vars: List of currently selected variables
        
    Returns:
        List of HTML components
    """
    if not variables:
        return []
    
    buttons = []
    for var in variables:
        is_selected = (var in selected_vars)
        buttons.append(
            dbc.Button(
                var,
                id={'type': 'channel-btn', 'index': var},
                color=color,
                outline=not is_selected,
                size='sm',
                className='me-1 mb-1'
            )
        )
    
    return [
        html.Div([
            html.Small(category_name, className="text-muted fw-bold"),
            html.Div(buttons, className="d-flex flex-wrap")
        ], className="mb-2")
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
        dcc.Store(id='selected-channels', data=[])
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
