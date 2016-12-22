import unittest
import os
from backup import backup

# https://docs.python.org/3/library/unittest.html
# Run individual tests like this:
# python test.py Tests.testSyncFolder

verbose = False
temp_dir = "/tmp"

test_data = os.path.join(os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))), "test_data")


def debug_print(*args):
    # When writing the tests we might want to print extra info
    if verbose:
        print(*args)


class Tests(unittest.TestCase):
    def setUp(self):
        pass

    def testSyncFolder(self):
        b = backup.Backup(
            source=test_data,
            destination=temp_dir,
            dry_run=True)
        b.run()

    def testSyncFile(self):
        source = os.path.join(test_data, "d.txt")
        b = backup.Backup(
            source=source,
            destination=temp_dir,
            dry_run=True,
            interval=0)
        b.run()

if __name__ == "__main__":
    # To debug run like this
    # VERBOSE=1 python test.py Tests.testSyncFolder
    if "VERBOSE" in os.environ:
        verbose = True

    # Use temp dir as given by OS
    if "TMPDIR" in os.environ:
        temp_dir = os.environ["TMPDIR"]

    unittest.main()

