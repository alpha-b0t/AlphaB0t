import time

class ErrorQueueLimitExceededError(Exception):
    def __init__(self, message):
        super().__init__(message)
    
    def __str__(self):
        return f"ErrorQueueLimitExceededError: {self.args[0]}"

class ErrorQueue():
    def __init__(self, latency, limit):
        assert type(latency) == float or type(latency) == int
        assert latency > 0
        assert type(limit) == int
        assert limit > 0
        
        self.queue = []
        self.latency = latency
        self.limit = limit
        return
    
    def __repr__(self):
        return '{queue: ' + repr(self.queue) + ', latency: ' + str(self.latency) + ', limit: ' + str(self.limit) + '}'
    
    def __str__(self):
        return repr(self.queue)
    
    def __len__(self):
        return len(self.queue)
    
    def update(self):
        current_time = time.time()
        
        remove_before = 0
        for i in range(len(self.queue)):
            if current_time - self.queue[i] >= self.latency:
                remove_before = i+1
            else:
                break
        
        if remove_before != 0:
            self.queue = self.queue[remove_before:]
        return
    
    def append(self, data):
        if not self.is_full():
            self.queue.append(data)
        return
    
    def is_full(self):
        if len(self.queue) < self.limit:
            return False
        elif len(self.queue) == self.limit:
            return True
        else:
            raise ErrorQueueLimitExceededError("There are too many items in the ErrorQueue. ErrorQueue length: " + str(len(self.queue)) + ", ErrorQueue limit: " + str(self.limit))
        return
