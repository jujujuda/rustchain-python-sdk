"""Data models for RustChain API responses."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Health:
    """Node health status."""
    ok: bool
    version: str
    uptime_s: float
    db_rw: bool
    tip_age_slots: int
    backup_age_hours: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Health":
        return cls(
            ok=data.get("ok", False),
            version=data.get("version", "unknown"),
            uptime_s=float(data.get("uptime_s", 0)),
            db_rw=data.get("db_rw", False),
            tip_age_slots=int(data.get("tip_age_slots", 0)),
            backup_age_hours=float(data.get("backup_age_hours", 0)),
        )

    def is_healthy(self) -> bool:
        return self.ok and self.db_rw


@dataclass
class Epoch:
    """Current epoch information."""
    epoch: int
    slot: int
    blocks_per_epoch: int
    enrolled_miners: int
    total_supply_rtc: float
    epoch_pot: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Epoch":
        return cls(
            epoch=int(data.get("epoch", 0)),
            slot=int(data.get("slot", 0)),
            blocks_per_epoch=int(data.get("blocks_per_epoch", 0)),
            enrolled_miners=int(data.get("enrolled_miners", 0)),
            total_supply_rtc=float(data.get("total_supply_rtc", 0)),
            epoch_pot=float(data.get("epoch_pot", 0)),
        )


@dataclass
class Miner:
    """A RustChain miner."""
    miner: str
    device_arch: str
    device_family: str
    hardware_type: str
    antiquity_multiplier: float
    entropy_score: float
    first_attest: Optional[int]
    last_attest: Optional[int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Miner":
        return cls(
            miner=data.get("miner", ""),
            device_arch=data.get("device_arch", ""),
            device_family=data.get("device_family", ""),
            hardware_type=data.get("hardware_type", ""),
            antiquity_multiplier=float(data.get("antiquity_multiplier", 0)),
            entropy_score=float(data.get("entropy_score", 0)),
            first_attest=data.get("first_attest"),
            last_attest=data.get("last_attest"),
        )

    def is_active(self) -> bool:
        return self.last_attest is not None


@dataclass
class Balance:
    """Wallet balance."""
    miner_id: str
    amount_rtc: float
    amount_i64: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Balance":
        return cls(
            miner_id=data.get("miner_id", ""),
            amount_rtc=float(data.get("amount_rtc", 0)),
            amount_i64=int(data.get("amount_i64", 0)),
        )

    def __repr__(self) -> str:
        return f"Balance({self.miner_id}: {self.amount_rtc} RTC)"


@dataclass
class Block:
    """A RustChain block."""
    hash: str
    slot: int
    epoch: int
    miner: str
    transactions: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        return cls(
            hash=data.get("hash", ""),
            slot=int(data.get("slot", 0)),
            epoch=int(data.get("epoch", 0)),
            miner=data.get("miner", ""),
            transactions=data.get("transactions", []),
        )


@dataclass
class AttestationStatus:
    """Attestation status for a miner."""
    miner_id: str
    enrolled: bool
    last_attest: Optional[int]
    first_attest: Optional[int]
    antiquity_multiplier: float
    device_arch: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttestationStatus":
        return cls(
            miner_id=data.get("miner_id", ""),
            enrolled=data.get("enrolled", False),
            last_attest=data.get("last_attest"),
            first_attest=data.get("first_attest"),
            antiquity_multiplier=float(data.get("antiquity_multiplier", 0)),
            device_arch=data.get("device_arch", ""),
        )


@dataclass
class TransferResult:
    """Result of a signed transfer."""
    success: bool
    tx_hash: Optional[str]
    message: str
    amount: float
    from_wallet: str
    to_wallet: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransferResult":
        return cls(
            success=data.get("success", False),
            tx_hash=data.get("tx_hash"),
            message=data.get("message", ""),
            amount=float(data.get("amount", 0)),
            from_wallet=data.get("from", ""),
            to_wallet=data.get("to", ""),
        )
