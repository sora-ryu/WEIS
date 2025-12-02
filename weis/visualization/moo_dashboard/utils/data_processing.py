"""
Data processing utilities for the MOO Dashboard
"""
import base64
import io
import pandas as pd
import yaml
import ast
import numpy as np
from typing import Optional, Dict, List, Any


def parse_uploaded_contents(contents: str, filename: str) -> Optional[Any]:
    """
    Parse uploaded file contents based on file type.
    
    Args:
        contents: Base64 encoded file contents
        filename: Name of the uploaded file
        
    Returns:
        Parsed data (DataFrame as JSON for CSV/Excel, dict for YAML)
    """
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        if 'csv' in filename.lower():
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            return df.to_json(date_format='iso', orient='split')
        
        elif any(ext in filename.lower() for ext in ['xls', 'xlsx']):
            df = pd.read_excel(io.BytesIO(decoded))
            return df.to_json(date_format='iso', orient='split')
        
        elif any(ext in filename.lower() for ext in ['yaml', 'yml']):
            return yaml.safe_load(io.StringIO(decoded.decode('utf-8')))
            
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return None


def load_csv_from_path(file_path: str) -> Optional[str]:
    """
    Load CSV/Excel file from file path.
    
    Args:
        file_path: Absolute path to the file
        
    Returns:
        DataFrame as JSON string or None if error
    """
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            print(f"Unsupported file format: {file_path}")
            return None
            
        return df.to_json(date_format='iso', orient='split')
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def load_yaml_from_path(file_path: str) -> Optional[Dict]:
    """
    Load YAML file from file path.
    
    Args:
        file_path: Absolute path to the YAML file
        
    Returns:
        Parsed YAML data or None if error
    """
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading YAML file {file_path}: {e}")
        return None


def extract_variable_names(var_list: List[Any]) -> List[str]:
    """
    Extract variable names from nested YAML structure.
    
    Args:
        var_list: List of variables from YAML (can be nested)
        
    Returns:
        Dictionary with variable names as keys and other details as values
    """
    names = {}
    for item in var_list:
        if isinstance(item, list):
            names[item[0]] = {k: float(item[1][k]) for k in ['lower', 'upper'] if k in item[1]}
        else:
            names[item] = None
    return names


def process_yaml_config(config: Dict) -> Dict[str, List[str]]:
    """
    Process YAML configuration to extract objectives, constraints, and design variables.
    
    Args:
        config: Parsed YAML configuration
        
    Returns:
        Dictionary with extracted variable categories
    """
    return {
        'objectives': extract_variable_names(config.get('objectives', [])),
        'constraints': extract_variable_names(config.get('constraints', [])),
        'design_vars': extract_variable_names(config.get('design_vars', []))
    }


def prepare_dataframe_for_splom(df: pd.DataFrame, selected_vars: List[str], yaml_data: Dict) -> tuple:
    """
    Prepare DataFrame for SPLOM visualization with simplified names and sample IDs.
    Array variables are automatically processed as separate min/max values.
    
    Args:
        df: Source DataFrame
        selected_vars: List of selected variable names (may include _min, _max suffixes)
        yaml_data: YAML data containing variable categories
        
    Returns:
        Tuple of (simplified_df, dimensions, variable_categories)
    """
    
    # Extract categories from YAML
    objectives = list(yaml_data.get('objectives', {}).keys()) if yaml_data else []
    constraints = list(yaml_data.get('constraints', {}).keys()) if yaml_data else []
    design_vars = list(yaml_data.get('design_vars', {}).keys()) if yaml_data else []
    
    # Parse selected variables - array variables are automatically processed as separate
    processed_vars = {}
    for var in selected_vars:
        if var.endswith('_min') or var.endswith('_max'):
            # Array processing with min/max
            base_var = var.rsplit('_', 1)[0]
            if base_var not in processed_vars:
                processed_vars[base_var] = {'type': 'array', 'vars': []}
            processed_vars[base_var]['vars'].append(var)
        else:
            # Regular variable
            processed_vars[var] = {'type': 'regular', 'vars': [var]}
    
    # Filter variables that exist in the DataFrame
    available_vars = []
    for base_var, config in processed_vars.items():
        if base_var in df.columns:
            available_vars.extend(config['vars'])
    
    if not available_vars:
        return None, [], {}
    
    # Create simplified DataFrame
    simplified_df = pd.DataFrame()
    dimensions = []
    variable_categories = {}  # Map simplified name to category
    
    # Helper function to determine category
    def get_category(var_name):
        if var_name in objectives:
            return 'objectives'
        elif var_name in constraints:
            return 'constraints'
        elif var_name in design_vars:
            return 'design_vars'
        return None
    
    for base_var, config in processed_vars.items():
        if base_var not in df.columns:
            continue
            
        if config['type'] == 'regular':
            # Regular variable - copy as is
            simplified_name = base_var.split('.')[-1]
            simplified_df[simplified_name] = df[base_var]
            dimensions.append(dict(
                label=simplified_name,
                values=df[base_var].values
            ))
            variable_categories[simplified_name] = get_category(base_var)
            
        elif config['type'] == 'array':
            # Array variable - separate min and max
            array_data = df[base_var]
            print(f"DEBUG: Processing array variable '{base_var}' for separate min/max")
            print(f"DEBUG: Array data type: {type(array_data.iloc[0]) if len(array_data) > 0 else 'empty'}")
            print(f"DEBUG: Sample array values: {array_data.head(2).tolist()}")
            
            # Process array values to extract min and max
            min_values = []
            max_values = []
            
            for val in array_data:
                try:
                    if isinstance(val, (list, np.ndarray)):
                        arr = np.array(val, dtype=float)
                    elif isinstance(val, str):
                        try:
                            # Try to parse as a Python literal (list, tuple, etc.)
                            parsed_val = ast.literal_eval(val)
                            if isinstance(parsed_val, (list, tuple)):
                                arr = np.array(parsed_val, dtype=float)
                            else:
                                arr = np.array([float(parsed_val)])
                        except (ValueError, SyntaxError):
                            # If parsing fails, try numpy-style string parsing
                            try:
                                # Handle numpy array string format like '[0. 0. 0. 0. 0. 0. 0.]'
                                val_clean = val.strip()
                                if val_clean.startswith('[') and val_clean.endswith(']'):
                                    # Remove brackets and split by whitespace
                                    inner_str = val_clean[1:-1].strip()
                                    if inner_str:
                                        # Split by whitespace and convert to float
                                        str_values = inner_str.split()
                                        arr = np.array([float(x) for x in str_values if x.strip()], dtype=float)
                                    else:
                                        arr = np.array([], dtype=float)
                                else:
                                    # Try direct float conversion
                                    arr = np.array([float(val)])
                            except (ValueError, TypeError):
                                # If all parsing fails, skip this value
                                print(f"Warning: Could not convert '{val}' to numeric array, skipping")
                                continue
                    else:
                        arr = np.array([float(val)])
                    
                    # Ensure we have a valid numeric array
                    if len(arr) > 0 and not np.isnan(arr).all():
                        # Sanity check if min/max values are within constraints
                        min_val = float(np.nanmin(arr))
                        max_val = float(np.nanmax(arr))
                        
                        if min_val > yaml_data['constraints'][base_var]['lower'] and min_val < yaml_data['constraints'][base_var]['upper']:
                            min_values.append(min_val)
                        if max_val > yaml_data['constraints'][base_var]['lower'] and max_val < yaml_data['constraints'][base_var]['upper']:
                            max_values.append(max_val)
                    else:
                        # If all values are NaN, append NaN
                        min_values.append(np.nan)
                        max_values.append(np.nan)
                        
                except Exception as e:
                    print(f"Warning: Error processing array value '{val}': {e}")
                    min_values.append(np.nan)
                    max_values.append(np.nan)
            
            # Add min and max as separate columns
            base_name = base_var.split('.')[-1]
            min_name = f"{base_name}_min"
            max_name = f"{base_name}_max"
            
            simplified_df[min_name] = min_values
            simplified_df[max_name] = max_values
            
            category = get_category(base_var)
            
            dimensions.extend([
                dict(label=min_name, values=min_values),
                dict(label=max_name, values=max_values)
            ])
            
            variable_categories[min_name] = category
            variable_categories[max_name] = category
    
    # Add sample_id
    simplified_df['sample_id'] = range(len(simplified_df))
    
    return simplified_df, dimensions, variable_categories


def find_pareto_front(objectives, df: pd.DataFrame) -> List[int]:
        """Find Pareto front samples algorithmically"""
        if not objectives or df.empty:
            return []
        
        pareto_indices = []
        n_samples = len(df)
        
        # Extract objective values
        obj_values = df[objectives].values
        
        # Find non-dominated solutions
        for i in range(n_samples):
            is_dominated = False
            
            for j in range(n_samples):
                if i == j:
                    continue
                
                # Check if j dominates i (assuming minimization)
                better_in_all = True
                better_at_least_one = False
                
                for k in range(len(objectives)):
                    if obj_values[j, k] > obj_values[i, k]:
                        better_in_all = False
                        break
                    elif obj_values[j, k] < obj_values[i, k]:
                        better_at_least_one = True
                
                if better_in_all and better_at_least_one:
                    is_dominated = True         # Set as dominated if dominated condition met true for all objectives
                    break
            
            if not is_dominated:                # Basically, pareto fronts will be a union of non-dominated solutions for each pair of objectives.
                pareto_indices.append(i)
        
        print(f"Found {len(pareto_indices)} Pareto optimal solutions algorithmically")

        return pareto_indices