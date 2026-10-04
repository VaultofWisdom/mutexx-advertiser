"""
Tests for the Mutexx account sync.

The server is replaced by a small in-memory stand-in that behaves like the real
table: every write gets the next revision, deletes are tombstones, and a pull returns
everything above a revision. Against it, two "devices" - two data folders - sync the
way two computers would.

The cases that matter are the ones that lose data when they go wrong: a change on
both sides, a deletion that comes back, and the history, which the safety catch
counts against.

Run:  python -m unittest discover -s tests
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advertiser import account, core  # noqa: E402

USER = "user-1"


class FakeServer:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict] = {}
        self.rev = 0

    def pull(self, _config, collection, since):
        return [dict(row) for (col, _key), row in sorted(self.rows.items(), key=lambda x: x[1]["rev"])
                if col == collection and row["rev"] > since]

    def push(self, _config, _session, records):
        written = []
        for record in records:
            self.rev += 1
            row = {"collection": record["collection"], "key": record["key"],
                   "hash": record.get("hash"), "rev": self.rev,
                   "payload": None if record.get("deleted") else record.get("payload"),
                   "deleted_at": "2026-10-04T00:00:00Z" if record.get("deleted") else None}
            self.rows[(record["collection"], record["key"])] = row
            written.append(dict(row))
        return written


class Device:
    """One computer: its own data folder, the shared server."""

    def __init__(self, server: FakeServer) -> None:
        self.home = tempfile.mkdtemp(prefix="advertiser-device-")
        self.server = server

    def __enter__(self):
        self._saved = {name: getattr(core, name)
                       for name in ("HOME_DIR", "DATA_DIR", "PRODUCTS_DIR", "CONFIG_PATH")}
        core.HOME_DIR = self.home
        core.DATA_DIR = os.path.join(self.home, "data")
        core.PRODUCTS_DIR = os.path.join(core.DATA_DIR, "products")
        core.CONFIG_PATH = os.path.join(self.home, "config.json")
        os.makedirs(core.DATA_DIR, exist_ok=True)
        self._fns = (account._pull, account._push, account._token, account._register_device)
        account._pull = self.server.pull
        account._push = self.server.push
        account._token = lambda config: ("token", {"user": {"id": USER}, "device_id": "d"})
        account._register_device = lambda config, session: None
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(core, name, value)
        account._pull, account._push, account._token, account._register_device = self._fns

    def cleanup(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    # -- helpers --
    def add_product(self, slug: str, name: str) -> None:
        config = core.load_config()
        config["products"] = [p for p in config.get("products", []) if p["slug"] != slug] + [
            {"slug": slug, "name": name}]
        config["active_product"] = slug
        core.save_config(config)

    def sync(self) -> dict:
        return account.sync()


class SyncBetweenTwoDevices(unittest.TestCase):

    def setUp(self) -> None:
        self.server = FakeServer()
        self.a = Device(self.server)
        self.b = Device(self.server)

    def tearDown(self) -> None:
        self.a.cleanup()
        self.b.cleanup()

    def test_a_product_travels_with_its_data(self) -> None:
        with self.a:
            self.a.add_product("notes", "Notes")
            core.save_product("notes", "seeds", {"subreddits": ["x"]})
            result = self.a.sync()
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["pushed"], 2)
        with self.b:
            result = self.b.sync()
            self.assertEqual(result["pulled"], 2)
            config = core.load_config()
            self.assertEqual([p["slug"] for p in config["products"]], ["notes"])
            self.assertEqual(config["active_product"], "notes")
            self.assertEqual(core.load_product("notes", "seeds", None), {"subreddits": ["x"]})

    def test_nothing_secret_is_sent(self) -> None:
        with self.a:
            config = core.load_config()
            config["anthropic"]["api_key"] = "sk-ant-SECRET"
            core.save_config(config)
            self.a.add_product("p", "P")
            self.a.sync()
        self.assertNotIn("sk-ant-SECRET", json.dumps(list(self.server.rows.values())))

    def test_a_second_pass_without_changes_sends_nothing(self) -> None:
        with self.a:
            self.a.add_product("p", "P")
            self.a.sync()
            self.assertEqual(self.a.sync()["pushed"], 0)

    def test_an_edit_on_one_side_arrives_on_the_other(self) -> None:
        with self.a:
            self.a.add_product("p", "P")
            core.save_product("p", "queue", [1])
            self.a.sync()
        with self.b:
            self.b.sync()
            core.save_product("p", "queue", [1, 2])
            self.b.sync()
        with self.a:
            self.a.sync()
            self.assertEqual(core.load_product("p", "queue", None), [1, 2])

    def test_a_deletion_does_not_come_back(self) -> None:
        with self.a:
            self.a.add_product("p", "P")
            core.save_product("p", "queue", [1])
            self.a.sync()
        with self.b:
            self.b.sync()
            os.remove(core.product_store_path("p", "queue"))
            self.b.sync()
            self.b.sync()
            self.assertFalse(os.path.exists(core.product_store_path("p", "queue")))
        with self.a:
            self.a.sync()
            self.assertFalse(os.path.exists(core.product_store_path("p", "queue")))

    def test_a_conflict_keeps_both_versions(self) -> None:
        with self.a:
            self.a.add_product("p", "P")
            core.save_product("p", "queue", ["start"])
            self.a.sync()
        with self.b:
            self.b.sync()
            core.save_product("p", "queue", ["from b"])
            self.b.sync()
        with self.a:
            core.save_product("p", "queue", ["from a"])
            result = self.a.sync()
            self.assertEqual(result["conflicts"], 1)
            self.assertEqual(core.load_product("p", "queue", None), ["from b"])
            folder = os.path.join(core.DATA_DIR, "account", "conflicts")
            kept = []
            for name in os.listdir(folder):
                with open(os.path.join(folder, name), encoding="utf-8") as handle:
                    kept.append(json.load(handle))
            self.assertIn(["from a"], kept)

    def test_the_history_is_merged_not_overwritten(self) -> None:
        """Losing a history entry would let the safety catch propose a community
        that was posted to yesterday on the other machine."""
        post_a = {"ts": 1, "community_id": "reddit:a", "channel": "r/a"}
        post_b = {"ts": 2, "community_id": "reddit:b", "channel": "r/b"}
        with self.a:
            self.a.add_product("p", "P")
            core.save_product("p", "history", [])
            self.a.sync()
        with self.b:
            self.b.sync()
            core.save_product("p", "history", [post_b])
            self.b.sync()
        with self.a:
            core.save_product("p", "history", [post_a])
            self.a.sync()
            self.assertEqual(core.load_product("p", "history", None), [post_a, post_b])
        with self.b:
            self.b.sync()
            self.assertEqual(core.load_product("p", "history", None), [post_a, post_b])


class TheSessionIsProtected(unittest.TestCase):

    def setUp(self) -> None:
        self.home = tempfile.mkdtemp()
        self._saved = core.DATA_DIR
        core.DATA_DIR = self.home

    def tearDown(self) -> None:
        core.DATA_DIR = self._saved
        shutil.rmtree(self.home, ignore_errors=True)

    def test_round_trip(self) -> None:
        session = {"access_token": "a", "refresh_token": "r", "expires_at": 1,
                   "user": {"id": "u", "email": "x@example.com"}}
        account._save_session(session)
        self.assertEqual(account.load_session(), session)
        with open(os.path.join(self.home, "account", "session.json"), encoding="utf-8") as handle:
            raw = handle.read()
        if os.name == "nt":
            self.assertNotIn("refresh_token", raw)

    def test_the_interface_sees_no_token(self) -> None:
        account._save_session({"access_token": "SECRET-A", "refresh_token": "SECRET-R",
                               "expires_at": 1, "user": {"id": "u", "email": "x@example.com"}})
        summary = json.dumps(account.summary())
        self.assertIn("x@example.com", summary)
        self.assertNotIn("SECRET", summary)

    def test_without_a_session_there_is_no_sync(self) -> None:
        result = account.sync(lambda: {"user_agent": "t"})
        self.assertEqual(result["status"], "unauthorized")


if __name__ == "__main__":
    unittest.main()
