# -*- coding: utf-8 -*-


"""backup.backup: provides entry point main()."""


import glob
import os
import datetime
import time
from collections import OrderedDict
import sh
import argparse

__version__ = "0.0.1"

BACKUPS_TO_KEEP = -1
HOUR = 60*60
BACKUP_INTERVAL = HOUR*24

parser = argparse.ArgumentParser(
    description="""
    Create rolling backups of a file or folder
    """
)
parser.add_argument("source",  help="Source path to backup")
parser.add_argument("destination",  help="Destination of the backup")
parser.add_argument("--dry-run",  help="Just print the commands to be executed",
                    dest="dry_run", action="store_true")
parser.add_argument("--keep", help=
                    "Number of backups to keep (keep all backups by default)",
                    type=int, default=BACKUPS_TO_KEEP)
parser.add_argument("--interval", help=
                    "Create new backup every INTERVAL hours (default is 24)",
                    type=int, default=BACKUP_INTERVAL)

PROGRAM = {
    "tar": {
        "create": {
            "args": OrderedDict([
                ("mode", "-c"),  # Create
                ("verbose", "-v"),
                ("compress", "-z"),  # Gzip
                ("file", "-f"),  # File to create
                ("file_path", "{}"),
                ("directory", "-C"),  # Change to this dir
                ("directory_path", "{}"),
                ("pattern", "./{}"),  # Globbing pattern inside dir
            ])
        },
        "list": {
            "args": OrderedDict([
                ("mode", "-t"),  # List
                ("verbose", "-v"),
                ("compress", "-z"),  # Gzip
                ("file", "-f"),  # File to list
                ("file_path", "{}"),
            ])
        }
    },
    "rsync": {
        "archive": {
            "args": OrderedDict([
                # -a is the same as -rlptgoD
                # --recursive   recurse into directories
                # --links       copy symlinks as symlinks
                # --perms       preserve permissions
                # --times       preserve times
                # --group       preserve group
                # --owner       preserve owner (super-user only)
                ("archive", "-a"),
                ("verbose", "-v"),  # increase verbosity
                ("compress", "-z"),  # compress file data during the transfer
                # Do not delete partially transferred files, show progress
                # ("partial_progress", "-P"),
                ("progress", "--progress"),  # show progress
                # "exclude": "--exclude",
                # "exclude_pattern": "{}",
                ("source", "{}"),
                ("destination", "{}"),
            ])
        }
    },
}

LOCAL = 0
REMOTE = 1

class Backup:

    dry_run = False

    prefix = "bak"
    tmp = "/tmp"
    source = None
    destination = None
    backup_file_format = ".tar.gz"
    backup_files = None

    timestamp_format = "%Y-%m-%d-%H-%M-%S"
    timestamp_length = 19
    last_timestamp = None

    keep = BACKUPS_TO_KEEP
    interval = BACKUP_INTERVAL

    now = None
    diff = None

    def __init__(self):
        self.tar = sh.Command("tar")
        self.rsync = sh.Command("rsync")
        self.now = datetime.datetime.utcnow()

    def parse_args(self, source,
                   destination,
                   dry_run=None,
                   keep=None,
                   interval=None):

        self.source = source
        self.destination = destination

        if dry_run is not None:
            self.dry_run = dry_run
        if keep is not None:
            self.keep = keep
        if interval is not None:
            self.interval = HOUR*interval

        self.set_backup_files()
        if len(self.backup_files) > 0:
            self.set_last_timestamp()
            self.set_diff()

    @staticmethod
    def get_args(args_dict):
        """
        Convert args_dict to list
        """
        args = []
        for key in args_dict:
            args.append(args_dict[key])
        return args

    def set_backup_files(self):
        pattern = os.path.join(self.destination, "{}-*".format(self.prefix))
        backup_files = glob.glob(pattern)
        backup_files.sort()
        self.backup_files = backup_files

    def set_last_timestamp(self):
        last_backup = self.backup_files[len(self.backup_files) - 1]
        end = -len(self.backup_file_format)
        start = -self.timestamp_length + end
        last_timestamp = last_backup[start:end]
        self.last_timestamp = last_timestamp

    def set_diff(self):
        modified = time.mktime(
            datetime.datetime.strptime(self.last_timestamp,
                                       self.timestamp_format).timetuple()
        )
        ts_now = datetime.datetime.utcnow().timestamp()
        self.diff = ts_now - modified

    def new_filename(self):
        return "{}-{}{}".format(
            self.prefix,
            self.now.strftime(self.timestamp_format),
            self.backup_file_format
        )

    def run(self):
        if self.source[-1:] == os.path.sep:
            # Strip trailing slash otherwise os.path.dirname breaks
            source_dir = os.path.dirname(self.source[:-1])
            source_base = os.path.basename(self.source[:-1])
        else:
            source_dir = os.path.dirname(self.source)
            source_base = os.path.basename(self.source)

        new_backup = os.path.join(self.destination, self.new_filename())

        # Create new backup before removing previous backups
        if self.diff is None or self.diff > self.interval:
            dict_args = PROGRAM["tar"]["create"]["args"]
            dict_args["file_path"] = dict_args["file_path"]\
                .format(new_backup)

            dict_args["directory_path"] = \
                dict_args["directory_path"].format(source_dir)
            dict_args["pattern"] = dict_args["pattern"]\
                .format(source_base)

            args = self.get_args(dict_args)
            if self.dry_run:
                print("tar {}".format(" ".join(args)))
            else:
                self.tar(*args)
                print("Last backup was {} hours ago, new backup created".format(
                    round(self.diff / 60 / 60, 2)))

        # Copy backup to destination

        # Remove old backups
        if self.keep > -1:
            # Refresh list to include new backup
            self.set_backup_files()
            if len(self.backup_files) > self.keep:
                for i in range(len(self.backup_files) - self.keep):
                    backup_file = self.backup_files[i]
                    if os.path.isdir(backup_file):
                        raise Exception("Removing dir backup not implemented")
                    else:
                        if self.dry_run:
                            print("os.remove {}".format(backup_file))
                        else:
                            os.remove(backup_file)


def main():
    args = parser.parse_args()

    b = Backup()
    b.parse_args(args.source,
                 args.destination,
                 args.dry_run,
                 args.keep,
                 args.interval)
    b.run()

    # new_backup = "foo"
    # args_tar_create = PROGRAM["tar"]["create"]["args"]
    # args_tar_create["file_path"] = args_tar_create["file_path"] \
    #     .format(new_backup)
    # print(args_tar_create)
