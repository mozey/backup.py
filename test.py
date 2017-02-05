import unittest
import os
import sh

from backup import backup
from datetime import timedelta
import logging
import sys

logger = logging.getLogger(__name__)

temp_dir = "/tmp"

test_data = os.path.join(os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))), "test_data")


def clear_tmp_backup_files(b):
    find = sh.Command("find")
    args = [temp_dir, "-name", "{}*".format(b.prefix)]
    backup_files = find(*args)
    for file in backup_files:
        file = file.replace("\n", "")
        pardir = os.path.dirname(file)
        if pardir == temp_dir:
            if os.path.isfile(file):
                logger.info("rm {}".format(file))
                os.remove(file)


class Tests(unittest.TestCase):
    def setUp(self):
        pass

    def testParseArgs(self):
        b = backup.Backup()
        now = b.now

        clear_tmp_backup_files(b)

        # Touch test backup files
        def touch_bak(interval):
            touch = sh.Command("touch")
            b.now = now - timedelta(seconds=interval)
            filename = b.new_filename()
            filepath = os.path.join(temp_dir, filename)
            touch_args = [filepath]
            touch(*touch_args)
            logger.info("touch {}".format(filepath))
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
        # it is the execution time since touching the file and parse_args,
        # assuming it won't take more than 5 seconds
        assert 5 > b.diff - b.interval >= 0

        clear_tmp_backup_files(b)

    def testCreateNewBackup(self):
        b = backup.Backup()
        b.parse_args(source=test_data,
                     destination=temp_dir,
                     dry_run=None)
        filename = b.new_filename()
        b.diff = b.interval * 2.5  # create_new_backup expect this to be set
        b.create_new_backup(b.destination, filename)
        filepath = os.path.join(b.destination, filename)

        # Test backup file was created
        logger.info(filepath)
        assert os.path.exists(filepath)

        # Print backup file content
        logger.info(b.list_backup(filepath))

        clear_tmp_backup_files(b)

    def testSync(self):
        b = backup.Backup()

        # dry_run = True
        dry_run = None

        def sync(source):
            keep = 1
            b.parse_args(source=source,
                         destination=temp_dir,
                         dry_run=dry_run,
                         keep=keep)
            b.run()
            b.parse_args(source=source,
                         destination=temp_dir,
                         dry_run=dry_run,
                         keep=keep)
            b.run()

        # Test sync folder
        sync(test_data)
        b.set_backup_files()
        assert len(b.backup_files) == 1
        clear_tmp_backup_files(b)

        # Test sync file
        b = backup.Backup()
        sync(os.path.join(test_data, "d.txt"))
        b.set_backup_files()
        assert len(b.backup_files) == 1
        clear_tmp_backup_files(b)

if __name__ == "__main__":
    # To debug with verbose mode set run like this
    # VERBOSE=1 python test.py -v
    # VERBOSE=1 python test.py -v Tests.testSync
    if "VERBOSE" in os.environ:
        if os.environ["VERBOSE"] == "1":
            logger.setLevel(logging.DEBUG)
            backup.logger.setLevel(logging.DEBUG)
            # Have to do this because of the way unittest works
            # http://stackoverflow.com/a/7483862/639133
            stream_handler = logging.StreamHandler(sys.stdout)
            logger.addHandler(stream_handler)

    # TODO Use tempfile module instead?
    # http://stackoverflow.com/a/847866/639133
    # Use temp dir as given by OS
    if "TMPDIR" in os.environ:
        temp_dir = os.environ["TMPDIR"].rstrip(os.path.sep)

    unittest.main()

