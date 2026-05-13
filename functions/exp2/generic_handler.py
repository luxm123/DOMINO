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
    configs = {
        # Video Analytics Chain
        'v_a': {'init_ms': 15000, 'exec_ms': 5000},  # 15s init
        'v_b': {'init_ms': 25000, 'exec_ms': 10000}, # 25s init
        'v_c': {'init_ms': 10000, 'exec_ms': 2000},  # 10s init
        
        # Image Pipeline Fanout
        'i_a': {'init_ms': 10000, 'exec_ms': 3000},  
        'i_b': {'init_ms': 20000, 'exec_ms': 8000}, 
        'i_c': {'init_ms': 20000, 'exec_ms': 8000}, 
        'i_d': {'init_ms': 10000, 'exec_ms': 2000},  
        
        # NLP Chat Branch
        'e_a': {'init_ms': 10000, 'exec_ms': 3000},  
        'e_b': {'init_ms': 30000, 'exec_ms': 12000},# 30s init
        'e_c': {'init_ms': 30000, 'exec_ms': 12000},# 30s init
        'e_d': {'init_ms': 10000, 'exec_ms': 2000}   
    }
    
    config = configs.get(func_key, {'init_ms': 10000, 'exec_ms': 5000})
    return get_response(event, context, config['exec_ms'], config['init_ms'])
