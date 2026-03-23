"""Typed exceptions for the RustChain SDK."""


class RustChainError(Exception):
    """Base exception for all RustChain SDK errors."""
    pass


class APIError(RustChainError):
    """Raised when the RustChain API returns an error response."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}

    def __repr__(self) -> str:
        return f"APIError({self.status_code}: {super().__str__()})"


class NodeUnavailableError(RustChainError):
    """Raised when the RustChain node is unreachable or returns an unhealthy status."""
    pass


class ValidationError(RustChainError):
    """Raised when request parameters fail validation."""
    pass


class TransferError(RustChainError):
    """Raised when a transfer fails."""

    def __init__(self, message: str, balance: float = None):
        super().__init__(message)
        self.balance = balance

    def __repr__(self) -> str:
        return f"TransferError({super().__str__()}, balance={self.balance})"
