"""Regression tests for OrderDraft restore/update behaviour."""

import unittest

from order import OrderDraft


class OrderDraftRestoreTests(unittest.TestCase):
    def test_as_dict_after_restore_from_saved_state(self):
        original = OrderDraft()
        original.update(customer_name="Jane", flavour="Vanilla", weight_kg=2, quantity=1)
        saved = original.as_dict()

        # Simulate WhatsAppAgentService restoring a persisted conversation:
        # the previously saved dict (including the derived "missing_fields" key)
        # is fed straight back into update().
        restored = OrderDraft()
        restored.update(**saved)

        # missing_fields() must still be callable, not shadowed by a stored list.
        self.assertTrue(callable(restored.missing_fields))
        result = restored.as_dict()

        self.assertEqual(result["customer_name"], "Jane")
        self.assertIn("phone_number", result["missing_fields"])
        self.assertNotIn("flavour", result["missing_fields"])

    def test_missing_fields_reflects_incomplete_draft(self):
        draft = OrderDraft()
        draft.update(customer_name="Jane")
        missing = draft.missing_fields()

        self.assertIn("flavour", missing)
        self.assertIn("phone_number", missing)


if __name__ == "__main__":
    unittest.main()
