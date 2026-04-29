import sys
import os

# Add common to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.utils import get_response

def lambda_handler(event, context):
    # Function B: ~800ms
    return get_response(event, context, 800)
