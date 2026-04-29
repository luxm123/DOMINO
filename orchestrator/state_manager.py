from enum import Enum

class FunctionStatus(Enum):
    UNKNOWN = "UNKNOWN"
    HOT = "HOT"
    COLD = "COLD"

class StateManager:
    def __init__(self):
        self.states = {} # function_name -> FunctionStatus
        self.last_invoke_time = {} # function_name -> timestamp
        self.params = {} # function_name -> {mu, sigma, delta}

    def update_state(self, function_name, status):
        self.states[function_name] = status

    def get_state(self, function_name):
        return self.states.get(function_name, FunctionStatus.UNKNOWN)

    def record_invoke(self, function_name):
        import time
        self.last_invoke_time[function_name] = time.time()

    def set_params(self, function_name, mu, sigma, delta):
        self.params[function_name] = {
            'mu': mu,
            'sigma': sigma,
            'delta': delta
        }

    def is_cold(self, function_name, duration_ms):
        """
        Check if an execution was cold based on duration.
        """
        if function_name not in self.params:
            return None
        
        p = self.params[function_name]
        return duration_ms > (p['mu'] + 2 * p['sigma'])
