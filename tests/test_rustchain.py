"""Unit tests for RustChain Python SDK."""

import unittest
from unittest.mock import patch, MagicMock

import rustchain
from rustchain import Client, AsyncClient
from rustchain.models import (
    Health, Epoch, Miner, Balance, Block,
    AttestationStatus, TransferResult,
)
from rustchain.exceptions import (
    RustChainError, APIError, NodeUnavailableError,
    ValidationError, TransferError,
)


# ── Test fixtures ──────────────────────────────────────────────────────────────

SAMPLE_HEALTH = {
    "ok": True,
    "version": "2.2.1-rip200",
    "uptime_s": 149888.0,
    "db_rw": True,
    "tip_age_slots": 0,
    "backup_age_hours": 6.27,
}

SAMPLE_EPOCH = {
    "epoch": 110,
    "slot": 15919,
    "blocks_per_epoch": 144,
    "enrolled_miners": 22,
    "total_supply_rtc": 8388608.0,
    "epoch_pot": 1.5,
}

SAMPLE_MINERS = [
    {
        "miner": "RTC14f06ee294f327f5685d3de5e1ed501cffab33e7",
        "device_arch": "aarch64",
        "device_family": "ARM",
        "hardware_type": "Unknown/Other",
        "antiquity_multiplier": 0.001,
        "entropy_score": 0.0,
        "first_attest": None,
        "last_attest": 1774258630,
    },
    {
        "miner": "m2-mac-mini-sophia",
        "device_arch": "apple_silicon",
        "device_family": "arm",
        "hardware_type": "Apple Silicon (Modern)",
        "antiquity_multiplier": 1.0,
        "entropy_score": 0.0,
        "first_attest": None,
        "last_attest": 1774258617,
    },
]

SAMPLE_BALANCE = {
    "miner_id": "my-wallet",
    "amount_rtc": 42.5,
    "amount_i64": 42500000,
}


# ── Model Tests ────────────────────────────────────────────────────────────────

class TestHealth(unittest.TestCase):
    def test_from_dict(self):
        h = Health.from_dict(SAMPLE_HEALTH)
        self.assertTrue(h.ok)
        self.assertEqual(h.version, "2.2.1-rip200")
        self.assertEqual(h.uptime_s, 149888.0)
        self.assertTrue(h.db_rw)
        self.assertEqual(h.tip_age_slots, 0)
        self.assertEqual(h.backup_age_hours, 6.27)

    def test_is_healthy(self):
        h = Health.from_dict(SAMPLE_HEALTH)
        self.assertTrue(h.is_healthy())

    def test_is_unhealthy(self):
        bad = dict(SAMPLE_HEALTH, ok=False)
        h = Health.from_dict(bad)
        self.assertFalse(h.is_healthy())


class TestEpoch(unittest.TestCase):
    def test_from_dict(self):
        ep = Epoch.from_dict(SAMPLE_EPOCH)
        self.assertEqual(ep.epoch, 110)
        self.assertEqual(ep.slot, 15919)
        self.assertEqual(ep.blocks_per_epoch, 144)
        self.assertEqual(ep.enrolled_miners, 22)
        self.assertEqual(ep.total_supply_rtc, 8388608.0)
        self.assertEqual(ep.epoch_pot, 1.5)

    def test_epoch_defaults(self):
        ep = Epoch.from_dict({})
        self.assertEqual(ep.epoch, 0)
        self.assertEqual(ep.slot, 0)


class TestMiner(unittest.TestCase):
    def test_from_dict(self):
        m = Miner.from_dict(SAMPLE_MINERS[0])
        self.assertEqual(m.miner, "RTC14f06ee294f327f5685d3de5e1ed501cffab33e7")
        self.assertEqual(m.device_arch, "aarch64")
        self.assertEqual(m.antiquity_multiplier, 0.001)
        self.assertIsNone(m.first_attest)
        self.assertIsNotNone(m.last_attest)

    def test_is_active(self):
        m = Miner.from_dict(SAMPLE_MINERS[0])
        self.assertTrue(m.is_active())

    def test_not_active(self):
        inactive = dict(SAMPLE_MINERS[0], last_attest=None)
        m = Miner.from_dict(inactive)
        self.assertFalse(m.is_active())


class TestBalance(unittest.TestCase):
    def test_from_dict(self):
        b = Balance.from_dict(SAMPLE_BALANCE)
        self.assertEqual(b.miner_id, "my-wallet")
        self.assertEqual(b.amount_rtc, 42.5)
        self.assertEqual(b.amount_i64, 42500000)

    def test_repr(self):
        b = Balance.from_dict(SAMPLE_BALANCE)
        self.assertIn("my-wallet", repr(b))
        self.assertIn("42.5", repr(b))


class TestTransferResult(unittest.TestCase):
    def test_success(self):
        data = {
            "success": True,
            "tx_hash": "abc123",
            "message": "Transfer successful",
            "amount": 10.0,
            "from": "alice",
            "to": "bob",
        }
        r = TransferResult.from_dict(data)
        self.assertTrue(r.success)
        self.assertEqual(r.tx_hash, "abc123")
        self.assertEqual(r.amount, 10.0)

    def test_failure(self):
        data = {"success": False, "message": "Insufficient funds", "amount": 0, "from": "", "to": ""}
        r = TransferResult.from_dict(data)
        self.assertFalse(r.success)


# ── Client Tests ───────────────────────────────────────────────────────────────

class TestClientHealth(unittest.TestCase):
    @patch("rustchain.client.httpx.Client")
    def test_health_returns_health_object(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = SAMPLE_HEALTH
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        h = client.health()

        self.assertIsInstance(h, Health)
        self.assertEqual(h.version, "2.2.1-rip200")
        self.assertTrue(h.is_healthy())


class TestClientEpoch(unittest.TestCase):
    @patch("rustchain.client.httpx.Client")
    def test_epoch_returns_epoch_object(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = SAMPLE_EPOCH
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        ep = client.epoch()

        self.assertIsInstance(ep, Epoch)
        self.assertEqual(ep.epoch, 110)
        self.assertEqual(ep.slot, 15919)


class TestClientMiners(unittest.TestCase):
    @patch("rustchain.client.httpx.Client")
    def test_miners_returns_list_of_miners(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = SAMPLE_MINERS
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        miners = client.miners()

        self.assertIsInstance(miners, list)
        self.assertEqual(len(miners), 2)
        self.assertIsInstance(miners[0], Miner)

    @patch("rustchain.client.httpx.Client")
    def test_miner_returns_specific_miner(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = SAMPLE_MINERS
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        m = client.miner("m2-mac-mini-sophia")

        self.assertIsInstance(m, Miner)
        self.assertEqual(m.hardware_type, "Apple Silicon (Modern)")

    @patch("rustchain.client.httpx.Client")
    def test_miner_returns_none_when_not_found(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = SAMPLE_MINERS
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        m = client.miner("nonexistent")
        self.assertIsNone(m)


class TestClientBalance(unittest.TestCase):
    @patch("rustchain.client.httpx.Client")
    def test_balance_returns_balance_object(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = SAMPLE_BALANCE
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        b = client.balance("my-wallet")

        self.assertIsInstance(b, Balance)
        self.assertEqual(b.amount_rtc, 42.5)

    @patch("rustchain.client.httpx.Client")
    def test_balance_empty_wallet_id_raises(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        client = Client(node_url="https://test.example.com")

        with self.assertRaises(ValidationError):
            client.balance("")


class TestClientAttestation(unittest.TestCase):
    @patch("rustchain.client.httpx.Client")
    def test_attestation_status_returns_status(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = SAMPLE_MINERS
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        s = client.attestation_status("m2-mac-mini-sophia")

        self.assertIsInstance(s, AttestationStatus)
        self.assertEqual(s.miner_id, "m2-mac-mini-sophia")
        self.assertEqual(s.antiquity_multiplier, 1.0)

    @patch("rustchain.client.httpx.Client")
    def test_attestation_status_none_for_unknown_miner(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = SAMPLE_MINERS
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        s = client.attestation_status("unknown-miner")
        self.assertIsNone(s)


class TestClientTransfer(unittest.TestCase):
    @patch("rustchain.client.httpx.Client")
    def test_transfer_positive_amount(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = {
            "success": True,
            "tx_hash": "tx123",
            "message": "OK",
            "amount": 5.0,
            "from": "alice",
            "to": "bob",
        }
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        result = client.transfer("alice", "bob", 5.0, "sig123")

        self.assertIsInstance(result, TransferResult)
        self.assertTrue(result.success)
        self.assertEqual(result.tx_hash, "tx123")

    @patch("rustchain.client.httpx.Client")
    def test_transfer_zero_amount_raises(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        client = Client(node_url="https://test.example.com")

        with self.assertRaises(ValidationError):
            client.transfer("alice", "bob", 0, "sig")

    @patch("rustchain.client.httpx.Client")
    def test_transfer_negative_amount_raises(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        client = Client(node_url="https://test.example.com")

        with self.assertRaises(ValidationError):
            client.transfer("alice", "bob", -5, "sig")


class TestClientContextManager(unittest.TestCase):
    @patch("rustchain.client.httpx.Client")
    def test_context_manager(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        with Client(node_url="https://test.example.com") as client:
            self.assertIsNotNone(client)
        mock_instance.close.assert_called_once()


class TestClientBlocks(unittest.TestCase):
    @patch("rustchain.client.httpx.Client")
    def test_blocks_returns_list(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = [
            {"hash": "abc", "slot": 1, "epoch": 1, "miner": "test"}
        ]
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        blocks = client.blocks(limit=10)

        self.assertIsInstance(blocks, list)
        self.assertEqual(len(blocks), 1)
        self.assertIsInstance(blocks[0], Block)


class TestClientTransactions(unittest.TestCase):
    @patch("rustchain.client.httpx.Client")
    def test_transactions_returns_list(self, mock_client_cls):
        mock_instance = MagicMock()
        mock_instance.request.return_value.json.return_value = [
            {"tx_hash": "abc", "amount": 10}
        ]
        mock_client_cls.return_value = mock_instance

        client = Client(node_url="https://test.example.com")
        txs = client.transactions("alice", limit=10)

        self.assertIsInstance(txs, list)
        self.assertEqual(txs[0]["tx_hash"], "abc")


# ── Exception Tests ───────────────────────────────────────────────────────────

class TestExceptions(unittest.TestCase):
    def test_api_error(self):
        err = APIError("Not found", status_code=404, response={"error": "missing"})
        self.assertEqual(err.status_code, 404)
        self.assertEqual(err.response["error"], "missing")
        self.assertIn("404", repr(err))

    def test_node_unavailable(self):
        err = NodeUnavailableError("Connection refused")
        self.assertIn("Connection refused", str(err))

    def test_validation_error(self):
        err = ValidationError("wallet_id is required")
        self.assertIn("required", str(err))

    def test_transfer_error(self):
        err = TransferError("Insufficient balance", balance=0.0)
        self.assertEqual(err.balance, 0.0)


# ── Import Tests ───────────────────────────────────────────────────────────────

class TestImport(unittest.TestCase):
    def test_version(self):
        self.assertEqual(rustchain.__version__, "0.1.0")

    def test_public_api(self):
        from rustchain import (
            Client, AsyncClient,
            RustChainError, APIError,
            NodeUnavailableError, ValidationError,
        )
        self.assertTrue(issubclass(RustChainError, Exception))


if __name__ == "__main__":
    unittest.main()
