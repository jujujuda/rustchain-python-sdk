"""
RustChain Python SDK
~~~~~~~~~~~~~~~~~~~~
A Python SDK for interacting with RustChain nodes.

Usage:
    >>> import rustchain
    >>> client = rustchain.Client()
    >>> health = client.health()
    >>> print(health)
"""

__version__ = "0.1.0"
__author__ = "RustChain Bounty Hunter"

from rustchain.client import Client, AsyncClient
from rustchain.exceptions import (
    RustChainError,
    APIError,
    NodeUnavailableError,
    ValidationError,
)

__all__ = [
    "Client",
    "AsyncClient",
    "RustChainError",
    "APIError",
    "NodeUnavailableError",
    "ValidationError",
]
