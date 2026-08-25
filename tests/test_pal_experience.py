import unittest

from palworld_pal_edit.PalInfo import (
    PalEntity,
    experience_progress,
    level_for_experience,
    xpthresholds,
)


class PalExperienceTests(unittest.TestCase):
    def make_pal(self, level=12, experience=1600):
        pal = PalEntity.__new__(PalEntity)
        pal._level = level
        pal._exp = experience
        pal._obj = {
            "Level": {"value": {"value": level}},
            "Exp": {"value": experience},
        }
        pal.CleanseAttacks = lambda: None
        return pal

    def test_experience_can_be_read_and_written(self):
        pal = self.make_pal()

        self.assertEqual(1600, pal.GetExp())

        pal.SetExp(1750)

        self.assertEqual(1750, pal.GetExp())
        self.assertEqual(1750, pal._obj["Exp"]["value"])

    def test_changing_level_updates_the_experience_value(self):
        pal = self.make_pal()

        pal.SetLevel(20)

        self.assertEqual(xpthresholds[19], pal.GetExp())
        self.assertEqual(xpthresholds[19], pal._obj["Exp"]["value"])

    def test_experience_is_kept_in_the_save_integer_range(self):
        pal = self.make_pal()

        pal.SetExp(-1)
        self.assertEqual(0, pal.GetExp())

        pal.SetExp(2_147_483_648)
        self.assertEqual(2_147_483_647, pal.GetExp())

    def test_experience_progress_reports_the_current_level_range(self):
        progress = experience_progress(level=1, experience=10, level_cap=80)

        self.assertEqual(0, progress["minimum"])
        self.assertEqual(24, progress["maximum"])
        self.assertEqual(25, progress["next_threshold"])
        self.assertEqual(15, progress["remaining"])
        self.assertEqual(40, progress["percent"])
        self.assertTrue(progress["matches_level"])

    def test_experience_progress_flags_values_outside_the_level_range(self):
        below = experience_progress(level=12, experience=xpthresholds[11] - 1, level_cap=80)
        above = experience_progress(level=12, experience=xpthresholds[12], level_cap=80)

        self.assertFalse(below["matches_level"])
        self.assertFalse(above["matches_level"])

    def test_max_level_progress_has_no_next_level(self):
        progress = experience_progress(level=80, experience=2_147_483_647, level_cap=80)

        self.assertEqual(2_147_483_647, progress["maximum"])
        self.assertIsNone(progress["next_threshold"])
        self.assertIsNone(progress["remaining"])
        self.assertEqual(100, progress["percent"])
        self.assertTrue(progress["matches_level"])

    def test_level_can_be_derived_from_experience(self):
        self.assertEqual(1, level_for_experience(24, level_cap=80))
        self.assertEqual(2, level_for_experience(25, level_cap=80))
        self.assertEqual(80, level_for_experience(2_147_483_647, level_cap=80))


if __name__ == "__main__":
    unittest.main()
