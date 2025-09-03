# Dashboard for Multi Objective Optimization

This is having the same coding environment as WEIS Input/Output Viz tool (appServer/) where it's mainly based on Dash and Plotly. This is separate and works independently for now, but could be potentially merged later.

## Action Items
- [X] Data Upload
- [X] Dynamic Scatter plot matrix renderer with toggle buttons - channel multi-selection from the user
- [X] Link samples
    - [X] Highlight samples once clicked
    - [X] Maybe add text field to show all information on that iteration
- [ ] Show Pareto Fronts
    - [ ] Calculate from scratch with checking constraints bounds
- [ ] Download interactive version of html
- [ ] How to visualize array values? (e.g., constr_fixed_margin, constr_draft_heel_margin, etc.)
    - [ ] Show dropdown list when array-value channel is clicked (combined single plot vs separated plots) either way, show both min and max where constraints bounds (min < min, max > max) are already checked

- How to calculate Pareto Fronts with 3 objective functions?
    - Should be okay with Cory's function
    - For cross checking, we need SPLOM visualization

## Food for Thoughts
- How to work on 3+ objectives?
- 3D+ Pareto Fronts?
- Connect all of the optimization results (DoE, DLC, Timeseries, etc.)
