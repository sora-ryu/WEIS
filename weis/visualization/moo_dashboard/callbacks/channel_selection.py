"""
Channel selection callbacks for button interactions
"""
import ast
from dash import Input, Output, State, callback, callback_context, ALL

from layouts.components import create_button_group, create_no_data_alert
from config.settings import COLOR_SCALES


def register_channel_selection_callbacks(app):
    """Register all channel selection related callbacks."""
    
    @callback(Output('channels', 'children'),
              [Input('yaml-df', 'data'),
               Input('selected-channels', 'data')])
    def update_channel_buttons(yaml_data, selected_channels):
        """Create dynamic button groups for channel selection."""
        if yaml_data is None:
            no_data_msg = create_no_data_alert("Load YAML file to see variable options", "info")
            return [no_data_msg]
        
        selected_channels = selected_channels or []

        # Extract all variables
        objectives = yaml_data.get('objectives', [])
        constraints = yaml_data.get('constraints', [])
        design_vars = yaml_data.get('design_vars', [])
        
        all_variables = objectives + constraints + design_vars
        
        if not all_variables:
            no_vars_msg = create_no_data_alert("No variables found in YAML file", "warning")
            return [no_vars_msg]
        
        # Create button groups for each category
        buttons = []
        if objectives:
            buttons.extend(create_button_group(
                objectives, "Objectives", COLOR_SCALES['objectives'], selected_channels
            ))
        if constraints:
            buttons.extend(create_button_group(
                constraints, "Constraints", COLOR_SCALES['constraints'], selected_channels
            ))
        if design_vars:
            buttons.extend(create_button_group(
                design_vars, "Design Variables", COLOR_SCALES['design_vars'], selected_channels
            ))

        return buttons

    @callback(Output('selected-channels', 'data'),
              [Input({'type': 'channel-btn', 'index': ALL}, 'n_clicks')],
              State('selected-channels', 'data'),
              prevent_initial_call=True)
    def handle_channels_selection(n_clicks_list, current_selected):
        """Handle channel button clicks for multi-select functionality."""
        if not n_clicks_list or not any(n_clicks_list):
            return current_selected or []
        
        # Find which button was clicked
        ctx = callback_context
        if ctx.triggered:
            try:
                trigger_info = ctx.triggered[0]['prop_id']
                button_id_str = trigger_info.split('.n_clicks')[0]
                
                button_info = ast.literal_eval(button_id_str)
                clicked_var = button_info['index']
                
                # Toggle selection: add if not present, remove if present
                current_selected = current_selected or []
                if clicked_var in current_selected:
                    current_selected.remove(clicked_var)
                else:
                    current_selected.append(clicked_var)
                
                return current_selected
            except Exception as e:
                print(f"Error parsing button ID: {e}")
                # Fallback method
                if '"index":"' in trigger_info:
                    start = trigger_info.find('"index":"') + 9
                    end = trigger_info.find('"', start)
                    if end > start:
                        clicked_var = trigger_info[start:end]
                        current_selected = current_selected or []
                        if clicked_var in current_selected:
                            current_selected.remove(clicked_var)
                        else:
                            current_selected.append(clicked_var)
                        return current_selected
        
        return current_selected or []
