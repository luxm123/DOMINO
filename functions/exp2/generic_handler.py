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
    func_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'unknown')
    
    # Define "Heavy" configurations for Exp 2 (Real-world scenarios)
    # init_ms: Simulated package loading time (OpenCV, Torch, etc.)
    # exec_ms: Simulated computation time
    configs = {
        # Video Analytics Chain
        'v_a': {'init_ms': 8000, 'exec_ms': 5000},  # Loading OpenCV + moviepy
        'v_b': {'init_ms': 15000, 'exec_ms': 10000}, # Loading PyTorch + ResNet50
        'v_c': {'init_ms': 2000, 'exec_ms': 1000},  # Simple post-processing
        
        # Image Pipeline Fanout
        'i_a': {'init_ms': 4000, 'exec_ms': 3000},  # Loading PIL + Pre-processing
        'i_b': {'init_ms': 12000, 'exec_ms': 8000}, # Loading CLIP (Model 1)
        'i_c': {'init_ms': 12000, 'exec_ms': 8000}, # Loading CLIP (Model 2)
        'i_d': {'init_ms': 3000, 'exec_ms': 2000},  # Aggregation
        
        # NLP Chat Branch
        'e_a': {'init_ms': 5000, 'exec_ms': 3000},  # Loading tokenizers
        'e_b': {'init_ms': 18000, 'exec_ms': 12000},# Loading Transformers (ZH)
        'e_c': {'init_ms': 18000, 'exec_ms': 12000},# Loading Transformers (EN)
        'e_d': {'init_ms': 2000, 'exec_ms': 1000}   # Output formatter
    }
    
    config = configs.get(func_name, {'init_ms': 3000, 'exec_ms': 2000})
    return get_response(event, context, config['exec_ms'], config['init_ms'])
