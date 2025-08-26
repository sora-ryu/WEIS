"""
Plot helpers and formatting utilities
"""
import plotly.express as px
import pandas as pd
from typing import Dict, List
from config.settings import DEFAULT_PLOT_WIDTH, DEFAULT_PLOT_HEIGHT, MARKER_SIZE, MARKER_LINE_WIDTH


def create_splom_figure(df: pd.DataFrame, dimensions: List[str], num_vars: int) -> px.scatter_matrix:
    """
    Create a scatter plot matrix (SPLOM) with color-coded samples.
    
    Args:
        df: DataFrame with simplified column names and sample_id
        dimensions: List of dimension names for the SPLOM
        num_vars: Number of variables for title
        
    Returns:
        Plotly scatter matrix figure
    """
    splom_fig = px.scatter_matrix(
        df,
        dimensions=dimensions,
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
        )
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
