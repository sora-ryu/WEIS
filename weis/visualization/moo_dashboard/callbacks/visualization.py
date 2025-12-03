"""
Visualization callbacks for plot generation
"""
import io
import pandas as pd
from dash import Input, Output, State, callback, callback_context

from utils.data_processing import prepare_dataframe_for_splom, find_pareto_front
from utils.plot_helpers import (
    create_splom_figure, create_empty_figure_with_message, 
    create_table_figure
)


def register_visualization_callbacks(app):
    """Register all visualization related callbacks."""
    
    @callback(Output('pareto-front-enabled', 'data'),
              Input('pareto-toggle-btn', 'n_clicks'),
              State('pareto-front-enabled', 'data'),
              prevent_initial_call=True)
    def toggle_pareto_front(n_clicks, current_state):
        """Toggle Pareto front visualization on/off."""
        if n_clicks is None:
            return current_state
        return not current_state
    
    @callback(Output('pareto-toggle-btn', 'children'),
              Input('pareto-front-enabled', 'data'))
    def update_pareto_button_text(pareto_enabled):
        """Update button text based on Pareto front state."""
        if pareto_enabled:
            return "Hide Pareto Front"
        else:
            return "Show Pareto Front"
    
    @callback([Output('splom', 'figure'),
               Output('selected-iteration', 'data')],
              [Input('csv-df', 'data'),
               Input('selected-channels', 'data'),
               Input('clear-highlight-btn', 'n_clicks'),
               Input('splom', 'clickData'),
               Input('pareto-front-enabled', 'data'),
               Input('objective-senses', 'data')],
              State('yaml-df', 'data'))
    def update_splom(csv_data, selected_channels, clear_clicks, click_data, pareto_enabled, objective_senses, yaml_data):
        """Update the scatter plot matrix based on selected channels and highlighted sample."""

        if csv_data is None:
            return create_empty_figure_with_message(
                'Load data to view plots', 'gray'
            ), None
        
        ctx = callback_context
        highlighted_iteration = None

        if ctx.triggered:
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            print(f"DEBUG: Trigger ID: {trigger_id}")

            if trigger_id == 'clear-highlight-btn':
                highlighted_iteration = None
            
            elif trigger_id == 'splom' and click_data:
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
        result = prepare_dataframe_for_splom(df, all_selected_vars, yaml_data)
        if result[0] is None:  # No valid data
            return create_empty_figure_with_message(
                'Click variable buttons to select channels for SPLOM', 'blue'
            ), highlighted_iteration

        simplified_df, dimensions, variable_categories = result

        # Calculate Pareto front if enabled
        pareto_indices = None
        if pareto_enabled and yaml_data is not None:
            try:
                # Get objectives from YAML data
                objectives_dict = yaml_data['objectives']
                objectives = list(objectives_dict.keys())
                
                # Use user-selected objective senses from UI (or default to minimize)
                if not objective_senses:
                    objective_senses = {obj: 'minimize' for obj in objectives}
                
                if len(objectives) >= 2:
                    print(f"DEBUG: Calculating Pareto front for objectives: {objectives}")
                    print(f"DEBUG: Objective senses (from UI): {objective_senses}")
                    pareto_indices = find_pareto_front(objectives, df, objective_senses)
                    print(f"DEBUG: Found {len(pareto_indices) if pareto_indices else 0} Pareto optimal points")
                else:
                    print(f"DEBUG: Not enough objectives ({len(objectives)}) for Pareto front calculation")
            except Exception as e:
                print(f"DEBUG: Error calculating Pareto front: {e}")
                import traceback
                traceback.print_exc()
                pareto_indices = None

        # Create and return the SPLOM figure with highlighting and Pareto front
        return create_splom_figure(
            simplified_df, 
            dimensions, 
            len(all_selected_vars),
            highlighted_iteration,
            pareto_indices,
            variable_categories
        ), highlighted_iteration


def register_table_callbacks(app):
    @callback(Output('data-table', 'figure'),
              [Input('csv-df', 'data'),
               Input('selected-iteration', 'data'),
               Input('yaml-df', 'data')])
    def update_table(csv_data, selected_iteration, yaml_data):
        """Update the data table based on selected data point from SPLOM with enhanced statistics"""
        if selected_iteration is None:
            return create_empty_figure_with_message(
                'Click on a data point in the SPLOM to see detailed analysis', 'gray'
            )

        # Convert JSON back to DataFrame
        df = pd.read_json(io.StringIO(csv_data), orient='split')
        
        # Get the selected row data and transpose for display
        filtered_df = df.iloc[[selected_iteration]].T
        
        print(f'Selected iteration: {selected_iteration}')
        print('Filtered DataFrame\n', filtered_df)
        
        # Extract categories from YAML
        variable_categories = {}
        if yaml_data:
            for var in yaml_data.get('objectives', {}).keys():
                variable_categories[var] = 'objectives'
            for var in yaml_data.get('constraints', {}).keys():
                variable_categories[var] = 'constraints'
            for var in yaml_data.get('design_vars', {}).keys():
                variable_categories[var] = 'design_vars'

        # Use the enhanced table with statistical comparisons
        return create_table_figure(filtered_df, variable_categories)
