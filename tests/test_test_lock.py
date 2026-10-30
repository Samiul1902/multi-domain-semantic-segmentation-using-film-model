import unittest
from pathlib import Path
from src.data.kub_dataset import KUBDataset, TestAccessError
from src.utils.test_lock import verify_test_lock


class TestTestLock(unittest.TestCase):
    def test_artifact(self): self.assertEqual(verify_test_lock()["test_sample_count"],1683)
    def test_development_access_blocked(self):
        with self.assertRaises(TestAccessError): KUBDataset(Path(r'D:\Softfors\jup\manifests\test.csv'),"TEST")

if __name__=="__main__": unittest.main()
