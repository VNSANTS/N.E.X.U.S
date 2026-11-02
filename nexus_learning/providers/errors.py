"""Provider-neutral failures with stable codes and safe diagnostics."""
import math


class ProviderError(Exception):
    """Base error; subclasses expose only fixed, non-sensitive summaries."""

    code = "provider_request_failed"
    safe_message = "Provider request failed."
    retryable = False

    def __init__(self):
        super().__init__(self.safe_message)
        self.retry_after = None

    @property
    def safe_summary(self):
        return f"{self.code}: {self.safe_message}"


class ProviderConfigurationError(ProviderError):
    code = "provider_configuration_invalid"
    safe_message = "Provider configuration is invalid."


class ProviderAuthenticationError(ProviderError):
    code = "provider_authentication_failed"
    safe_message = "Provider authentication failed."


class ProviderRateLimitError(ProviderError):
    code = "provider_rate_limited"
    safe_message = "Provider rate limit exceeded."
    retryable = True

    def __init__(self, *, retry_after=None):
        super().__init__()
        if retry_after is not None:
            if isinstance(retry_after, bool) or not isinstance(retry_after, (int, float)):
                raise ValueError("retry_after must be a finite, non-negative number")
            try:
                normalized = float(retry_after)
            except (OverflowError, ValueError):
                raise ValueError("retry_after must be a finite, non-negative number") from None
            if not math.isfinite(normalized) or normalized < 0:
                raise ValueError("retry_after must be a finite, non-negative number")
            self.retry_after = normalized


class ProviderTimeoutError(ProviderError):
    code = "provider_timeout"
    safe_message = "Provider request timed out."
    retryable = True


class ProviderUnavailableError(ProviderError):
    code = "provider_unavailable"
    safe_message = "Provider is temporarily unavailable."
    retryable = True


class ProviderResponseError(ProviderError):
    code = "provider_response_invalid"
    safe_message = "Provider returned an invalid response."


class ProviderModelNotFoundError(ProviderError):
    code = "provider_model_not_found"
    safe_message = "The selected model is unavailable from this provider."
