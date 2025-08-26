"""
Data processing utilities for the MOO Dashboard
"""
import base64
import io
import pandas as pd
import yaml
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
        Flattened list of variable names
    """
    names = []
    for item in var_list:
        if isinstance(item, list):
            if isinstance(item[0], list):
                names.append(item[0][0])  # Extract the first element of the first list
            else:
                names.append(item[0])
        else:
            names.append(item)
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


def prepare_dataframe_for_splom(df: pd.DataFrame, selected_vars: List[str]) -> tuple:
    """
    Prepare DataFrame for SPLOM visualization with simplified names and sample IDs.
    
    Args:
        df: Source DataFrame
        selected_vars: List of selected variable names
        
    Returns:
        Tuple of (processed_df, simplified_names_dict, simplified_var_list)
    """
    # Filter variables that exist in the DataFrame
    available_vars = [var for var in selected_vars if var in df.columns]
    
    if not available_vars:
        return None, {}, []
    
    # Create simplified DataFrame
    simplified_df = df[available_vars].copy()
    simplified_df['sample_id'] = range(len(simplified_df))
    
    # Create mapping of simplified names
    simplified_names = {}
    for var in available_vars:
        simplified_name = var.split('.')[-1]
        simplified_names[var] = simplified_name
        simplified_df = simplified_df.rename(columns={var: simplified_name})
    
    # Get list of simplified variable names
    simplified_vars = [simplified_names[var] for var in available_vars]
    
    return simplified_df, simplified_names, simplified_vars
