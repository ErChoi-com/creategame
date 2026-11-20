"""mcp_server.py / _session_bridge.py — the MCP seam over Session (callback/engine/README.md's
player-facing boundary). Drives the real stdio process with raw JSON-RPC, the way an MCP client does."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from callback.engine.simulation._session_bridge import GameError, GameRegistry, to_plain

REPO_ROOT = Path(__file__).resolve().parents[3]


class McpProcess:
    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "callback.engine.simulation.mcp_server"], cwd=REPO_ROOT,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
        self._id = 0

    def request(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}) + "\n")
        self.proc.stdin.flush()
        reply = json.loads(self.proc.stdout.readline())
        assert reply["id"] == self._id
        return reply

    def notify(self, method: str) -> None:
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.proc.stdin.flush()

    def tool(self, name: str, **arguments) -> tuple[object, bool]:
        result = self.request("tools/call", {"name": name, "arguments": arguments})["result"]
        text = result["content"][0]["text"]
        try:
            return json.loads(text), result["isError"]
        except json.JSONDecodeError:
            return text, result["isError"]

    def close(self) -> None:
        self.proc.stdin.close()
        self.proc.wait(timeout=10)


class TestMcpServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mcp = McpProcess()
        init = cls.mcp.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                              "clientInfo": {"name": "test", "version": "0"}})
        cls.init = init["result"]
        cls.mcp.notify("notifications/initialized")

    @classmethod
    def tearDownClass(cls):
        cls.mcp.close()

    def test_handshake_and_tool_list(self):
        self.assertEqual(self.init["protocolVersion"], "2025-06-18")
        self.assertIn("tools", self.init["capabilities"])
        names = {t["name"] for t in self.mcp.request("tools/list")["result"]["tools"]}
        self.assertTrue({"new_game", "call_session", "auto_play", "run_archetype"} <= names)

    def test_play_one_acting_year_by_hand(self):
        game, err = self.mcp.tool("new_game", background="conservatory", ambition="work", seed=11)
        self.assertFalse(err)
        gid = game["game_id"]
        self.assertEqual(game["status"]["age"], 22)

        board, _ = self.mcp.tool("call_session", game_id=gid, method="offer_board")
        for _ in range(10):
            if any(o["available"] for o in board):
                break
            more, _ = self.mcp.tool("call_session", game_id=gid, method="generate_more_listings")
            board += more
        open_roles = [o for o in board if o["available"]]
        if open_roles:
            self.mcp.tool("call_session", game_id=gid, method="accept", args={"index": open_roles[0]["index"]})
            self.mcp.tool("call_session", game_id=gid, method="choose_deal", args={"want_approvals": False})
            prep, _ = self.mcp.tool("call_session", game_id=gid, method="prep_options")
            self.mcp.tool("call_session", game_id=gid, method="choose_prep", args={"key": prep[0][0]})
            dials, _ = self.mcp.tool("call_session", game_id=gid, method="dial_options")
            positions, _ = self.mcp.tool("call_session", game_id=gid, method="position_options")
            scenes, _ = self.mcp.tool("call_session", game_id=gid, method="scene_names")
            episodes, _ = self.mcp.tool("call_session", game_id=gid, method="episode_labels")
            for _ in episodes:
                for _ in scenes:
                    _, err = self.mcp.tool("call_session", game_id=gid, method="play_scene",
                                           args={"choices": {d: positions[0][0] for d, _ in dials}})
                    self.assertFalse(err)
            summary, err = self.mcp.tool("call_session", game_id=gid, method="choose_release",
                                         args={"strategy": "wide", "bid_policy": "self"})
            self.assertFalse(err, summary)
            self.assertIsInstance(summary, dict)
        else:
            self.mcp.tool("call_session", game_id=gid, method="decline_board")
        self.mcp.tool("call_session", game_id=gid, method="end_year")
        status, _ = self.mcp.tool("game_status", game_id=gid)
        self.assertEqual(status["age"], 23)

    def test_auto_play_advances_years(self):
        game, _ = self.mcp.tool("new_game", background="conservatory", ambition="fortune", seed=3)
        result, err = self.mcp.tool("auto_play", game_id=game["game_id"], years=3)
        self.assertFalse(err)
        self.assertEqual(result["years_played"], 3)
        self.assertEqual(result["status"]["age"], 25)
        self.assertIn("RECKONING", result["transcript"])

    def test_bad_input_is_a_tool_error_not_a_crash(self):
        _, err = self.mcp.tool("call_session", game_id="nope", method="age")
        self.assertTrue(err)
        game, _ = self.mcp.tool("new_game", background="conservatory", ambition="work", seed=1)
        msg, err = self.mcp.tool("call_session", game_id=game["game_id"], method="_private")
        self.assertTrue(err)
        msg, err = self.mcp.tool("call_session", game_id=game["game_id"], method="accept", args={"nope": 1})
        self.assertTrue(err)
        self.assertIn("bad arguments", msg)
        self.assertIn("error", self.mcp.request("does/not/exist"))

    def test_run_archetype(self):
        result, err = self.mcp.tool("run_archetype", archetype="gambler", seed=2, years=20)
        self.assertFalse(err)
        self.assertEqual(result["archetype"], "gambler")


class TestBridge(unittest.TestCase):
    def test_unknown_background_rejected(self):
        with self.assertRaises(GameError):
            GameRegistry().new_game("astronaut", "work")

    def test_to_plain_never_leaks_objects(self):
        class Engine:  # stands in for an engine dataclass
            pass
        out = to_plain({"a": (1, 2), "b": frozenset({"x"}), "c": Engine()})
        self.assertEqual(out["a"], [1, 2])
        self.assertEqual(out["b"], ["x"])
        self.assertIsInstance(out["c"], str)


if __name__ == "__main__":
    unittest.main()
