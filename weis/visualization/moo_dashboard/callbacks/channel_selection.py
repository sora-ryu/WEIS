"""
Channel selection callbacks for button interactions
"""
import ast
import io
import pandas as pd
import numpy as np
from dash import Input, Output, State, callback, callback_context, ALL

from layouts.components import create_button_group, create_no_data_alert
from config.settings import COLOR_SCALES


def detect_array_columns(csv_data):
    """
    Detect which columns contain array values.
    
    Args:
        csv_data: JSON string of CSV data
        
    Returns:
        Set of column names that contain arrays
    """
    if csv_data is None:
        return set()
    
    try:
        df = pd.read_json(io.StringIO(csv_data), orient='split')
        array_columns = set()
        
        for col in df.columns:
            # Check if any value in the column is array-like
            sample_values = df[col].dropna().head(3)  # Check first 3 non-null values
            for val in sample_values:
                is_array = False
                
                # Check if it's a string that could represent an array
                if isinstance(val, str):
                    try:
                        # Try to parse as a Python literal
                        parsed = ast.literal_eval(val)
                        if isinstance(parsed, (list, tuple)) and len(parsed) > 1:
                            is_array = True
                    except (ValueError, SyntaxError):
                        # Check for numpy array string format like '[0. 0. 0. 0. 0. 0. 0.]'
                        val_clean = val.strip()
                        if val_clean.startswith('[') and val_clean.endswith(']'):
                            inner_str = val_clean[1:-1].strip()
                            if inner_str and len(inner_str.split()) > 1:
                                # Multiple space-separated values indicate an array
                                is_array = True
                
                # Check if it's already a list/array
                elif isinstance(val, (list, tuple, np.ndarray)) and len(val) > 1:
                    is_array = True
                
                if is_array:
                    array_columns.add(col)
                    print(f"DEBUG: Detected array column '{col}' with sample value: {val}")
                    break  # Found array in this column, move to next

        print(f"DEBUG: Final detected array columns: {array_columns}")
        return array_columns
    except Exception as e:
        print(f"Error detecting array columns: {e}")
        return set()


def register_channel_selection_callbacks(app):
    """Register all channel selection related callbacks."""
    
    @callback(Output('channels', 'children'),
              [Input('yaml-df', 'data'),
               Input('csv-df', 'data'),
               Input('selected-channels', 'data')])
    def update_channel_buttons(yaml_data, csv_data, selected_channels):
        """Create dynamic button groups for channel selection."""
        if yaml_data is None:
            no_data_msg = create_no_data_alert("Load YAML file to see variable options", "info")
            return [no_data_msg]
        
        selected_channels = selected_channels or []
        
        # Detect array columns from CSV data
        array_columns = detect_array_columns(csv_data)
        print(f"DEBUG: Detected array columns: {array_columns}")

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
                objectives, "Objectives", COLOR_SCALES['objectives'], selected_channels, array_columns
            ))
        if constraints:
            buttons.extend(create_button_group(
                constraints, "Constraints", COLOR_SCALES['constraints'], selected_channels, array_columns
            ))
        if design_vars:
            buttons.extend(create_button_group(
                design_vars, "Design Variables", COLOR_SCALES['design_vars'], selected_channels, array_columns
            ))

        return buttons

    @callback(Output('selected-channels', 'data'),
              [Input({'type': 'channel-btn', 'index': ALL}, 'n_clicks'),
               Input({'type': 'array-option-btn', 'index': ALL, 'var': ALL}, 'n_clicks'),
               Input({'type': 'array-toggle-btn', 'index': ALL}, 'n_clicks')],
              State('selected-channels', 'data'),
              prevent_initial_call=True)
    def handle_channels_selection(channel_clicks, array_option_clicks, array_toggle_clicks, current_selected):
        """Handle channel button clicks and array option button clicks for multi-select functionality."""
        ctx = callback_context
        if not ctx.triggered:
            return current_selected or []
        
        current_selected = current_selected or []

        # Check if any button was actually clicked (n_clicks > 0)
        # This prevents the callback from firing on initial load when n_clicks are None
        total_channel_clicks = sum(click or 0 for click in channel_clicks)
        total_array_clicks = sum(click or 0 for click in array_option_clicks)
        total_toggle_clicks = sum(click or 0 for click in array_toggle_clicks)
        
        if total_channel_clicks == 0 and total_array_clicks == 0 and total_toggle_clicks == 0:
            return current_selected or []
        
        try:
            trigger_info = ctx.triggered_id
            
            if  trigger_info['type'] == 'channel-btn':
                # Handle regular channel button clicks
                clicked_var = trigger_info['index']
                print(f"DEBUG: Regular channel clicked: {clicked_var}")
                
                # Toggle selection: add if not present, remove if present
                if clicked_var in current_selected:
                    current_selected.remove(clicked_var)
                    print(f"DEBUG: Removed {clicked_var}")
                else:
                    current_selected.append(clicked_var)
                    print(f"DEBUG: Added {clicked_var}")
            elif trigger_info['type'] == 'array-option-btn':
                # Handle array option button clicks (separate/combine)
                var_name = trigger_info['var']
                option = trigger_info['index']  # 'separate' or 'combine'
                
                print(f"DEBUG: Array option clicked - var: {var_name}, option: {option}")
                
                # Remove any existing entries for this variable
                current_selected = [sel for sel in current_selected 
                                  if not (sel.startswith(f"{var_name}_") or sel == var_name)]
                
                # Add the new selection
                if option == 'separate':
                    current_selected.extend([f"{var_name}_min", f"{var_name}_max"])
                    print(f"DEBUG: Added separate: {var_name}_min, {var_name}_max")
                elif option == 'combine':
                    current_selected.append(f"{var_name}_combined")
                    print(f"DEBUG: Added combined: {var_name}_combined")
            elif trigger_info['type'] == 'array-toggle-btn':
                # Handle array toggle button clicks (remove all selections for this array)
                var_name = trigger_info['index']
                print(f"DEBUG: Array toggle clicked: {var_name}")
                
                # Remove any existing entries for this variable
                old_count = len(current_selected)
                current_selected = [sel for sel in current_selected 
                                  if not (sel.startswith(f"{var_name}_") or sel == var_name)]
                
                if len(current_selected) < old_count:
                    print(f"DEBUG: Removed all selections for {var_name}")
                else:
                    print(f"DEBUG: No selections to remove for {var_name}")
            
            print(f"DEBUG: Current selected after: {current_selected}")
            return current_selected
            
        except Exception as e:
            print(f"ERROR parsing button ID: {e}")
            print(f"ERROR trigger_info: {trigger_info}")
            return current_selected
