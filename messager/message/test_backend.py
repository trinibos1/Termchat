import unittest
from unittest.mock import MagicMock
from messager.message.backend import Backend

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.backend = Backend()
        self.backend.supabase = MagicMock()
        mock_user = MagicMock(id="test_user_id")
        mock_auth_response = MagicMock(user=mock_user, error=None)
        mock_auth_response.user = mock_user
        mock_auth_response.error = MagicMock(message=None)
        self.backend.supabase.auth.sign_up.return_value = mock_auth_response
        self.backend.supabase.table("profiles").insert().execute.return_value = (MagicMock(error=None), None)

    def test_signup_success(self):
        user, error = self.backend.signup("test@example.com", "password")
        print(f"User: {user}")
        print(f"Error: {error}")
        print(f"User ID: {user.id}")
        self.assertEqual(user.id, "test_user_id")
        self.assertIsNone(error)

    def test_signup_failure(self):
        self.backend.supabase.auth.return_value.user = None
        self.backend.supabase.auth.return_value.error = MagicMock()
        user, error = self.backend.signup("test@example.com", "password")
        self.assertIsNone(user)
        self.assertEqual(error, "Signup failed")

    def test_add_contact_success(self):
        self.backend.get_profile_by_email = MagicMock(return_value={"id": "contact_id"})
        mock_select_result = MagicMock()
        mock_select_result.data = []
        self.backend.supabase.table("contacts").select().eq().eq().execute.return_value = mock_select_result

        mock_insert_result = MagicMock()
        mock_insert_result.error = None
        self.backend.supabase.table("contacts").insert().execute.return_value = mock_insert_result

        success, error = self.backend.add_contact("owner_id", "contact@example.com")
        self.assertTrue(success)
        self.assertIsNone(error)

    def test_add_contact_not_found(self):
        self.backend.get_profile_by_email = MagicMock(return_value=None)
        success, error = self.backend.add_contact("owner_id", "contact@example.com")
        self.assertFalse(success)
        self.assertEqual(error, "Contact not found")

if __name__ == "__main__":
    unittest.main()