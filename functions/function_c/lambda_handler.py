import sys
import os

try:
    from common.utils import get_response
except ImportError:
    from utils import get_response

def lambda_handler(event, context):
    # Function C: ~300ms
    return get_response(event, context, 300)
