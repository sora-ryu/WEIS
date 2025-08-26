"""
Configuration settings for the MOO Dashboard
"""

# App configuration
DEBUG = True
HOST = '0.0.0.0'
PORT = 8050

# UI Configuration
DEFAULT_PLOT_WIDTH = 800
DEFAULT_PLOT_HEIGHT = 800
MARKER_SIZE = 4
MARKER_LINE_WIDTH = 0.5

# Color schemes
COLOR_SCALES = {
    'samples': 'viridis',
    'objectives': 'primary',
    'constraints': 'warning', 
    'design_vars': 'success'
}

# File upload settings
ALLOWED_CSV_EXTENSIONS = ['.csv', '.xls', '.xlsx']
ALLOWED_YAML_EXTENSIONS = ['.yaml', '.yml']
