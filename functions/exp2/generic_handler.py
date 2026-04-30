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
    
    # Define durations for Exp 2 functions
    durations = {
        # Video
        'v_a': 500, 'v_b': 800, 'v_c': 300,
        # Image
        'i_a': 400, 'i_b': 600, 'i_c': 600, 'i_d': 300,
        # E-commerce
        'e_a': 300, 'e_b': 500, 'e_c': 500, 'e_d': 400
    }
    
    duration = durations.get(func_name, 500)
    return get_response(event, context, duration)
