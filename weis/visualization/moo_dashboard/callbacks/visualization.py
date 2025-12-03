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
    
    @callback(Output('diagonal-visible', 'data'),
              Input('diagonal-toggle-btn', 'n_clicks'),
              State('diagonal-visible', 'data'),
              prevent_initial_call=True)
    def toggle_diagonal(n_clicks, current_state):
        """Toggle diagonal visibility."""
        if n_clicks is None:
            return current_state
        return not current_state
    
    @callback(Output('diagonal-toggle-btn', 'children'),
              Input('diagonal-visible', 'data'))
    def update_diagonal_button_text(diagonal_visible):
        """Update button text based on diagonal visibility state."""
        if diagonal_visible:
            return "Hide Diagonal"
        else:
            return "Show Diagonal"
    
    @callback([Output('splom', 'figure'),
               Output('selected-iteration', 'data')],
              [Input('csv-df', 'data'),
               Input('selected-channels', 'data'),
               Input('clear-highlight-btn', 'n_clicks'),
               Input('splom', 'clickData'),
               Input('pareto-front-enabled', 'data'),
               Input('objective-senses', 'data'),
               Input('diagonal-visible', 'data')],
              State('yaml-df', 'data'))
    def update_splom(csv_data, selected_channels, clear_clicks, click_data, pareto_enabled, objective_senses, diagonal_visible, yaml_data):
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
            variable_categories,
            diagonal_visible
        ), highlighted_iteration


    @callback(
        Output('download-splom-html', 'data'),
        Input('download-html-btn', 'n_clicks'),
        State('splom', 'figure'),
        State('data-table', 'figure'),
        State('csv-df', 'data'),
        State('yaml-df', 'data'),
        State('selected-channels', 'data'),
        State('objective-senses', 'data'),
        prevent_initial_call=True
    )
    def download_splom_html(n_clicks, splom_figure, table_figure, csv_data, yaml_data, selected_channels, objective_senses):
        """Download an interactive HTML file with SPLOM, data table, and working controls."""
        if n_clicks is None or splom_figure is None or csv_data is None:
            return None
        
        import plotly.graph_objects as go
        import json
        from datetime import datetime
        
        # Parse CSV data to reconstruct complete data trace if needed
        df = pd.read_json(io.StringIO(csv_data), orient='split')
        
        # Ensure the SPLOM figure has the main data trace visible
        # The issue is that splom_figure might not have the base data trace if it's been filtered
        # So we need to ensure all traces are present
        all_traces = []
        
        # Find or create the main data points trace
        main_trace = None
        pareto_trace = None
        highlight_trace = None
        
        for trace in splom_figure.get('data', []):
            if trace.get('name') == 'Data Points':
                main_trace = trace
            elif trace.get('name') == 'Pareto Front':
                pareto_trace = trace
            elif trace.get('name') == 'Highlighted':
                highlight_trace = trace
        
        # Prepare data for reconstruction if needed
        simplified_df = None
        dimensions_serializable = None
        variable_categories = None
        
        if selected_channels and yaml_data:
            simplified_df, dimensions, variable_categories = prepare_dataframe_for_splom(df, selected_channels, yaml_data)
            
            # Convert numpy arrays to lists for JSON serialization
            dimensions_serializable = []
            for dim in dimensions:
                dim_copy = dict(dim)
                if hasattr(dim_copy['values'], 'tolist'):
                    dim_copy['values'] = dim_copy['values'].tolist()
                dimensions_serializable.append(dim_copy)
        
        # If main trace exists, add it first
        if main_trace:
            # Ensure it's visible
            main_trace_copy = dict(main_trace)
            main_trace_copy['visible'] = True
            all_traces.append(main_trace_copy)
        elif dimensions_serializable:
            # Reconstruct main trace from data if it's missing
            colors = list(range(len(simplified_df)))
            text_labels = [f"Iteration {i}" for i in range(len(simplified_df))]
            
            main_trace_reconstructed = {
                'type': 'splom',
                'name': 'Data Points',
                'dimensions': dimensions_serializable,
                'text': text_labels,
                'marker': {
                    'color': colors,
                    'colorscale': 'Viridis',
                    'size': 8,
                    'symbol': 'circle',
                    'line': {'color': 'white', 'width': 0.5},
                    'opacity': 1.0,
                    'colorbar': {
                        'title': 'Iteration',
                        'title_side': 'right',
                        'thickness': 15,
                        'len': 0.7,
                        'x': 1.02
                    }
                },
                'diagonal': {'visible': False},
                'showupperhalf': True,
                'showlowerhalf': False,
                'visible': True
            }
            all_traces.append(main_trace_reconstructed)
        
        # Calculate and add Pareto front trace
        if simplified_df is not None and not simplified_df.empty and yaml_data:
            # Get objective columns
            objective_cols_original = [col for col in selected_channels if col in yaml_data.get('objectives', {})]
            
            if len(objective_cols_original) >= 2:
                # Map original column names to simplified names in simplified_df
                objective_cols_simplified = []
                for col in objective_cols_original:
                    simplified_name = col.split('.')[-1]
                    if simplified_name in simplified_df.columns:
                        objective_cols_simplified.append(simplified_name)
                
                if len(objective_cols_simplified) >= 2:
                    # Map objective_senses from original names to simplified names
                    objective_senses_simplified = {}
                    if objective_senses:
                        for orig_col in objective_cols_original:
                            simplified_name = orig_col.split('.')[-1]
                            if orig_col in objective_senses and simplified_name in simplified_df.columns:
                                objective_senses_simplified[simplified_name] = objective_senses[orig_col]
                    
                    # Calculate Pareto front using simplified column names and mapped senses
                    pareto_indices = find_pareto_front(objective_cols_simplified, simplified_df, objective_senses_simplified)
                
                    if pareto_indices is not None and len(pareto_indices) > 0:
                        # Create Pareto dimensions from the main trace data
                        pareto_dimensions = []
                        for dim in dimensions_serializable:
                            pareto_values = [dim['values'][i] for i in pareto_indices]
                            pareto_dimensions.append({
                                'label': dim['label'],
                                'values': pareto_values
                            })
                        
                        pareto_text = [f"Pareto - Iteration {i}" for i in pareto_indices]
                        
                        pareto_trace_reconstructed = {
                            'type': 'splom',
                            'name': 'Pareto Front',
                            'dimensions': pareto_dimensions,
                            'text': pareto_text,
                            'marker': {
                                'color': '#FF2400',
                                'size': 10,
                                'symbol': 'diamond',
                                'line': {'color': 'black', 'width': 1.5},
                                'opacity': 1.0
                            },
                            'diagonal': {'visible': False},
                            'showupperhalf': True,
                            'showlowerhalf': False,
                            'visible': True
                        }
                        all_traces.append(pareto_trace_reconstructed)
        elif pareto_trace:
            # Use existing Pareto trace if we couldn't reconstruct
            all_traces.append(dict(pareto_trace))
        
        # Don't include highlight trace in export (user can click to create new ones)
        
        # Create the complete figure for export
        export_figure = {
            'data': all_traces,
            'layout': splom_figure.get('layout', {})
        }
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"moo_dashboard_{timestamp}.html"
        
        # Convert figures to JSON for embedding
        splom_json = json.dumps(export_figure)
        table_json = json.dumps(table_figure) if table_figure else json.dumps({})
        
        # Create comprehensive interactive HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MOO Dashboard - Interactive Export</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 1800px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .controls {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .btn {{
            background-color: #0d6efd;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }}
        .btn:hover {{
            background-color: #0b5ed7;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .btn-secondary {{
            background-color: #6c757d;
        }}
        .btn-secondary:hover {{
            background-color: #5a6268;
        }}
        .btn-success {{
            background-color: #198754;
        }}
        .btn-success:hover {{
            background-color: #157347;
        }}
        .btn-info {{
            background-color: #0dcaf0;
        }}
        .btn-info:hover {{
            background-color: #31d2f2;
        }}
        .plot-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .plot-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 1200px) {{
            .plot-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        h1 {{
            margin: 0;
            font-size: 28px;
        }}
        h2 {{
            margin-top: 0;
            color: #495057;
            font-size: 20px;
        }}
        .export-info {{
            font-size: 14px;
            color: rgba(255,255,255,0.9);
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Multi-Objective Optimization Dashboard</h1>
            <div class="export-info">Exported on {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}</div>
            <div class="export-info" id="objectiveGoals" style="margin-top: 10px;"></div>
        </div>
        
        <div class="controls">
            <button class="btn btn-secondary" onclick="clearHighlight()">Clear Highlighting</button>
            <button class="btn btn-success" id="paretoBtn" onclick="togglePareto()">Hide Pareto Front</button>
            <button class="btn btn-info" id="diagonalBtn" onclick="toggleDiagonal()">Show Diagonal</button>
        </div>
        
        <div class="plot-grid">
            <div class="plot-container">
                <h2>Scatter Plot Matrix (SPLOM)</h2>
                <div id="splom"></div>
            </div>
            
            <div class="plot-container">
                <h2>Data Table</h2>
                <div id="table"></div>
            </div>
        </div>
    </div>

    <script>
        // Store the original data
        const csvData = {json.dumps(csv_data)};
        const yamlData = {json.dumps(yaml_data)};
        const splomFigure = {splom_json};
        const initialTableData = {table_json};
        const objectiveSenses = {json.dumps(objective_senses or {})};
        
        // Store initial data (includes all traces: data points, pareto, etc.)
        const initialData = splomFigure.data.map(trace => ({{
            ...trace,
            visible: trace.visible !== false
        }}));
        
        // Detect if Pareto trace exists and set initial state
        const hasParetoTrace = initialData.some(trace => trace.name === 'Pareto Front');
        
        // State management
        let paretoVisible = hasParetoTrace;  // Initialize based on whether Pareto exists
        let diagonalVisible = false;
        let highlightedPoint = null;
        
        // Update button text based on initial state
        if (hasParetoTrace) {{
            document.getElementById('paretoBtn').textContent = 'Hide Pareto Front';
        }} else {{
            document.getElementById('paretoBtn').textContent = 'Show Pareto Front';
            document.getElementById('paretoBtn').disabled = true;  // Disable if no Pareto data
        }}
        
        // Display objective goals
        if (yamlData && yamlData.objectives && Object.keys(objectiveSenses).length > 0) {{
            const objectiveGoalsDiv = document.getElementById('objectiveGoals');
            const goalsList = [];
            for (const [objName, sense] of Object.entries(objectiveSenses)) {{
                const simpleName = objName.split('.').pop();
                const goal = sense === 'maximize' ? 'Maximize' : 'Minimize';
                goalsList.push(`${{goal}}: ${{simpleName}}`);
            }}
            if (goalsList.length > 0) {{
                objectiveGoalsDiv.textContent = 'Optimization Goals: ' + goalsList.join(' | ');
            }}
        }}
        
        // Initialize plots with all data
        Plotly.newPlot('splom', initialData, splomFigure.layout);
        if (initialTableData.data) {{
            Plotly.newPlot('table', initialTableData.data, initialTableData.layout);
        }}
        
        // Click event handler for SPLOM
        document.getElementById('splom').on('plotly_click', function(data) {{
            if (data.points && data.points.length > 0) {{
                const point = data.points[0];
                
                // Get the point index - handle different trace types
                let pointIndex = point.pointIndex;
                
                // If clicked on Pareto or other trace, find the actual index in main data
                if (point.data.name !== 'Data Points') {{
                    const clickedValue = point.data.dimensions[0].values[point.pointIndex];
                    const mainTrace = initialData.find(t => t.name === 'Data Points');
                    if (mainTrace) {{
                        pointIndex = mainTrace.dimensions[0].values.indexOf(clickedValue);
                    }}
                }}
                
                // Update table based on clicked point
                updateTable(pointIndex);
                
                // Highlight the clicked point
                highlightPoint(pointIndex);
            }}
        }});
        
        function updateTable(iterationIndex) {{
            if (!csvData) return;
            
            // Parse CSV data
            const df = JSON.parse(csvData);
            const columns = df.columns;
            const data = df.data;
            
            // Get row data for selected iteration
            const rowData = data[iterationIndex];
            
            // Extract variable categories
            const variableCategories = {{}};
            if (yamlData) {{
                if (yamlData.objectives) {{
                    Object.keys(yamlData.objectives).forEach(key => variableCategories[key] = 'objectives');
                }}
                if (yamlData.constraints) {{
                    Object.keys(yamlData.constraints).forEach(key => variableCategories[key] = 'constraints');
                }}
                if (yamlData.design_vars) {{
                    Object.keys(yamlData.design_vars).forEach(key => variableCategories[key] = 'design_vars');
                }}
            }}
            
            // Create table data with color coding via font property
            const tableHeaders = ['Variable', 'Value'];
            const variableNames = [];
            const variableColors = [];
            const values = [];
            
            columns.forEach((col, idx) => {{
                const category = variableCategories[col] || 'other';
                let color = '#212529';
                if (category === 'objectives') color = '#0d6efd';
                else if (category === 'constraints') color = '#fd7e14';
                else if (category === 'design_vars') color = '#198754';
                
                variableNames.push(col);
                variableColors.push(color);
                values.push(rowData[idx]?.toFixed(6) || 'N/A');
            }});
            
            const tableData = [{{
                type: 'table',
                header: {{
                    values: tableHeaders,
                    align: 'left',
                    fill: {{color: '#f8f9fa'}},
                    font: {{size: 14, color: '#212529', family: 'Arial, sans-serif'}}
                }},
                cells: {{
                    values: [variableNames, values],
                    align: ['left', 'right'],
                    fill: {{color: 'white'}},
                    font: [
                        {{size: 13, family: 'Arial, sans-serif', color: variableColors}},
                        {{size: 13, family: 'Arial, sans-serif', color: '#212529'}}
                    ],
                    height: 30
                }}
            }}];
            
            const tableLayout = {{
                margin: {{t: 10, b: 10, l: 10, r: 10}},
                height: 600
            }};
            
            Plotly.newPlot('table', tableData, tableLayout);
        }}
        
        function highlightPoint(pointIndex) {{
            highlightedPoint = pointIndex;
            
            // Find the main trace to get dimensions structure
            const mainTrace = initialData.find(t => t.name === 'Data Points');
            if (!mainTrace || !mainTrace.dimensions) return;
            
            // Create highlight trace with the selected point
            const highlightDimensions = mainTrace.dimensions.map(dim => ({{
                label: dim.label,
                values: [dim.values[pointIndex]]
            }}));
            
            // Get current plot data and remove existing highlight trace
            let currentData = [...initialData].filter(trace => trace.name !== 'Highlighted');
            
            // Add new highlight trace
            const highlightTrace = {{
                type: 'splom',
                name: 'Highlighted',
                dimensions: highlightDimensions,
                marker: {{
                    color: '#2ca02c',
                    size: 12,
                    symbol: 'star',
                    line: {{color: 'black', width: 2}}
                }},
                diagonal: {{visible: diagonalVisible}},
                showupperhalf: true,
                showlowerhalf: false
            }};
            
            currentData.push(highlightTrace);
            
            // Update the plot with new highlight
            Plotly.react('splom', currentData, splomFigure.layout);
        }}
        
        function clearHighlight() {{
            highlightedPoint = null;
            
            // Remove highlight trace - keep all original traces
            const currentData = initialData.filter(trace => trace.name !== 'Highlighted');
            Plotly.react('splom', currentData, splomFigure.layout);
            
            // Clear table
            Plotly.purge('table');
            const emptyLayout = {{
                annotations: [{{
                    text: 'Click on a data point in the SPLOM to see detailed analysis',
                    xref: 'paper',
                    yref: 'paper',
                    showarrow: false,
                    font: {{size: 16, color: 'gray'}}
                }}],
                xaxis: {{visible: false}},
                yaxis: {{visible: false}}
            }};
            Plotly.newPlot('table', [], emptyLayout);
        }}
        
        function togglePareto() {{
            paretoVisible = !paretoVisible;
            const btn = document.getElementById('paretoBtn');
            btn.textContent = paretoVisible ? 'Hide Pareto Front' : 'Show Pareto Front';
            
            // Get current traces from the plot
            const splomDiv = document.getElementById('splom');
            const currentData = splomDiv.data;
            
            // Toggle Pareto trace visibility
            const updatedData = currentData.map(trace => {{
                if (trace.name === 'Pareto Front') {{
                    return {{...trace, visible: paretoVisible}};
                }}
                return trace;
            }});
            
            Plotly.react('splom', updatedData, splomFigure.layout);
        }}
        
        function toggleDiagonal() {{
            diagonalVisible = !diagonalVisible;
            const btn = document.getElementById('diagonalBtn');
            btn.textContent = diagonalVisible ? 'Hide Diagonal' : 'Show Diagonal';
            
            // Get current traces from the plot
            const splomDiv = document.getElementById('splom');
            const currentData = splomDiv.data;
            
            // Update all traces diagonal visibility
            const updatedData = currentData.map(trace => ({{
                ...trace,
                diagonal: {{visible: diagonalVisible}}
            }}));
            
            Plotly.react('splom', updatedData, splomFigure.layout);
        }}
    </script>
</body>
</html>
"""
        
        # Return the HTML content for download
        return dict(content=html_content, filename=filename)


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
