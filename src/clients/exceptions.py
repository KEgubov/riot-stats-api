class RiotKeyExpiredError(Exception):
    """
    Raised when the Riot Development API key has expired or is invalid (403).
    """
    pass