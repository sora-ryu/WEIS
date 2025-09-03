"""
Plot helpers and formatting utilities
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List
from config.settings import (
    DEFAULT_PLOT_WIDTH, DEFAULT_PLOT_HEIGHT, MARKER_SIZE, MARKER_LINE_WIDTH,
    BASE_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE, BASE_MARGIN, MAX_MARGIN,
    HIGHLIGHT_COLOR, HIGHLIGHT_SIZE_MULTIPLIER, HIGHLIGHT_OPACITY, 
    NON_HIGHLIGHT_OPACITY, HIGHLIGHT_LINE_WIDTH
)
import math


def calculate_font_size(num_vars: int, plot_width: int = DEFAULT_PLOT_WIDTH) -> int:
    """
    Calculate optimal font size based on number of variables and plot width.
    
    Args:
        num_vars: Number of variables in the SPLOM
        plot_width: Width of the plot
        
    Returns:
        Optimal font size for axis labels
    """
    # Calculate space available per subplot
    subplot_width = plot_width / num_vars
    
    # Adjust font size based on available space
    if subplot_width < 100:
        font_size = max(MIN_FONT_SIZE, int(BASE_FONT_SIZE * 0.5))
    elif subplot_width < 150:
        font_size = max(MIN_FONT_SIZE + 2, int(BASE_FONT_SIZE * 0.7))
    elif subplot_width < 200:
        font_size = max(MIN_FONT_SIZE + 4, int(BASE_FONT_SIZE * 0.85))
    else:
        font_size = BASE_FONT_SIZE
    
    return min(font_size, MAX_FONT_SIZE)


def truncate_labels(dimensions: List[str], max_length: int = 15) -> List[str]:
    """
    Intelligently truncate long variable names for better display.
    
    Args:
        dimensions: List of dimension names
        max_length: Maximum length for labels
        
    Returns:
        List of truncated dimension names
    """
    truncated = []
    for dim in dimensions:
        if len(dim) <= max_length:
            truncated.append(dim)
        else:
            # Try to keep meaningful parts
            if '_' in dim:
                # Split by underscore and take first and last parts
                parts = dim.split('_')
                if len(parts) >= 2:
                    truncated_name = f"{parts[0]}_{parts[-1]}"
                    if len(truncated_name) <= max_length:
                        truncated.append(truncated_name)
                    else:
                        truncated.append(dim[:max_length-2] + "..")
                else:
                    truncated.append(dim[:max_length-2] + "..")
            else:
                # Simple truncation with ellipsis
                truncated.append(dim[:max_length-2] + "..")
    
    return truncated


def calculate_margin_size(num_vars: int, font_size: int) -> int:
    """
    Calculate optimal margin size based on number of variables and font size.
    
    Args:
        num_vars: Number of variables in the SPLOM
        font_size: Font size being used
        
    Returns:
        Optimal margin size
    """
    # Increase margin for smaller fonts and more variables
    if num_vars > 6:
        margin = BASE_MARGIN + (font_size * 2)
    elif num_vars > 4:
        margin = BASE_MARGIN + font_size
    else:
        margin = BASE_MARGIN
    
    return min(margin, MAX_MARGIN)


def create_splom_figure(df: pd.DataFrame, dimensions: List[str], num_vars: int, highlighted_iteration: int = None):
    """
    Create a scatter plot matrix (SPLOM) with color-coded samples and auto-sized labels.
    Uses plotly.graph_objects for better control of marker properties and highlighting.
    
    Args:
        df: DataFrame with simplified column names and sample_id
        dimensions: List of dimension names for the SPLOM
        num_vars: Number of variables for title
        highlighted_iteration: Optional iteration to highlight across all subplots

    Returns:
        Plotly figure with SPLOM
    """
    if df.empty or not dimensions:
        return go.Figure()

    # Prepare data for SPLOM
    n_vars = num_vars
    n_samples = len(df)
        
    # Create color array based on iteration index
    colors = np.arange(n_samples) / max(1, n_samples - 1)
    
    # Create text labels
    text_labels = [f"Iteration {i}" for i in range(n_samples)]

    # Create main SPLOM trace with normal points
    splom_trace = go.Splom(
        dimensions=dimensions,
        text=text_labels,
        marker=dict(
            color=colors,
            colorscale='Viridis',
            size=8,
            symbol='circle',
            line=dict(
                color='white',
                width=0.5
            ),
            opacity=1.0 if highlighted_iteration is None else NON_HIGHLIGHT_OPACITY
        ),
        diagonal_visible=True,
        showupperhalf=True,
        showlowerhalf=False,
        name="Data Points",
        showlegend=False
    )
    
    traces = [splom_trace]
    
    # Add highlighted trace on top if highlighting is needed
    if highlighted_iteration is not None and highlighted_iteration < n_samples:
        # Create dimensions for highlighted point
        highlighted_dimensions = []
        for dim_dict in dimensions:
            dim_label = dim_dict['label']
            dim_values = dim_dict['values']
            
            # Extract the value for the highlighted iteration
            highlighted_value = dim_values[highlighted_iteration]
            
            highlighted_dimensions.append(dict(
                label=dim_label,
                values=[highlighted_value]  # Single value as list
            ))
        
        # Create highlighted trace (rendered on top)
        highlighted_trace = go.Splom(
            dimensions=highlighted_dimensions,
            text=[f"Iteration {highlighted_iteration} (Selected)"],
            marker=dict(
                color=HIGHLIGHT_COLOR,
                size=MARKER_SIZE * HIGHLIGHT_SIZE_MULTIPLIER,
                symbol='circle',
                line=dict(
                    color=HIGHLIGHT_COLOR,
                    width=HIGHLIGHT_LINE_WIDTH
                ),
                opacity=HIGHLIGHT_OPACITY
            ),
            diagonal_visible=True,
            showupperhalf=True,
            showlowerhalf=False,
            name="Highlighted Point",
            showlegend=False
        )
        
        traces.append(highlighted_trace)

    fig = go.Figure(data=traces)

    # Update layout
    fig.update_layout(
        title=f"Scatterplot Matrix (SPLOM) - {n_vars} Variables × {n_samples} Iterations",
        font=dict(size=12),
        plot_bgcolor='rgba(240,240,240,0.95)',
        margin=dict(l=80, r=80, t=100, b=80),
        height=min(800, max(600, n_vars * 100))
    )
    
    return fig


def create_empty_figure_with_message(message: str, message_color: str = 'gray') -> Dict:
    """
    Create an empty figure with a centered message.
    
    Args:
        message: Message to display
        message_color: Color of the message text
        
    Returns:
        Plotly figure dictionary
    """
    return {
        'data': [],
        'layout': {
            'title': message,
            'xaxis': {'visible': False},
            'yaxis': {'visible': False},
            'annotations': [{
                'text': message,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'xanchor': 'center',
                'yanchor': 'middle',
                'showarrow': False,
                'font': {'size': 16, 'color': message_color}
            }]
        }
    }


def create_table_figure(data: pd.DataFrame) -> Dict:
    """
    Create a table figure from a DataFrame with index (which is prior cols)

    Args:
        data: DataFrame to display in the table
        
    Returns:
        Plotly figure dictionary
    """
    return {
        'data': [
            {
                'type': 'table',
                'header': {
                    'values': ['index']+list(data.columns),
                    'fill': {'color': 'lightgray'},
                    'align': 'left'
                },
                'cells': {
                    'values': [data.index] + [data[col] for col in data.columns],
                    'fill': {'color': 'white'},
                    'align': 'left'
                }
            }
        ],
        'layout': {
            'title': 'Data Table',
            'margin': {'l': 10, 'r': 10, 't': 30, 'b': 10}
        }
    }