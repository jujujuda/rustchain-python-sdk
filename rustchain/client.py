"""
RustChain Python SDK — Main Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sync and async clients for interacting with RustChain nodes.
"""

import asyncio
import time
from typing import List, Optional, Dict, Any, Iterator
from urllib.parse import urljoin

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from rustchain.exceptions import (
    RustChainError,
    APIError,
    NodeUnavailableError,
    ValidationError,
    TransferError,
)
from rustchain.models import (
    Health,
    Epoch,
    Miner,
    Balance,
    Block,
    AttestationStatus,
    TransferResult,
)


class Client:
    """
    Synchronous RustChain client.

    Usage::

        >>> import rustchain
        >>> client = rustchain.Client(node_url="https://50.28.86.131")
        >>> health = client.health()
        >>> print(health.version)
        2.2.1-rip200
    """

    def __init__(
        self,
        node_url: str = "https://50.28.86.131",
        timeout: float = 10.0,
        verify: bool = True,
    ):
        """
        Initialize the RustChain client.

        Args:
            node_url: Base URL of the RustChain node (default: primary node)
            timeout: Request timeout in seconds
            verify: Whether to verify SSL certificates
        """
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required. Install it with: pip install httpx"
            )
        self.node_url = node_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.node_url,
            timeout=timeout,
            verify=verify,
            follow_redirects=True,
        )

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request and handle errors."""
        url = urljoin(self.node_url + "/", path.lstrip("/"))
        try:
            resp = self._client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            try:
                body = e.response.json()
            except Exception:
                body = {}
            raise APIError(
                f"API error {e.response.status_code}: {e.response.text[:200]}",
                status_code=e.response.status_code,
                response=body,
            )
        except httpx.RequestError as e:
            raise NodeUnavailableError(f"Failed to connect to {url}: {e}")

    def _get(self, path: str, params: Dict = None) -> Dict[str, Any]:
        return self._request("GET", path, params=params)

    def _post(self, path: str, json: Dict = None) -> Dict[str, Any]:
        return self._request("POST", path, json=json)

    # ── Node Health ────────────────────────────────────────────────────────────

    def health(self) -> Health:
        """
        Check node health and uptime.

        Returns:
            Health object with node status details.

        Example::

            >>> h = client.health()
            >>> print(h.version, h.is_healthy())
            2.2.1-rip200 True
        """
        data = self._get("/health")
        return Health.from_dict(data)

    # ── Epoch ─────────────────────────────────────────────────────────────────

    def epoch(self) -> Epoch:
        """
        Get current epoch information.

        Returns:
            Epoch object with slot, epoch number, and supply data.

        Example::

            >>> ep = client.epoch()
            >>> print(f"Epoch {ep.epoch}, Slot {ep.slot}")
            Epoch 110, Slot 15919
        """
        data = self._get("/epoch")
        return Epoch.from_dict(data)

    # ── Miners ────────────────────────────────────────────────────────────────

    def miners(self) -> List[Miner]:
        """
        List all enrolled miners.

        Returns:
            List of Miner objects.

        Example::

            >>> miners = client.miners()
            >>> print(f"{len(miners)} miners enrolled")
            22 miners enrolled
        """
        data = self._get("/api/miners")
        if isinstance(data, list):
            return [Miner.from_dict(m) for m in data]
        return []

    def miner(self, miner_id: str) -> Optional[Miner]:
        """
        Get a specific miner by ID.

        Args:
            miner_id: The miner ID (wallet name).

        Returns:
            Miner object or None if not found.
        """
        miners = self.miners()
        for m in miners:
            if m.miner == miner_id:
                return m
        return None

    # ── Balance ───────────────────────────────────────────────────────────────

    def balance(self, wallet_id: str) -> Balance:
        """
        Check the RTC balance for a wallet.

        Args:
            wallet_id: The wallet ID (miner_id / address name).

        Returns:
            Balance object with amount.

        Example::

            >>> bal = client.balance("my-wallet")
            >>> print(f"Balance: {bal.amount_rtc} RTC")
            Balance: 0.0 RTC
        """
        if not wallet_id:
            raise ValidationError("wallet_id cannot be empty")
        data = self._get("/wallet/balance", params={"miner_id": wallet_id})
        return Balance.from_dict(data)

    # ── Attestation ───────────────────────────────────────────────────────────

    def attestation_status(self, miner_id: str) -> Optional[AttestationStatus]:
        """
        Get attestation status for a miner.

        Args:
            miner_id: The miner ID to check.

        Returns:
            AttestationStatus or None if miner not found.
        """
        miner = self.miner(miner_id)
        if miner is None:
            return None
        return AttestationStatus(
            miner_id=miner.miner,
            enrolled=True,
            last_attest=miner.last_attest,
            first_attest=miner.first_attest,
            antiquity_multiplier=miner.antiquity_multiplier,
            device_arch=miner.device_arch,
        )

    def submit_attestation(self, miner_id: str, signature: str) -> Dict[str, Any]:
        """
        Submit an attestation for a miner.

        Args:
            miner_id: The miner ID submitting the attestation.
            signature: Ed25519 signature of the attestation payload.

        Returns:
            API response dict.
        """
        return self._post("/attest/submit", json={
            "miner_id": miner_id,
            "signature": signature,
        })

    # ── Transfer ──────────────────────────────────────────────────────────────

    def transfer(
        self,
        from_wallet: str,
        to_wallet: str,
        amount: float,
        signature: str,
    ) -> TransferResult:
        """
        Submit a signed RTC transfer.

        Args:
            from_wallet: Sender wallet ID.
            to_wallet: Recipient wallet ID.
            amount: Amount of RTC to transfer.
            signature: Ed25519 signature of the transfer payload.

        Returns:
            TransferResult with success status and tx hash.

        Raises:
            TransferError: If the transfer fails.
        """
        if amount <= 0:
            raise ValidationError("Transfer amount must be positive")
        data = self._post("/wallet/transfer/signed", json={
            "from": from_wallet,
            "to": to_wallet,
            "amount": amount,
            "signature": signature,
        })
        result = TransferResult.from_dict(data)
        if not result.success:
            raise TransferError(
                result.message,
                balance=self.balance(from_wallet).amount_rtc
                if result.from_wallet else None,
            )
        return result

    # ── Explorer ─────────────────────────────────────────────────────────────

    def blocks(self, limit: int = 20) -> List[Block]:
        """
        Fetch recent blocks (if endpoint available).

        Args:
            limit: Maximum number of blocks to return.

        Returns:
            List of Block objects.
        """
        # Endpoint may not exist on all nodes — fall back gracefully
        try:
            data = self._get("/api/blocks", params={"limit": limit})
            if isinstance(data, list):
                return [Block.from_dict(b) for b in data]
            return []
        except (APIError, NodeUnavailableError):
            return []

    def transactions(self, address: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch transactions for an address (if endpoint available).

        Args:
            address: Wallet address to query.
            limit: Maximum transactions to return.

        Returns:
            List of transaction dicts.
        """
        try:
            data = self._get("/api/transactions", params={
                "address": address,
                "limit": limit,
            })
            if isinstance(data, list):
                return data
            return []
        except (APIError, NodeUnavailableError):
            return []

    # ── Context manager ───────────────────────────────────────────────────────

    def close(self):
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class AsyncClient:
    """
    Asynchronous RustChain client.

    Usage::

        >>> import asyncio
        >>> from rustchain import AsyncClient
        >>> async def main():
        ...     async with AsyncClient() as client:
        ...         health = await client.health()
        ...         print(health.version)
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        node_url: str = "https://50.28.86.131",
        timeout: float = 10.0,
        verify: bool = True,
    ):
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required. Install it with: pip install httpx")
        self.node_url = node_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.node_url,
                timeout=self.timeout,
                verify=verify,
                follow_redirects=True,
            )
        return self._client

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        client = await self._ensure_client()
        url = urljoin(self.node_url + "/", path.lstrip("/"))
        try:
            resp = await client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            try:
                body = e.response.json()
            except Exception:
                body = {}
            raise APIError(
                f"API error {e.response.status_code}: {e.response.text[:200]}",
                status_code=e.response.status_code,
                response=body,
            )
        except httpx.RequestError as e:
            raise NodeUnavailableError(f"Failed to connect to {url}: {e}")

    async def _get(self, path: str, params: Dict = None) -> Dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, json: Dict = None) -> Dict[str, Any]:
        return await self._request("POST", path, json=json)

    async def health(self) -> Health:
        data = await self._get("/health")
        return Health.from_dict(data)

    async def epoch(self) -> Epoch:
        data = await self._get("/epoch")
        return Epoch.from_dict(data)

    async def miners(self) -> List[Miner]:
        data = await self._get("/api/miners")
        if isinstance(data, list):
            return [Miner.from_dict(m) for m in data]
        return []

    async def miner(self, miner_id: str) -> Optional[Miner]:
        miners = await self.miners()
        for m in miners:
            if m.miner == miner_id:
                return m
        return None

    async def balance(self, wallet_id: str) -> Balance:
        if not wallet_id:
            raise ValidationError("wallet_id cannot be empty")
        data = await self._get("/wallet/balance", params={"miner_id": wallet_id})
        return Balance.from_dict(data)

    async def attestation_status(self, miner_id: str) -> Optional[AttestationStatus]:
        miner = await self.miner(miner_id)
        if miner is None:
            return None
        return AttestationStatus(
            miner_id=miner.miner,
            enrolled=True,
            last_attest=miner.last_attest,
            first_attest=miner.first_attest,
            antiquity_multiplier=miner.antiquity_multiplier,
            device_arch=miner.device_arch,
        )

    async def submit_attestation(self, miner_id: str, signature: str) -> Dict[str, Any]:
        return await self._post("/attest/submit", json={
            "miner_id": miner_id,
            "signature": signature,
        })

    async def transfer(
        self,
        from_wallet: str,
        to_wallet: str,
        amount: float,
        signature: str,
    ) -> TransferResult:
        if amount <= 0:
            raise ValidationError("Transfer amount must be positive")
        data = await self._post("/wallet/transfer/signed", json={
            "from": from_wallet,
            "to": to_wallet,
            "amount": amount,
            "signature": signature,
        })
        result = TransferResult.from_dict(data)
        if not result.success:
            raise TransferError(result.message)
        return result

    async def blocks(self, limit: int = 20) -> List[Block]:
        try:
            data = await self._get("/api/blocks", params={"limit": limit})
            if isinstance(data, list):
                return [Block.from_dict(b) for b in data]
            return []
        except (APIError, NodeUnavailableError):
            return []

    async def transactions(self, address: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            data = await self._get("/api/transactions", params={
                "address": address,
                "limit": limit,
            })
            if isinstance(data, list):
                return data
            return []
        except (APIError, NodeUnavailableError):
            return []

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
