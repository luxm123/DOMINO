import time
import threading
from .lambda_client import LambdaClient
from .event_logger import EventLogger

class WorkflowExecutor:
    def __init__(self, lambda_client, state_manager=None):
        self.client = lambda_client
        self.state_manager = state_manager
        self.logger = EventLogger()

    def execute_chain(self, chain, ping_others=False):
        """
        Execute a linear chain of functions.
        If ping_others is True, it will ping subsequent functions to keep them warm
        while the current function is running (Scenario C/D control).
        """
        results = []
        workflow_start = time.time()
        
        for i, func_name in enumerate(chain):
            ping_threads = []
            if ping_others and i < len(chain) - 1:
                # Start pinging subsequent functions
                remaining = chain[i+1:]
                for target in remaining:
                    t = threading.Thread(target=self._keep_warm, args=(target,))
                    t.daemon = True
                    t.start()
                    ping_threads.append(t)
            
            # Execute current function
            step_start = time.time()
            res = self.client.invoke(func_name)
            step_end = time.time()
            
            res['step_latency_ms'] = (step_end - step_start) * 1000
            res['function_name'] = func_name
            results.append(res)
            
            # Wait for ping threads if needed (though they are daemon)
            # In practice, we just move to the next function
        
        workflow_end = time.time()
        total_latency = (workflow_end - workflow_start) * 1000
        
        return {
            'total_latency_ms': total_latency,
            'steps': results
        }

    def _keep_warm(self, function_name):
        """
        Periodically ping a function to keep it warm.
        """
        while True:
            self.client.invoke(function_name, payload={'warmup': True})
            time.sleep(180) # Ping every 3 minutes
