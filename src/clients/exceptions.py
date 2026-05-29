class RiotBaseException(Exception):
    """Basic exception for all Riot API related errors"""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class RiotKeyExpiredError(RiotBaseException):
    """
    Raised when the Riot Development API key has expired or is invalid (403).
    """

    pass


class RiotRateLimitException(RiotBaseException):
    """The limit of attempts when accessing the API has been reached (429)"""

    pass


class RiotServiceUnavailableException(RiotBaseException):
    """
    We throw it away if the external network is down or Riot has
    a status of 5xx after all retrays
    """

    pass
