import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.runtime import bug_feedback  # noqa: E402


class BugFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "profile" / "admin" / "bug_feedback.json"
        self.player = {"id": "alice", "nickname": "Alice"}
        self.admin = {"id": "bruce", "nickname": "Bruce", "is_admin": True}

    def tearDown(self):
        self.tmp.cleanup()

    def test_submit_feedback_writes_global_admin_file_shape(self):
        item = bug_feedback.submit_feedback(self.player, "提示按钮点了没有反应", path=self.path)

        self.assertTrue(self.path.exists())
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 2)
        self.assertEqual(data["items"][0]["id"], item["id"])
        self.assertEqual(data["items"][0]["player_id"], "alice")
        self.assertEqual(data["items"][0]["player_name"], "Alice")
        self.assertEqual(data["items"][0]["player_nickname"], "Alice")
        self.assertEqual(data["items"][0]["status"], "pending")
        self.assertFalse(data["items"][0]["fixed"])
        self.assertEqual(data["items"][0]["modification"], "")

    def test_admin_can_accept_reject_and_modify_feedback(self):
        first = bug_feedback.submit_feedback(self.player, "主界面音乐听不见", path=self.path)
        second = bug_feedback.submit_feedback(self.player, "建议调小按钮", path=self.path)

        accepted = bug_feedback.update_feedback_status(first["id"], "accepted", self.admin, path=self.path)
        modified = bug_feedback.update_feedback_status(second["id"], "modified", self.admin, "按钮需要只调设置页。", path=self.path)

        self.assertEqual(accepted["status_label"], "同意")
        self.assertEqual(accepted["admin_id"], "bruce")
        self.assertEqual(modified["status"], "modified")
        self.assertEqual(modified["modification"], "按钮需要只调设置页。")
        data = bug_feedback.load_feedback(self.path)
        self.assertEqual(len(data["items"]), 2)
        self.assertIn("modified", [entry["action"] for entry in modified["history"]])

    def test_legacy_feedback_player_nickname_becomes_player_name(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "items": [
                        {
                            "id": "legacy",
                            "player_id": "old",
                            "player_nickname": "Old Player",
                            "suggestion": "旧文件测试",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        data = bug_feedback.load_feedback(self.path)

        self.assertEqual(data["version"], 2)
        self.assertEqual(data["items"][0]["player_name"], "Old Player")
        self.assertEqual(data["items"][0]["player_nickname"], "Old Player")

    def test_mark_feedback_fixed_records_debug_note(self):
        item = bug_feedback.submit_feedback(self.player, "结算页链接打不开", path=self.path)

        fixed = bug_feedback.mark_feedback_fixed(item["id"], True, "已修复点击区域。", path=self.path)

        self.assertTrue(fixed["fixed"])
        self.assertEqual(fixed["fixed_note"], "已修复点击区域。")
        self.assertTrue(fixed["fixed_at"])

    def test_submit_term_delete_feedback_records_context_message(self):
        item = bug_feedback.submit_term_feedback(
            self.player,
            "delete",
            "数学模式 / 线索 / 入门",
            "高中数学",
            "空集",
            source_file="words/数学/入门模式：高中数学/high_school_sets_functions_terms.csv",
            record_path="record/2026-06/example.json",
            path=self.path,
        )

        self.assertEqual(item["feedback_type"], "term")
        self.assertEqual(item["term_action"], "delete")
        self.assertEqual(item["term_action_label"], "删除")
        self.assertEqual(item["source_label"], "高中数学")
        self.assertEqual(item["term_name"], "空集")
        self.assertEqual(
            item["suggestion"],
            "在进行数学模式 / 线索 / 入门时，高中数学词库里的空集词应该被删掉",
        )
        data = bug_feedback.load_feedback(self.path)
        self.assertEqual(data["items"][0]["record_path"], "record/2026-06/example.json")

    def test_submit_term_modify_feedback_requires_and_records_target(self):
        with self.assertRaises(ValueError):
            bug_feedback.submit_term_feedback(
                self.player,
                "modify",
                "物理模式 / 自由 / 简单",
                "高中力学",
                "速度",
                path=self.path,
            )

        item = bug_feedback.submit_term_feedback(
            self.player,
            "modify",
            "物理模式 / 自由 / 简单",
            "高中力学",
            "速度",
            proposed_change="速率",
            path=self.path,
        )

        self.assertEqual(item["term_action"], "modify")
        self.assertEqual(item["proposed_change"], "速率")
        self.assertEqual(item["suggestion"], "在进行物理模式 / 自由 / 简单时，高中力学词库里的速度词应该改为速率")


if __name__ == "__main__":
    unittest.main()
