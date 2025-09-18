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
    NON_HIGHLIGHT_OPACITY, HIGHLIGHT_LINE_WIDTH, COLOR_SCALES, HIGHLIGHT_SYMBOL
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


def create_splom_figure(df: pd.DataFrame, dimensions: List[Dict], num_vars: int, highlighted_iteration: int = None, pareto_indices: List[int] = None):
    """
    Create a scatter plot matrix (SPLOM) with color-coded samples and auto-sized labels.
    Uses plotly.graph_objects for better control of marker properties and highlighting.
    
    Args:
        df: DataFrame with simplified column names and sample_id
        dimensions: List of dimension dictionaries with 'label' and 'values' keys
        num_vars: Number of variables for title
        highlighted_iteration: Optional iteration to highlight across all subplots
        pareto_indices: Optional list of indices for Pareto front points

    Returns:
        Plotly figure with SPLOM
    """
    if df.empty or not dimensions:
        return go.Figure()

    # Calculate optimal font size and margins
    font_size = calculate_font_size(num_vars, DEFAULT_PLOT_WIDTH)
    margin_size = calculate_margin_size(num_vars, font_size)
    
    # Determine max label length based on number of variables
    max_label_length = 20 if num_vars <= 3 else 15 if num_vars <= 5 else 12 if num_vars <= 7 else 10
    
    # Extract labels from dimensions and truncate them
    dimension_labels = [dim['label'] for dim in dimensions]
    truncated_labels = truncate_labels(dimension_labels, max_label_length)
    
    # Create updated dimensions with truncated labels
    truncated_dimensions = []
    for i, dim in enumerate(dimensions):
        truncated_dimensions.append({
            'label': truncated_labels[i],
            'values': dim['values']
        })
    
    # Prepare data for SPLOM
    n_vars = num_vars
    n_samples = len(df)
        
    # Create color array based on iteration index
    colors = np.arange(n_samples)  # Use actual iteration numbers for colors
    
    # Create text labels
    text_labels = [f"Iteration {i}" for i in range(n_samples)]

    # Create main SPLOM trace with normal points
    splom_trace = go.Splom(
        dimensions=truncated_dimensions,
        text=text_labels,
        marker=dict(
            color=colors,
            colorscale=COLOR_SCALES['samples'],
            size=8,
            symbol='circle',
            line=dict(
                color='white',
                width=0.5
            ),
            opacity=1.0 if highlighted_iteration is None else NON_HIGHLIGHT_OPACITY,
            colorbar=dict(
                title="Iteration",
                title_side="right",
                thickness=15,
                len=0.7,
                x=1.02,
                tickmode='linear',
                tick0=0,
                dtick=max(1, n_samples // 10)  # Show reasonable number of ticks
            )
        ),
        diagonal_visible=True,
        showupperhalf=True,
        showlowerhalf=False,
        name=f"",
        showlegend=False
    )
    
    traces = [splom_trace]
    
    # Add Pareto front trace first (so it's drawn before highlights)
    if pareto_indices is not None and len(pareto_indices) > 0:
        # Create dimensions for Pareto front points
        pareto_dimensions = []
        for dim_dict in truncated_dimensions:
            dim_label = dim_dict['label']
            dim_values = dim_dict['values']
            
            # Extract values for Pareto front points
            pareto_values = [dim_values[i] for i in pareto_indices if i < len(dim_values)]
            
            pareto_dimensions.append(dict(
                label=dim_label,
                values=pareto_values
            ))
        
        # Create Pareto front trace (rendered before highlights)
        pareto_trace = go.Splom(
            dimensions=pareto_dimensions,
            text=[f"Iteration {i} (Pareto)" for i in pareto_indices],
            marker=dict(
                color='red',
                size=MARKER_SIZE * 1.2,  # Slightly larger than normal
                symbol='diamond',  # Different symbol for Pareto points
                line=dict(
                    color='darkred',
                    width=2
                ),
                opacity=0.8
            ),
            diagonal_visible=True,
            showupperhalf=True,
            showlowerhalf=False,
            name=f"Pareto Front ({len(pareto_indices)} points)",
            showlegend=False
        )
        
        traces.append(pareto_trace)

    # Add highlighted trace LAST so it's always on top
    if highlighted_iteration is not None and highlighted_iteration < n_samples:
        # Create dimensions for highlighted point using truncated dimensions
        highlighted_dimensions = []
        for dim_dict in truncated_dimensions:
            dim_label = dim_dict['label']
            dim_values = dim_dict['values']
            
            # Extract the value for the highlighted iteration
            highlighted_value = dim_values[highlighted_iteration]
            
            highlighted_dimensions.append(dict(
                label=dim_label,
                values=[highlighted_value]  # Single value as list
            ))
        
        # Create highlighted trace (rendered on top of everything)
        highlighted_trace = go.Splom(
            dimensions=highlighted_dimensions,
            text=[f"Iteration {highlighted_iteration} (Selected)"],
            marker=dict(
                color=HIGHLIGHT_COLOR,
                size=MARKER_SIZE * HIGHLIGHT_SIZE_MULTIPLIER,
                symbol=HIGHLIGHT_SYMBOL,  # Use star for high visibility
                line=dict(
                    color='black',  # Black border for maximum contrast
                    width=HIGHLIGHT_LINE_WIDTH
                ),
                opacity=HIGHLIGHT_OPACITY
            ),
            diagonal_visible=True,
            showupperhalf=True,
            showlowerhalf=False,
            name=f"Iteration {highlighted_iteration} (Selected)",
            showlegend=False
        )
        
        traces.append(highlighted_trace)

    fig = go.Figure(data=traces)

    # Update layout
    fig.update_layout(
        width=DEFAULT_PLOT_WIDTH,
        height=DEFAULT_PLOT_HEIGHT,
        title={
            'text': f'Scatterplot Matrix (SPLOM) - {n_vars} Variables × {n_samples} Iterations',
            'x': 0.5,
            'xanchor': 'center'
        },
        plot_bgcolor='rgba(240,240,240,0.95)',
        # Add margins to prevent label cutoff and accommodate colorbar
        margin=dict(
            l=margin_size,
            r=margin_size + 60,  # Extra space for colorbar
            t=margin_size + 20,  # Extra space for title
            b=margin_size
        ),
        # Configure font sizes for all text elements
        font=dict(size=font_size),
        # Adjust axis label properties
        showlegend=False
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
    # Format numeric values for better display
    formatted_data = data.copy()
    
    # Round numeric columns to 4 decimal places and format
    for col in formatted_data.columns:
        if formatted_data[col].dtype in ['float64', 'float32']:
            formatted_data[col] = formatted_data[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A")
        elif formatted_data[col].dtype in ['int64', 'int32']:
            formatted_data[col] = formatted_data[col].apply(lambda x: f"{x:,}" if pd.notna(x) else "N/A")
    
    # Create alternating row colors
    num_rows = len(formatted_data)
    row_colors = ['#f8f9fa' if i % 2 == 0 else '#ffffff' for i in range(num_rows)]
    
    # Prepare header values with better formatting
    header_values = ['Iteration'] + [f"<b>{col}</b>" for col in formatted_data.columns]
    
    # Prepare cell values with index
    cell_values = [formatted_data.index.tolist()] + [formatted_data[col].tolist() for col in formatted_data.columns]
    
    return {
        'data': [
            {
                'type': 'table',
                'header': {
                    'values': header_values,
                    'fill': {
                        'color': '#2c3e50'  # Dark blue-gray header
                    },
                    'align': ['left'] * (len(formatted_data.columns) + 1),
                    'font': {
                        'color': 'white',
                        'size': MAX_FONT_SIZE,
                    },
                    'height': 40,
                    'line': {'color': '#34495e', 'width': 1}
                },
                'cells': {
                    'values': cell_values,
                    'fill': {
                        'color': [['#e8f4fd'] + row_colors]  # Light blue for index column, alternating for data
                    },
                    'align': ['left'] * (len(formatted_data.columns) + 1),
                    'font': {
                        'color': ['#2c3e50'] * (len(formatted_data.columns) + 1),
                        'size': BASE_FONT_SIZE,
                    },
                    'height': 35,
                    'line': {'color': '#bdc3c7', 'width': 0.5}
                }
            }
        ],
        'layout': {
            'margin': {'l': 20, 'r': 20, 't': 60, 'b': 20},
            'paper_bgcolor': '#ffffff',
            'plot_bgcolor': '#ffffff',
            'height': max(300, min(600, num_rows * 40 + 120))  # Dynamic height based on data
        }
    }