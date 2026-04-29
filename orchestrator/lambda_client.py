import boto3
import json
import time
from botocore.config import Config

class LambdaClient:
    def __init__(self, region_name='us-east-1'):
        config = Config(
            retries = {
                'max_attempts': 3,
                'mode': 'standard'
            }
        )
        self.client = boto3.client('lambda', region_name=region_name, config=config)

    def invoke(self, function_name, payload=None, async_invoke=False):
        """
        Invoke a Lambda function.
        """
        if payload is None:
            payload = {}
        
        invocation_type = 'Event' if async_invoke else 'RequestResponse'
        
        start_time = time.time()
        try:
            response = self.client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )
            end_time = time.time()
            
            if async_invoke:
                return {
                    'status': 'async_sent',
                    'start_time': start_time,
                    'end_time': end_time
                }
            
            # Read response
            payload_raw = response['Payload'].read().decode('utf-8')
            response_payload = json.loads(payload_raw)
            
            # Check for Lambda function errors
            if 'FunctionError' in response:
                print(f"Lambda Error in {function_name}: {response_payload}")
                return {
                    'status': 'error',
                    'error_type': 'function_error',
                    'payload': response_payload
                }

            # Extract duration from response body if present (added by our common utils)
            body_str = response_payload.get('body', '{}')
            try:
                body = json.loads(body_str)
            except (json.JSONDecodeError, TypeError):
                body = {}
            
            lambda_duration = body.get('duration_ms')
            
            return {
                'status': 'success',
                'start_time': start_time,
                'end_time': end_time,
                'duration_ms': (end_time - start_time) * 1000,
                'lambda_duration_ms': lambda_duration,
                'is_warmup': body.get('is_warmup', False),
                'request_id': response.get('ResponseMetadata', {}).get('RequestId'),
                'log_result': response.get('LogResult')
            }
        except Exception as e:
            print(f"Error invoking {function_name}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
