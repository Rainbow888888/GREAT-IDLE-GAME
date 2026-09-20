import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace

from tools.sim.sim import (
    ConfigError,
    building_cost,
    building_rate,
    load_config,
    load_plan,
    milestone_multiplier,
    simulate,
    worker_cost,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
SMOKE_CONFIG = os.path.join(FIXTURES, "smoke-config.json")
SMOKE_PLAN = os.path.join(FIXTURES, "smoke-plan.json")
SIM_PY = os.path.join(os.path.dirname(__file__), "sim.py")


class TestBalanceFormulas(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(SMOKE_CONFIG)

    def test_worker_costs(self) -> None:
        worker = self.config.worker
        self.assertAlmostEqual(worker_cost(worker, 0), 10.0, places=9)
        self.assertAlmostEqual(worker_cost(worker, 1), 11.7, places=9)
        self.assertAlmostEqual(worker_cost(worker, 2), 13.689, places=9)

    def test_building_levels(self) -> None:
        rig = self.config.buildings["rig"]
        self.assertAlmostEqual(building_cost(rig, 1), 30.0, places=9)
        self.assertAlmostEqual(building_cost(rig, 2), 72.0, places=9)
        self.assertAlmostEqual(building_rate(rig, 1), 3.0, places=9)
        self.assertAlmostEqual(building_rate(rig, 2), 4.8, places=9)

    def test_milestones_are_total(self) -> None:
        worker = self.config.worker
        self.assertAlmostEqual(milestone_multiplier(worker, 4), 1.0, places=9)
        self.assertAlmostEqual(milestone_multiplier(worker, 5), 1.5, places=9)
        self.assertAlmostEqual(milestone_multiplier(worker, 10), 1.75, places=9)
        self.assertAlmostEqual(milestone_multiplier(worker, 20), 2.0, places=9)


class TestSmokeSimulation(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(SMOKE_CONFIG)
        self.plan = load_plan(SMOKE_PLAN)

    def test_smoke_timeline(self) -> None:
        result = simulate(self.config, self.plan)
        self.assertTrue(result.completed)

        times = {
            (e.kind, e.item_id, e.level, e.count): e.time_seconds
            for e in result.events
        }
        self.assertEqual(times[("worker", "worker", None, 1)], 10)
        self.assertEqual(times[("building", "rig", 1, None)], 25)
        self.assertEqual(times[("worker", "worker", None, 5)], 35)
        self.assertEqual(times[("fixed", "auto_delivery", None, None)], 40)
        self.assertEqual(times[("building", "rig", 2, None)], 46)
        self.assertEqual(times[("fixed", "emp", None, None)], 54)

    def test_deterministic(self) -> None:
        first = simulate(self.config, self.plan)
        second = simulate(self.config, self.plan)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_config_is_used(self) -> None:
        new_manual = replace(self.config.manual_action, yield_=2.0)
        new_config = replace(self.config, manual_action=new_manual)
        result = simulate(new_config, self.plan)
        first_worker = next(e for e in result.events if e.kind == "worker" and e.count == 1)
        self.assertEqual(first_worker.time_seconds, 5)


class TestValidationAndErrors(unittest.TestCase):
    def test_unknown_plan_id_rejected(self) -> None:
        config = load_config(SMOKE_CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            bad_plan = os.path.join(tmp, "bad-plan.json")
            with open(bad_plan, "w", encoding="utf-8") as f:
                f.write('{"steps": [{"kind": "building", "id": "unknown_rig", "targetLevel": 1, "category": "x"}]}')
            plan = load_plan(bad_plan)
            with self.assertRaises(ConfigError):
                simulate(config, plan)


class TestCli(unittest.TestCase):
    def _run_cli(self, config_path: str, plan_path: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, SIM_PY, "--config", config_path, "--plan", plan_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_timeout(self) -> None:
        config = load_config(SMOKE_CONFIG)
        fast_config = replace(config, max_seconds=20)
        result = simulate(fast_config, load_plan(SMOKE_PLAN))
        self.assertFalse(result.completed)
        self.assertEqual(result.elapsed_seconds, 20)

        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = os.path.join(tmp, "fast-config.json")
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write('{"schemaVersion": 1, "tickSeconds": 1, "maxSeconds": 20,')
                f.write(' "manualAction": {"yield": 1, "cooldownSeconds": 1, "stopsAfterPurchaseId": "auto_delivery"},')
                f.write(' "worker": {"id": "worker", "baseCost": 10, "costGrowth": 1.17, "baseRate": 1, "milestones": [{"count": 5, "totalMultiplier": 1.5}, {"count": 10, "totalMultiplier": 1.75}, {"count": 20, "totalMultiplier": 2.0}]},')
                f.write(' "buildings": [{"id": "rig", "baseCost": 30, "costGrowth": 2.4, "baseOutput": 3, "outputGrowth": 1.6, "maxLevel": 2}],')
                f.write(' "fixedPurchases": [{"id": "auto_delivery", "cost": 50, "category": "mechanical", "endsRun": false}, {"id": "emp", "cost": 100, "category": "mechanical", "endsRun": true}]}')
            proc = self._run_cli(cfg_path, SMOKE_PLAN)
            self.assertEqual(proc.returncode, 3)
            self.assertIn("completed=false", proc.stdout)


class TestCliRegressions(unittest.TestCase):
    def _run_cli(self, config_path: str, plan_path: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        return subprocess.run(
            [sys.executable, SIM_PY, "--config", config_path, "--plan", plan_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

    def test_unknown_plan_id_cli_returns_error_code_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_plan = os.path.join(tmp, "bad-plan.json")
            with open(bad_plan, "w", encoding="utf-8") as f:
                f.write('{"steps": [{"kind": "building", "id": "unknown_rig", "targetLevel": 1, "category": "x"}]}')
            proc = self._run_cli(SMOKE_CONFIG, bad_plan)
            self.assertEqual(proc.returncode, 2)
            self.assertTrue(proc.stdout.startswith("ERROR |"))
            self.assertEqual(proc.stderr, "")
            self.assertNotIn("Traceback", proc.stdout)

    def test_plan_without_ends_run_is_not_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            no_end_plan = os.path.join(tmp, "no-end-plan.json")
            with open(no_end_plan, "w", encoding="utf-8") as f:
                f.write('{"steps": [{"kind": "worker", "targetCount": 1, "category": "routine"}]}')

            result = simulate(load_config(SMOKE_CONFIG), load_plan(no_end_plan))
            self.assertFalse(result.completed)
            self.assertEqual(result.elapsed_seconds, 10)

            proc = self._run_cli(SMOKE_CONFIG, no_end_plan)
            self.assertEqual(proc.returncode, 3)
            self.assertIn("completed=false", proc.stdout)
            self.assertIn("00:10 | purchase | worker | count=1", proc.stdout)


if __name__ == "__main__":
    unittest.main()
