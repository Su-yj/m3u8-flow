from httpx_retries import Retry, RetryTransport


def get_transport(
    total: int = 5,
    backoff_factor: float = 0.5,
    status_forcelist: list[int] = [400, 401, 402, 403, 408, 429, 500, 502, 503, 504],
) -> RetryTransport:
    retry = Retry(
        total=total,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    transport = RetryTransport(retry=retry)
    return transport
