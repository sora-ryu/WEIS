"""
Plot helpers and formatting utilities
"""
import plotly.express as px
import pandas as pd
from typing import Dict, List
from config.settings import (
    DEFAULT_PLOT_WIDTH, DEFAULT_PLOT_HEIGHT, MARKER_SIZE, MARKER_LINE_WIDTH,
    BASE_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE, BASE_MARGIN, MAX_MARGIN
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


def create_splom_figure(df: pd.DataFrame, dimensions: List[str], num_vars: int) -> px.scatter_matrix:
    """
    Create a scatter plot matrix (SPLOM) with color-coded samples and auto-sized labels.
    
    Args:
        df: DataFrame with simplified column names and sample_id
        dimensions: List of dimension names for the SPLOM
        num_vars: Number of variables for title
        
    Returns:
        Plotly scatter matrix figure
    """
    # Calculate optimal font size and margins
    font_size = calculate_font_size(num_vars, DEFAULT_PLOT_WIDTH)
    margin_size = calculate_margin_size(num_vars, font_size)
    
    # Determine max label length based on number of variables
    max_label_length = 20 if num_vars <= 3 else 15 if num_vars <= 5 else 12 if num_vars <= 7 else 10
    
    # Create a mapping of original to truncated names for the plot
    original_dimensions = dimensions.copy()
    truncated_dimensions = truncate_labels(dimensions, max_label_length)
    
    # Create a temporary DataFrame with truncated column names for the plot
    plot_df = df.copy()
    dimension_mapping = dict(zip(original_dimensions, truncated_dimensions))
    
    # Rename columns in the DataFrame for plotting
    for orig, trunc in dimension_mapping.items():
        if orig in plot_df.columns:
            plot_df = plot_df.rename(columns={orig: trunc})
    
    splom_fig = px.scatter_matrix(
        plot_df,
        dimensions=truncated_dimensions,
        color='sample_id',
        hover_data=['sample_id'],
        color_continuous_scale='viridis',
        title=f'Scatter Plot Matrix ({num_vars} variables)'
    )
    
    splom_fig.update_layout(
        width=DEFAULT_PLOT_WIDTH,
        height=DEFAULT_PLOT_HEIGHT,
        title={
            'text': f'Scatter Plot Matrix ({num_vars} variables)',
            'x': 0.5,
            'xanchor': 'center'
        },
        hovermode='closest',
        coloraxis_colorbar=dict(
            title="Sample ID",
            title_side="right"
        ),
        # Add margins to prevent label cutoff
        margin=dict(
            l=margin_size,
            r=margin_size,
            t=margin_size + 20,  # Extra space for title
            b=margin_size
        ),
        # Configure font sizes for all text elements
        font=dict(size=font_size),
        # Adjust axis label properties
        showlegend=False
    )
    
    # Update all axes with optimized text settings
    for i in range(num_vars):
        for j in range(num_vars):
            # Update x-axis labels
            splom_fig.update_xaxes(
                title_font_size=font_size,
                tickfont_size=max(6, font_size - 2),
                title_standoff=10,
                row=i+1, col=j+1
            )
            # Update y-axis labels  
            splom_fig.update_yaxes(
                title_font_size=font_size,
                tickfont_size=max(6, font_size - 2),
                title_standoff=10,
                row=i+1, col=j+1
            )
    
    splom_fig.update_traces(
        diagonal_visible=True,
        showlowerhalf=False,
        showupperhalf=True,
        hovertemplate='<b>Sample %{customdata[0]}</b><br>' +
                      '%{xaxis.title.text}: %{x}<br>' +
                      '%{yaxis.title.text}: %{y}<br>' +
                      '<extra></extra>',
        marker=dict(size=MARKER_SIZE, line=dict(width=MARKER_LINE_WIDTH, color='white'))
    )
    
    return splom_fig


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