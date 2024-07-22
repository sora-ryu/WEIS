'''
Various functions for help visualizing WEIS outputs
'''
from weis.aeroelasticse.FileTools import load_yaml
import pandas as pd
import numpy as np
import openmdao.api as om
import plotly.graph_objects as go
import os
import io
import yaml
import re
import socket
from dash import html
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
import pickle
import raft

try:
    import ruamel_yaml as ry
except Exception:
    try:
        import ruamel.yaml as ry
    except Exception:
        raise ImportError('No module named ruamel.yaml or ruamel_yaml')


def checkPort(port, host="0.0.0.0"):
    # check port availability and then close the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.bind((host, port))
        result = True
    except:
        result = False

    sock.close()
    return result


def parse_yaml(file_path):
    '''
    Parse the data contents in dictionary format
    '''
    # print('Reading the input yaml file..')
    try:
        with io.open(file_path, 'r') as stream:
            dict = yaml.safe_load(stream)
        
        dict['yamlPath'] = file_path
        # print('input file dict:\n', dict)
        return dict
    
    except FileNotFoundError:
        print('Could not locate the input yaml file..')
        exit()
    
    except Exception as e:
        print(e)
        exit()


def dict_to_html(data, out_html_list, level):
    '''
    Show the nested dictionary data to html
    '''

    # return [html.H5(f'Heading {i+1}') for i in range(5)]        # Works!! -- no big line gap
    # return [html.H5(f'{a}') for a, b in data.items()]       # Works
    for k1, v1 in data.items():
        if not k1 in ['dirs', 'files']:
            # out_html_list.append(html.Pre(html.B(html.P(f'{'   '*level}{k1}'))))      # Big line gap
            if not isinstance(v1, list) and not isinstance(v1, dict):
                out_html_list.append(html.H6(f'{'---'*level}{k1}: {v1}'))
                continue
            
            out_html_list.append(html.H6(f'{'---'*level}{k1}'))
        
        if isinstance(v1, list):
            '''
            out_html_list.append(html.Div([
                                    html.Pre(html.P(f'{'   '*(level+1)}{i}')) for i in v1],
                                    style={'border-width':'1px', 'border-style':'solid', 'border-color':'black', 'marginTop': 0, 'marginBottom': 0, 'paddingTop': 0, 'paddingBottom': 0}))
            '''
            out_html_list.append(html.Div([
                                    html.H6(f'{'---'*(level+1)}{i}') for i in v1]))
            
        elif isinstance(v1, dict):
            out_html_list = dict_to_html(v1, out_html_list, level+1)
        # else:
        #     out_html_list.append(html.Hr())

    return out_html_list

    '''
    for a, b in data.items():
        print('key: ', a)
        # First level - outputDirStructure, userOptions, userPreferences, yamlPath
        # yield '{}{}(\'{}\'),'.format(html.H5, '   '*c, a)
        yield ['{},'.format(html.H5(a))]
        # if isinstance(b, dict):
        #         yield 'html.Div([\n{}html.P({}))'.format('    '*c, '\n'.join(dict_to_html(b, c+1)))

    '''

def read_cm(cm_file):
    """
    Function originally from:
    https://github.com/WISDEM/WEIS/blob/main/examples/16_postprocessing/rev_DLCs_WEIS.ipynb

    Parameters
    __________
    cm_file : The file path for case matrix

    Returns
    _______
    cm : The dataframe of case matrix
    dlc_inds : The indices dictionary indicating where corresponding dlc is used for each run
    """
    cm_dict = load_yaml(cm_file, package=1)
    cnames = []
    for c in list(cm_dict.keys()):
        if isinstance(c, ry.comments.CommentedKeySeq):
            cnames.append(tuple(c))
        else:
            cnames.append(c)
    cm = pd.DataFrame(cm_dict, columns=cnames)
    
    return cm

def parse_contents(data):
    """
    Function from:
    https://github.com/WISDEM/WEIS/blob/main/examples/09_design_of_experiments/postprocess_results.py
    """
    collected_data = {}
    for key in data.keys():
        if key not in collected_data.keys():
            collected_data[key] = []
        
        for key_idx, _ in enumerate(data[key]):
            if isinstance(data[key][key_idx], int):
                collected_data[key].append(np.array(data[key][key_idx]))
            elif len(data[key][key_idx]) == 1:
                try:
                    collected_data[key].append(np.array(data[key][key_idx][0]))
                except:
                    collected_data[key].append(np.array(data[key][key_idx]))
            else:
                collected_data[key].append(np.array(data[key][key_idx]))
    
    df = pd.DataFrame.from_dict(collected_data)

    return df


def load_OMsql(log):
    """
    Function from :
    https://github.com/WISDEM/WEIS/blob/main/examples/09_design_of_experiments/postprocess_results.py
    """
    # logging.info("loading ", log)
    cr = om.CaseReader(log)
    rec_data = {}
    cases = cr.get_cases('driver')
    for case in cases:
        for key in case.outputs.keys():
            if key not in rec_data:
                rec_data[key] = []
            rec_data[key].append(case[key])
    
    return rec_data


def read_per_iteration(iteration, stats_paths):

    stats_path_matched = [x for x in stats_paths if f'iteration_{iteration}' in x][0]
    iteration_path = '/'.join(stats_path_matched.split('/')[:-1])
    stats = pd.read_pickle(stats_path_matched)
    # dels = pd.read_pickle(iteration_path+'/DELs.p')
    # fst_vt = pd.read_pickle(iteration_path+'/fst_vt.p')
    print('iteration path with ', iteration, ': ', stats_path_matched)

    return stats, iteration_path


def get_timeseries_data(run_num, stats, iteration_path):
    
    stats = stats.reset_index()     # make 'index' column that has elements of 'IEA_22_Semi_00, ...'
    filename = stats.loc[run_num, 'index'].to_string()      # filenames are not same - stats: IEA_22_Semi_83 / timeseries/: IEA_22_Semi_0_83.p
    if filename.split('_')[-1].startswith('0'):
        filename = ('_'.join(filename.split('_')[:-1])+'_0_'+filename.split('_')[-1][1:]+'.p').strip()
    else:
        filename = ('_'.join(filename.split('_')[:-1])+'_0_'+filename.split('_')[-1]+'.p').strip()
    
    # visualization_demo/openfast_runs/rank_0/iteration_0/timeseries/IEA_22_Semi_0_0.p
    timeseries_path = '/'.join([iteration_path, 'timeseries', filename])
    timeseries_data = pd.read_pickle(timeseries_path)

    return filename, timeseries_data


def empty_figure():
    '''
    Draw empty figure showing nothing once initialized
    '''
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)

    return fig


def toggle(click, is_open):
    if click:
        return not is_open
    return is_open


def store_dataframes(var_files):
    dfs = []
    for idx, file_path in var_files.items():
        if file_path == 'None':
            dfs.append({idx: []})
            continue
        df = pd.read_csv(file_path, skiprows=[0,1,2,3,4,5,7], sep='\s+')
        dfs.append({idx: df.to_dict('records')})
    
    return dfs


def get_file_info(file_path):
    file_name = file_path.split('/')[-1]
    file_abs_path = os.path.abspath(file_path)
    file_size = round(os.path.getsize(file_path) / (1024**2), 2)
    creation_time = os.path.getctime(file_path)
    modification_time = os.path.getmtime(file_path)

    file_info = {
        'file_name': file_name,
        'file_abs_path': file_abs_path,
        'file_size': file_size,
        'creation_time': creation_time,
        'modification_time': modification_time
    }

    return file_info


def find_file_path_from_tree(nested_dict, filename, prepath=()):
    # Works for multi-keyed files
    # Sample outputs: ('outputDirStructure', 'sample_test') ('outputDirStructure', 'sample_multi')
    for k, v in nested_dict.items():
        path = prepath + (k,)
        if v == filename:
            yield path + (v, )
        elif isinstance(v, list) and filename in v:
            yield path + (filename, )
        elif hasattr(v, 'items'):
            yield from find_file_path_from_tree(v, filename, path)

def find_iterations(nested_dict, prepath=()):
    for k, v in nested_dict.items():
        path = prepath + (k,)
        if 'iteration' in k:
            yield int(re.findall(r'\d+', k)[0])
        elif hasattr(v, 'items'):
            yield from find_iterations(v, path)


def update_yaml(input_dict, yaml_filepath):
    with open(yaml_filepath, 'w') as outfile:
        yaml.dump(input_dict, outfile, default_flow_style=False)


def read_cost_variables(labels, refturb_variables):
    # Read tcc cost-related variables from CSV file

    cost_matrix = [['Main Turbine Components', 'Cost']]

    for l in labels:
        cost_matrix.append([l, eval(refturb_variables[f'tcc.{l}_cost']['values'])[0]])
    
    return cost_matrix


def generate_raft_img(raft_design_dir, log_data):

    n_plots = len(os.listdir(raft_design_dir))
    print('n_plots: ', n_plots)

    image_filenames = []
    plot_dir = os.path.join(raft_design_dir,'..','raft_plots')
    os.makedirs(plot_dir,exist_ok=True)

    opt_outs = {}
    opt_outs['max_pitch'] = np.squeeze(np.array(log_data['raft.Max_PtfmPitch']))
    opt_outs['draft'] = -np.squeeze(np.array(log_data['floating.jointdv_0']))
    opt_outs['spacing'] = np.squeeze(np.array(log_data['floating.jointdv_1']))
    opt_outs['diam'] = np.squeeze(np.array(log_data['floating.memgrp1.outer_diameter_in']))
    opt_outs['mass'] = np.squeeze(np.array(log_data['floatingse.system_structural_mass']))

    for i_plot in range(n_plots):
        # Set up subplots
        fig = plt.figure()
        fig.patch.set_facecolor('white')
        gs = GridSpec(5, 2, figure=fig, wspace= 0.3)

        axs = {}
        axs['ptfm'] = fig.add_subplot(gs[1:, 0],projection='3d')
        axs['draft'] = fig.add_subplot(gs[0, 1])
        axs['spacing'] = fig.add_subplot(gs[1, 1])
        axs['diam'] = fig.add_subplot(gs[2, 1])
        axs['max_pitch'] = fig.add_subplot(gs[3, 1])
        axs['mass'] = fig.add_subplot(gs[4, 1])

        
        with open(os.path.join(raft_design_dir,f'raft_design_{i_plot}.pkl'),'rb') as f:
            design = pickle.load(f)

        # print('===== design:\n', design)
        # for k, v in design.items():
        #     print('---', k)
        #     if k == 'turbine':
        #         print('gamma: ', v['tower'])

        # TODO: Found typo on gamma value at 1_raft_opt example
        design['turbine']['tower']['gamma'] = 0.0       # Change it from array([0.])
        
        # set up the model
        model1 = raft.Model(design)
        model1.analyzeUnloaded(
            ballast= False, 
            heave_tol = 1.0
            )

        model1.fowtList[0].r6[4] = np.radians(opt_outs['max_pitch'][i_plot])
        

        fix, axs['ptfm'] = model1.plot(ax=axs['ptfm'])

        # if False:
        #     print('Set breakpoint here and find nice camera angle')

        #     azm=axs['ptfm'].azim
        #     ele=axs['ptfm'].elev

        #     xlm=axs['ptfm'].get_xlim3d() #These are two tupples
        #     ylm=axs['ptfm'].get_ylim3d() #we use them in the next
        #     zlm=axs['ptfm'].get_zlim3d() #graph to reproduce the magnification from mousing

        #     print(f"axs['ptfm'].azim = {axs['ptfm'].azim}")
        #     print(f"axs['ptfm'].elev = {axs['ptfm'].elev}")
        #     print(f"axs['ptfm'].set_xlim3d({xlm})")
        #     print(f"axs['ptfm'].set_ylim3d({ylm})")
        #     print(f"axs['ptfm'].set_zlim3d({zlm})")

        print('Setting ')
        axs['ptfm'].azim = -88.63636363636361
        axs['ptfm'].elev = 27.662337662337674
        axs['ptfm'].set_xlim3d((-110.90447789470043, 102.92063063344857))
        axs['ptfm'].set_ylim3d((64.47420067304586, 311.37818252335893))
        axs['ptfm'].set_zlim3d((-88.43591080818854, -57.499893019459606))


        # Plot convergences
        for out in opt_outs:
            axs[out].plot(np.arange(i_plot+1),opt_outs[out][:i_plot+1],'.')
            axs[out].set_xlabel('')
            axs[out].set_xlim(0,n_plots)
            axs[out].set_ylabel(out)

        r = 45
        lp = 20
        axs['draft'].set_ylabel('Draft (m)',rotation=r, labelpad=lp)
        axs['spacing'].set_ylabel('Col. Spacing (m)',rotation=r, labelpad=lp)
        axs['diam'].set_ylabel('Col. Diam. (m)',rotation=r, labelpad=lp)
        axs['max_pitch'].set_ylabel('Max Pitch (deg.)',rotation=r, labelpad=lp)
        axs['mass'].set_ylabel('Struct Mass (kg)',rotation=r, labelpad=lp)

        axs['draft'].set_xticklabels('')
        axs['spacing'].set_xticklabels('')
        axs['diam'].set_xticklabels('')
        axs['max_pitch'].set_xticklabels('')

        axs['max_pitch'].axhline(6,color='k',linestyle='--')

        fig.set_size_inches(11,6)
        fig.align_ylabels()
        
        image_filename = os.path.join(plot_dir,f'ptfm_{i_plot}.png')
        plt.savefig(image_filename, bbox_inches='tight')
        print('saved ', image_filename)