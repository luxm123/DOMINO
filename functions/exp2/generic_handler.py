import sys
import os
import json

# Add project root to path to find common.utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
try:
    from common.utils import get_response
except ImportError:
    from utils import get_response

def lambda_handler(event, context):
    full_func_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'unknown')
    
    # Matching logic: extract v_a, i_b, etc. from full function name
    func_key = 'unknown'
    for key in ['v_a', 'v_b', 'v_c', 'i_a', 'i_b', 'i_c', 'i_d', 'e_a', 'e_b', 'e_c', 'e_d']:
        if key in full_func_name:
            func_key = key
            break

    # Define "Brutal" configurations for Exp 2 (Amplify the gap)
    # Optimized for showing multi-stage pre-warming advantage:
    # exec_ms is small (500ms) to shrink the one-step-ahead window.
    # init_ms is large (10s) to make cold starts expensive.
    configs = {
        # Video Analytics Chain
        'v_a': {'init_ms': 10000, 'exec_ms': 500}, 
        'v_b': {'init_ms': 10000, 'exec_ms': 500},
        'v_c': {'init_ms': 10000, 'exec_ms': 500},
        
        # Image Pipeline Fanout
        'i_a': {'init_ms': 10000, 'exec_ms': 500},  
        'i_b': {'init_ms': 10000, 'exec_ms': 500}, 
        'i_c': {'init_ms': 10000, 'exec_ms': 500}, 
        'i_d': {'init_ms': 10000, 'exec_ms': 500},  
        
        # NLP Chat Branch
        'e_a': {'init_ms': 10000, 'exec_ms': 500},  
        'e_b': {'init_ms': 10000, 'exec_ms': 500},
        'e_c': {'init_ms': 10000, 'exec_ms': 500},
        'e_d': {'init_ms': 10000, 'exec_ms': 500}   
    }
    
    config = configs.get(func_key, {'init_ms': 10000, 'exec_ms': 5000})
    return get_response(event, context, config['exec_ms'], config['init_ms'])
