import unittest
import os

import sh

from backup import backup
from datetime import timedelta

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

    def testParseArgs(self):
        b = backup.Backup()
        now = b.now

        # Clear test backup files
        find = sh.Command("find")
        args = [temp_dir, "-name", "{}*".format(b.prefix)]
        backup_files = find(*args)
        for file in backup_files:
            file = file.replace("\n", "")
            pardir = os.path.dirname(file)
            if pardir == temp_dir:
                if os.path.isfile(file):
                    debug_print("rm {}".format(file))
                    os.remove(file)

        # Touch test backup files
        def touch_bak(interval):
            touch = sh.Command("touch")
            b.now = now - timedelta(seconds=interval)
            filename = b.new_filename()
            filepath = os.path.join(temp_dir, filename)
            touch_args = [filepath]
            touch(*touch_args)
            debug_print("touch {}".format(filepath))
        touch_bak(b.interval*3)
        touch_bak(b.interval*2)
        touch_bak(b.interval)

        b.parse_args(source=test_data,
                     destination=temp_dir,
                     dry_run=True)

        # Test set_backup_files
        assert len(b.backup_files) == 3

        # Test set_last_timestamp,
        # assuming we touched the latest file last
        assert b.last_timestamp == b.now.strftime(b.timestamp_format)

        # diff should be fractionally bigger than interval,
        # it is the execution time since touching the file and parse_args
        assert 1 > b.diff - b.interval > 0

    def testCreateTarGz(self):
        b = backup.Backup()
        b.parse_args(source=test_data,
                     destination=temp_dir,
                     dry_run=True)
        print(b.backup_files)
        print(b.now)
        # b.run()

    def testSyncFolder(self):
        b = backup.Backup()
        b.parse_args(source=test_data,
                     destination=temp_dir,
                     dry_run=True)
        b.run()

    def testSyncFile(self):
        source = os.path.join(test_data, "d.txt")
        b = backup.Backup()
        b.parse_args(source=source,
                     destination=temp_dir,
                     dry_run=True,
                     interval=0)
        b.run()

if __name__ == "__main__":
    # To debug with verbose mode set run like this
    # VERBOSE=1 python test.py Tests.testSyncFolder
    if "VERBOSE" in os.environ:
        verbose = True

    # TODO Use tempfile module instead?
    # http://stackoverflow.com/a/847866/639133
    # Use temp dir as given by OS
    if "TMPDIR" in os.environ:
        temp_dir = os.environ["TMPDIR"].rstrip(os.path.sep)

    unittest.main()

