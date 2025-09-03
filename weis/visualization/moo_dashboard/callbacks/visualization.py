"""
Visualization callbacks for plot generation
"""
import io
import pandas as pd
from dash import Input, Output, State, callback, callback_context

from utils.data_processing import prepare_dataframe_for_splom
from utils.plot_helpers import create_splom_figure, create_empty_figure_with_message, create_table_figure


def register_visualization_callbacks(app):
    """Register all visualization related callbacks."""
    
    @callback([Output('splom', 'figure'),
               Output('selected-iteration', 'data')],
              [Input('csv-df', 'data'),
               Input('selected-channels', 'data'),
               Input('splom', 'clickData')],
              [State('selected-iteration', 'data')])
    def update_splom(csv_data, selected_channels, click_data, selected_iteration):
        """Update the scatter plot matrix based on selected channels and highlighted sample."""
        print(f"DEBUG: update_splom called with selected_iteration: {selected_iteration}")

        if csv_data is None:
            return create_empty_figure_with_message(
                'Load data to view plots', 'gray'
            ), None
        
        ctx = callback_context
        highlighted_iteration = selected_iteration

        if ctx.triggered:
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            print(f"DEBUG: Trigger ID: {trigger_id}")

            if trigger_id == 'splom' and click_data:
                # Handle plot clicks
                if 'points' in click_data and len(click_data['points']) > 0:
                    point = click_data['points'][0]
                    print(f"DEBUG: Clicked point: {point}")
                    new_iteration = point['pointNumber']

                    # Toggle selection
                    if highlighted_iteration == new_iteration:
                        highlighted_iteration = None
                        print("DEBUG: Deselecting point")
                    else:
                        highlighted_iteration = new_iteration
                        print(f"DEBUG: Highlighting iteration: {highlighted_iteration}")

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
            ), highlighted_iteration

        simplified_df, dimensions = result

        # Create and return the SPLOM figure with highlighting
        return create_splom_figure(
            simplified_df, 
            dimensions, 
            len(all_selected_vars),
            highlighted_iteration
        ), highlighted_iteration


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
