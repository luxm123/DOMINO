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
    
    # Define durations for Exp 2 functions (Increased for Direction 2)
    durations = {
        # Video
        'v_a': 2000, 'v_b': 1000, 'v_c': 500,
        # Image
        'i_a': 2000, 'i_b': 800, 'i_c': 800, 'i_d': 500,
        # E-commerce
        'e_a': 2000, 'e_b': 1000, 'e_c': 1000, 'e_d': 800
    }
    
    duration = durations.get(func_name, 500)
    return get_response(event, context, duration)
