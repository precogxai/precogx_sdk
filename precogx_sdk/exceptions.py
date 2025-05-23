class PrecogXError(Exception):
    """Base exception for all PrecogX SDK errors."""
    pass

class AuthenticationError(PrecogXError):
    """Raised when there are authentication issues."""
    pass

class ValidationError(PrecogXError):
    """Raised when data validation fails."""
    pass

class APIError(PrecogXError):
    """Raised when the API returns an error."""
    pass

class ConfigurationError(PrecogXError):
    """Raised when there are configuration issues."""
    pass 