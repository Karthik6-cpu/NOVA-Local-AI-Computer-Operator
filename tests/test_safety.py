import unittest
from nova.safety import validate_action, validate_url
from nova.voice import decision_from_text
from nova.planner import validate_plan

class SafetyTests(unittest.TestCase):
    def test_http_url_allowed(self):
        self.assertEqual(validate_url("https://example.com"), "https://example.com")
    def test_file_url_blocked(self):
        with self.assertRaises(ValueError):
            validate_url("file:///C:/Windows/win.ini")
    def test_embedded_credentials_blocked(self):
        with self.assertRaises(ValueError):
            validate_url("https://user:pass@example.com")
    def test_unknown_tool_blocked(self):
        with self.assertRaises(ValueError):
            validate_action({"tool":"run_shell","args":{"command":"whoami"}})
    def test_extra_args_blocked(self):
        with self.assertRaises(ValueError):
            validate_action({"tool":"open_notepad","args":{"command":"calc"}})
    def test_invalid_filename_blocked(self):
        with self.assertRaises(ValueError):
            validate_action({"tool":"create_note","args":{"title":"../bad","content":"x"}})
    def test_empty_search_blocked(self):
        with self.assertRaises(ValueError):
            validate_action({"tool":"search_files","args":{"query":""}})
    def test_plan_rejects_unknown_tool(self):
        with self.assertRaises(Exception):
            validate_plan({"summary":"test","actions":[{"tool":"run_shell","args":{}}]})
    def test_plan_rejects_too_many_actions(self):
        with self.assertRaises(Exception):
            validate_plan({"summary":"test","actions":[{"tool":"open_notepad","args":{}}]*6})


    def test_new_windows_app_tool_allowed(self):
        self.assertEqual(validate_action({"tool":"open_file_explorer","args":{}})[0], "open_file_explorer")

    def test_application_name_must_be_plain_name(self):
        with self.assertRaises(ValueError):
            validate_action({"tool":"open_application","args":{"name":"C:\\Windows\\System32"}})

    def test_approval_phrase_recognized(self):
        self.assertEqual(decision_from_text("approve"), "approve")
        self.assertEqual(decision_from_text("please approve the plan"), "approve")
        self.assertEqual(decision_from_text("open notepad and approve"), None)
        self.assertEqual(decision_from_text("reject"), "reject")
        self.assertEqual(decision_from_text("open notepad and approve"), None)

if __name__ == "__main__":
    unittest.main()
