"""
Visualization callbacks for plot generation
"""
import io
import pandas as pd
from dash import Input, Output, callback

from utils.data_processing import prepare_dataframe_for_splom
from utils.plot_helpers import create_splom_figure, create_empty_figure_with_message


def register_visualization_callbacks(app):
    """Register all visualization related callbacks."""
    
    @callback(Output('splom', 'figure'),
              [Input('csv-df', 'data'),
               Input('selected-channels', 'data')])
    def update_splom(csv_data, selected_channels):
        """Update the scatter plot matrix based on selected channels."""
        if csv_data is None:
            return create_empty_figure_with_message(
                'Load CSV data to view plots', 'gray'
            )

        # Convert JSON back to DataFrame
        df = pd.read_json(io.StringIO(csv_data), orient='split')
        
        # Ensure selected variables are lists
        selected_channels = selected_channels or []
        all_selected_vars = list(set(selected_channels))

        # Prepare data for SPLOM
        result = prepare_dataframe_for_splom(df, all_selected_vars)
        if result[0] is None:  # No valid data
            return create_empty_figure_with_message(
                'Click variable buttons to select channels for SPLOM', 'blue'
            )
        
        simplified_df, simplified_names, simplified_vars = result
        
        # Create and return the SPLOM figure
        return create_splom_figure(simplified_df, simplified_vars, len(all_selected_vars))
