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

    def force_cold_start(self, function_name):
        """
        Force a cold start by updating function environment variables.
        """
        try:
            # Add or update a dummy environment variable to force a new deployment
            import uuid
            self.client.update_function_configuration(
                FunctionName=function_name,
                Environment={
                    'Variables': {
                        'FORCE_COLD_START': str(uuid.uuid4())
                    }
                }
            )
            # Wait for the function to finish updating
            waiter = self.client.get_waiter('function_updated')
            waiter.wait(FunctionName=function_name)
            return True
        except Exception as e:
            print(f"Error forcing cold start for {function_name}: {e}")
            return False

    def invoke(self, function_name, payload=None, async_invoke=False):
        """
        Invoke a Lambda function with retry for resource conflicts.
        """
        if payload is None:
            payload = {}
        
        invocation_type = 'Event' if async_invoke else 'RequestResponse'
        
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
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
                        'function_name': function_name,
                        'start_time': start_time,
                        'end_time': end_time
                    }
                
                # Read response
                payload_raw = response['Payload'].read().decode('utf-8')
                response_payload = json.loads(payload_raw)
                
                # Check for Lambda function errors
                if 'FunctionError' in response:
                    return {
                        'status': 'error',
                        'function_name': function_name,
                        'error_type': 'function_error',
                        'payload': response_payload
                    }

                # Extract duration from response body if present
                body_str = response_payload.get('body', '{}')
                try:
                    body = json.loads(body_str)
                except (json.JSONDecodeError, TypeError):
                    body = {}
                
                return {
                    'status': 'success',
                    'function_name': function_name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_ms': (end_time - start_time) * 1000,
                    'lambda_duration_ms': body.get('duration_ms'),
                    'is_warmup': body.get('is_warmup', False),
                    'request_id': response.get('ResponseMetadata', {}).get('RequestId')
                }
            except self.client.exceptions.ResourceConflictException:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise
            except Exception as e:
                return {
                    'status': 'error',
                    'function_name': function_name,
                    'error': str(e)
                }
