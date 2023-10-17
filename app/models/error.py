# Kraken API errors

# General errors
class KrakenGeneralInternalError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenGeneralInternalError: {self.args[0]}"

class KrakenGeneralUnknownMethodError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenGeneralUnknownMethodError: {self.args[0]}"

class KrakenGeneralInvalidArgumentsError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenGeneralInvalidArgumentsError: {self.args[0]}"

class KrakenGeneralInvalidArgumentsIndexUnavailableError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenGeneralInvalidArgumentsIndexUnavailableError: {self.args[0]}"

class KrakenGeneralPermissionDeniedError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenGeneralPermissionDeniedError: {self.args[0]}"

class KrakenGeneralTemporaryLockoutError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenGeneralTemporaryLockoutError: {self.args[0]}"

# Service errors
class KrakenServiceUnavailableError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenServiceUnavailableError: {self.args[0]}"

class KrakenServiceBusyError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenServiceBusyError: {self.args[0]}"

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

# API errors
class KrakenAPIBadRequestError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenAPIBadRequestError: {self.args[0]}"

class KrakenAPIRateLimitExceededError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenAPIRateLimitExceededError: {self.args[0]}"

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

class KrakenAPIFeatureDisabledError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenAPIFeatureDisabledError: {self.args[0]}"

# Order errors
class KrakenOrderCannotOpenOrderError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderCannotOpenOrderError: {self.args[0]}"

class KrakenOrderCannotOpenOpposingPositionError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderCannotOpenOpposingPositionError: {self.args[0]}"

class KrakenOrderInsufficientFundsError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderInsufficientFundsError: {self.args[0]}"

class KrakenOrderMinimumNotMetError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderMinimumNotMetError: {self.args[0]}"

class KrakenOrderCostMinimumNotMetError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderCostMinimumNotMetError: {self.args[0]}"

class KrakenOrderTickSizeCheckFailedError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderTickSizeCheckFailedError: {self.args[0]}"

class KrakenOrderOrdersLimitExceededError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderOrdersLimitExceededError: {self.args[0]}"

class KrakenOrderRateLimitExceededError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderRateLimitExceededError: {self.args[0]}"

class KrakenOrderDomainRateLimitExceededError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderDomainRateLimitExceededError: {self.args[0]}"

class KrakenOrderPositionsLimitExceededError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderPositionsLimitExceededError: {self.args[0]}"

class KrakenOrderUnknownPositionError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderUnknownPositionError: {self.args[0]}"

class KrakenOrderOrderNotEditableError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderOrderNotEditableError: {self.args[0]}"

class KrakenOrderNotEnoughLeavesQtyError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenOrderNotEnoughLeavesQtyError: {self.args[0]}"

# Funding errors
class KrakenFundingFailedError(Exception):
    def __init__(self, message):
        super().__init__(message)
    
    def __str__(self):
        return f"KrakenFundingFailedError: {self.args[0]}"

class KrakenFundingMaxFeeExceededError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenFundingMaxFeeExceededError: {self.args[0]}"

# Query errors
class KrakenQueryUnknownAssetPairError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenQueryUnknownAssetPairError: {self.args[0]}"

# Session errors
class KrakenSessionInvalidSessionError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenSessionInvalidSessionError: {self.args[0]}"

# Trade errors
class KrakenTradeLockedError(Exception):
    def __init__(self, message):
        super.__init__(message)
    
    def __str__(self):
        return f"KrakenTradeLockedError: {self.args[0]}"