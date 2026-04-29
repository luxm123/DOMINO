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
            response_payload = json.loads(response['Payload'].read().decode('utf-8'))
            
            # Extract duration from response body if present (added by our common utils)
            body = json.loads(response_payload.get('body', '{}'))
            
            return {
                'status': 'success',
                'start_time': start_time,
                'end_time': end_time,
                'duration_ms': (end_time - start_time) * 1000,
                'lambda_duration_ms': body.get('duration_ms'),
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
