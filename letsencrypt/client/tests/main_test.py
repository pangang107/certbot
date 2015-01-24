"""letsencrypt.scripts.main.py tests."""
import unittest

import mock
import zope.component


class RollbackTest(unittest.TestCase):
    """Test the rollback function."""
    def setUp(self):
        self.m_install = mock.MagicMock()
        self.m_input = mock.MagicMock()
        zope.component.getUtility = self.m_input

    def _call(self, checkpoints):
        from letsencrypt.scripts.main import rollback
        rollback(checkpoints)

    @mock.patch("letsencrypt.scripts.main.determine_installer")
    def test_no_problems(self, mock_det):
        mock_det.side_effect = self.m_install

        self._call(1)

        self.assertEqual(self.m_install().rollback_checkpoints.call_count, 1)
        self.assertEqual(self.m_install().restart.call_count, 1)

    @mock.patch("letsencrypt.client.reverter.Reverter")
    @mock.patch("letsencrypt.scripts.main.determine_installer")
    def test_misconfiguration_fixed(self, mock_det, mock_rev):
        from letsencrypt.client.errors import LetsEncryptMisconfigurationError
        mock_det.side_effect = [LetsEncryptMisconfigurationError,
                                self.m_install]
        self.m_input().generic_yesno.return_value = True

        self._call(1)

        # Don't rollback twice... (only on one object)
        self.assertEqual(self.m_install().rollback_checkpoints.call_count, 0)
        self.assertEqual(mock_rev().rollback_checkpoints.call_count, 1)

        # Only restart once
        self.assertEqual(self.m_install.restart.call_count, 1)

    @mock.patch("letsencrypt.scripts.main.logging.warning")
    @mock.patch("letsencrypt.client.reverter.Reverter")
    @mock.patch("letsencrypt.scripts.main.determine_installer")
    def test_misconfiguration_remains(self, mock_det, mock_rev, mock_warn):
        from letsencrypt.client.errors import LetsEncryptMisconfigurationError
        mock_det.side_effect = LetsEncryptMisconfigurationError

        self.m_input().generic_yesno.return_value = True

        self._call(1)

        # Don't rollback twice... (only on one object)
        self.assertEqual(self.m_install().rollback_checkpoints.call_count, 0)
        self.assertEqual(mock_rev().rollback_checkpoints.call_count, 1)

        # Never call restart because init never succeeds
        self.assertEqual(self.m_install().restart.call_count, 0)
        # There should be a warning about the remaining problem
        self.assertEqual(mock_warn.call_count, 1)

    @mock.patch("letsencrypt.client.reverter.Reverter")
    @mock.patch("letsencrypt.scripts.main.determine_installer")
    def test_user_decides_to_manually_investigate(self, mock_det, mock_rev):
        from letsencrypt.client.errors import LetsEncryptMisconfigurationError
        mock_det.side_effect = LetsEncryptMisconfigurationError

        self.m_input().generic_yesno.return_value = False

        self._call(1)

        # Neither is ever called
        self.assertEqual(self.m_install().rollback_checkpoints.call_count, 0)
        self.assertEqual(mock_rev().rollback_checkpoints.call_count, 0)

    @mock.patch("letsencrypt.scripts.main.determine_installer")
    def test_no_installer(self, mock_det):
        mock_det.return_value = None

        # Just make sure no exceptions are raised
        self._call(1)


if __name__ == '__main__':
    unittest.main()
