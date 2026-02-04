import unittest
import sqlite3
import os
from discord_ai_bot import PersistenceManager, SystemState, ResourceManager, is_safe_prompt

class TestClairCore(unittest.TestCase):

    def setUp(self):
        """Runs BEFORE every test. Sets up a temporary test DB."""
        self.test_db = "test_clair.db"
        self.db = PersistenceManager(self.test_db)

    def tearDown(self):
        """Runs AFTER every test. Cleans up the file."""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_database_persistence(self):
        """Test if the DB actually remembers stuff."""
        # 1. Save a message
        self.db.save_message(12345, "user", "Hello Clair")

        # 2. Retrieve it
        history = self.db.get_recent_context(12345, limit=1)

        # 3. Assert it matches
        self.assertEqual(history[0]['content'], "Hello Clair")
        print("\n✅ Database Persistence Passed")

    def test_limit_logic(self):
        """Test if the daily limit actually blocks users."""
        user_id = 999
        # 1. Use up 2 slots (Limit is 3 for images)
        self.db.check_and_increment(user_id, "image", 3)
        self.db.check_and_increment(user_id, "image", 3)

        # 2. Check the 3rd slot (Should be allowed)
        allowed, msg = self.db.check_and_increment(user_id, "image", 3)
        self.assertTrue(allowed)

        # 3. Check the 4th slot (Should fail)
        allowed, msg = self.db.check_and_increment(user_id, "image", 3)
        self.assertFalse(allowed)
        self.assertIn("Daily Limit", msg)
        print("\n✅ Usage Limits Passed")

    def test_safety_filter(self):
        """Test the regex filter."""
        self.assertTrue(is_safe_prompt("A beautiful sunset"))
        self.assertFalse(is_safe_prompt("Show me a toddler"))
        print("\n✅ Safety Filter Passed")

if __name__ == '__main__':
    unittest.main()
