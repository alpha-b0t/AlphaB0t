# Kraken API errors
class KrakenAPIInvalidKeyError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenAPIInvalidKeyError: {self.args[0]}"

class KrakenAPIInvalidSignatureError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenAPIInvalidSignatureError: {self.args[0]}"

class KrakenAPIInvalidNonceError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenAPIInvalidNonceError: {self.args[0]}"

class KrakenPermissionDeniedError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenPermissionDeniedError: {self.args[0]}"

class KrakenInvalidArgumentsError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenInvalidArgumentsError: {self.args[0]}"

class KrakenCannotOpenOrderError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenCannotOpenOrderError: {self.args[0]}"

class KrakenInsufficientFundsError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenInsufficientFundsError: {self.args[0]}"

class KrakenOrderMinimumNotMetError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderMinimumNotMetError: {self.args[0]}"

class KrakenCostMinimumNotMetError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenCostMinimumNotMetError: {self.args[0]}"

class KrakenTickSizeCheckFailedError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenTickSizeCheckFailedError: {self.args[0]}"

class KrakenOrdersLimitExceededError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrdersLimitExceededError: {self.args[0]}"

class KrakenRateLimitExceededError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenRateLimitExceededError: {self.args[0]}"

class KrakenDomainRateLimitExceededError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenDomainRateLimitExceededError: {self.args[0]}"

class KrakenServiceUnavailableError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenServiceUnavailableError: {self.args[0]}"

class KrakenServiceMarketCancelOnlyError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenServiceMarketCancelOnlyError: {self.args[0]}"

class KrakenServiceMarketPostOnlyError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenServiceMarketPostOnlyError: {self.args[0]}"

class KrakenServiceDeadlineElapsedError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenServiceDeadlineElapsedError: {self.args[0]}"