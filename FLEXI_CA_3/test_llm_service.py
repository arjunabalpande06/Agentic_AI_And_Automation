import os
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import services
try:
    from llm_service import parse_task_with_llm, get_groq_api_key
    from app import create_ai_reminder, view_assignments
    from database import load_deadlines
except ImportError:
    from FLEXI_CA_3.llm_service import parse_task_with_llm, get_groq_api_key
    from FLEXI_CA_3.app import create_ai_reminder, view_assignments
    from FLEXI_CA_3.database import load_deadlines


class TestLLMService(unittest.TestCase):

    def setUp(self):
        from database import load_deadlines
        self.original_deadlines = load_deadlines()

    def tearDown(self):
        from database import save_deadlines
        save_deadlines(self.original_deadlines)

    def test_empty_input(self):
        """Test that empty or whitespace-only input returns a clean validation error."""
        result = parse_task_with_llm("")
        self.assertFalse(result["success"])
        self.assertIn("enter a task", result["error"].lower())

        result_spaces = parse_task_with_llm("   \n\t  ")
        self.assertFalse(result_spaces["success"])
        self.assertIn("enter a task", result_spaces["error"].lower())

    def test_missing_api_key(self):
        """Test that missing GROQ_API_KEY returns a clear error without crashing."""
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
            with patch("llm_service.get_groq_api_key", return_value=None):
                result = parse_task_with_llm("Submit assignment tomorrow at 5 PM")
                self.assertFalse(result["success"])
                self.assertIn("Groq API key is not configured", result["error"])

    def test_clarification_when_date_missing_mock(self):
        """Test that if the model flags missing date/time, needs_clarification is True."""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"task": "Submit assignment", "date": "", "time": "", "category": "Assignment", "description": "", "needs_clarification": true, "clarification_message": "Please specify the deadline date and time for this assignment."}'
        mock_response.choices = [mock_choice]

        with patch("groq.Groq") as mock_groq:
            instance = mock_groq.return_value
            instance.chat.completions.create.return_value = mock_response

            with patch("llm_service.get_groq_api_key", return_value="gsk_mock_test_key"):
                result = parse_task_with_llm("Remind me to submit my assignment")
                self.assertFalse(result["success"])
                self.assertTrue(result["needs_clarification"])
                self.assertIn("Please specify the deadline date", result["clarification_message"])

    def test_successful_parsing_mock(self):
        """Test structured output extraction when model returns valid assignment JSON."""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"task": "Submit Python assignment", "date": "2026-09-25", "time": "18:00", "category": "Assignment", "description": "", "needs_clarification": false, "clarification_message": ""}'
        mock_response.choices = [mock_choice]

        with patch("groq.Groq") as mock_groq:
            instance = mock_groq.return_value
            instance.chat.completions.create.return_value = mock_response

            with patch("llm_service.get_groq_api_key", return_value="gsk_mock_test_key"):
                result = parse_task_with_llm("Remind me to submit my Python assignment on September 25 at 6 PM.")
                self.assertTrue(result["success"])
                self.assertEqual(result["data"]["task"], "Submit Python assignment")
                self.assertEqual(result["data"]["date"], "2026-09-25")
                self.assertEqual(result["data"]["time"], "18:00")
                self.assertEqual(result["data"]["category"], "Assignment")

    def test_app_create_ai_reminder_flow(self):
        """Test the end-to-end Gradio helper create_ai_reminder using a mock."""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"task": "Project presentation", "date": "2026-09-28", "time": "10:00", "category": "Presentation", "description": "", "needs_clarification": false, "clarification_message": ""}'
        mock_response.choices = [mock_choice]

        with patch("groq.Groq") as mock_groq:
            instance = mock_groq.return_value
            instance.chat.completions.create.return_value = mock_response

            with patch("llm_service.get_groq_api_key", return_value="gsk_mock_test_key"):
                ui_output = create_ai_reminder(
                    "I have a project presentation on September 28 at 10 AM.",
                    student_name="Test Student",
                    reminder_days=2
                )
                self.assertIn("Project presentation", ui_output)
                self.assertIn("28 September 2026", ui_output)
                self.assertIn("10:00 AM", ui_output)
                self.assertIn("Presentation", ui_output)
                self.assertIn("Saved as Assignment #", ui_output)


if __name__ == "__main__":
    unittest.main()
