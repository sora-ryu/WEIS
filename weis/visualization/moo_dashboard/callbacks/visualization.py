"""
Visualization callbacks for plot generation
"""
import io
import pandas as pd
from dash import Input, Output, callback

from utils.data_processing import prepare_dataframe_for_splom
from utils.plot_helpers import create_splom_figure, create_empty_figure_with_message, create_table_figure


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


def register_table_callbacks(app):
    @callback(Output('data-table', 'figure'),
              [Input('csv-df', 'data'),
               Input('splom', 'clickData')])
    def update_table(csv_data, click_data):
        """Update the data table based on clicked data point from SPLOM"""
        if click_data is None:
            return create_empty_figure_with_message(
                'Click on a data point in the SPLOM to see details', 'gray'
            )

        # Extract information from click_data
        selected_point_idx = click_data['points'][0]['pointIndex']
        print('clickData\n', click_data)

        # Convert JSON back to DataFrame
        df = pd.read_json(io.StringIO(csv_data), orient='split')
        filtered_df = df.iloc[[selected_point_idx]].T       # Transpose dataframe so that we can have some additional rows

        print('Filtered DataFrame\n', filtered_df)

        return create_table_figure(filtered_df)
