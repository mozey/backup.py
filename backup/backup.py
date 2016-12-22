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


parser = argparse.ArgumentParser(
    description="""
    Create rolling backups of a file or folder
    """
)
parser.add_argument("source",  help="Source path to backup")
parser.add_argument("destination",  help="Destination of the backup")
parser.add_argument("--dry-run",  help="Just print the commands to be executed",
                    dest="dry_run", action="store_true")
parser.add_argument("--keep",  help=
                    "Number of backups to keep (keep all backups by default)",
                    type=int, default=-1)
parser.add_argument("--interval",  help=
                    "Create new backup every INTERVAL hours (default is 24)",
                    type=int, default=-1)


args_tar_create = OrderedDict([
    ("mode", "-c"),  # Create
    ("verbose", "-v"),
    ("compress", "-z"),  # Gzip
    ("file", "-f"),  # File to create
    ("file_path", "{}"),
    ("directory", "-C"),  # Change to this dir
    ("directory_path", "{}"),
    ("pattern", "./{}"),  # Globbing pattern inside dir
])

# tar -tvzf FILE
args_tar_list = OrderedDict([
    ("mode", "-t"),  # List
    ("verbose", "-v"),
    ("compress", "-z"),  # Gzip
    ("file", "-f"),  # File to list
    ("file_path", "{}"),
])

args_rsync = OrderedDict([
    # -a is the same as -rlptgoD
    # --recursive   recurse into directories
    # --links       copy symlinks as symlinks
    # --perms       preserve permissions
    # --times       preserve times
    # --group       preserve group
    # --owner       preserve owner (super-user only)
    ("archive", "-a"),
    ("progress", "--progress"),
    # "exclude": "--exclude",
    # "exclude_pattern": "{}",
    ("source", "{}"),
    ("destination", "{}"),
])


class Backup:

    dry_run = False

    prefix = "bak"
    tmp = "/tmp"
    source = None
    destination = None
    # TODO Support backup file formats other than ".tar.gz"
    backup_file_format = ".tar.gz"
    backup_files = None

    timestamp_format = "%Y-%m-%d-%H-%M-%S"
    timestamp_length = 19
    last_timestamp = None

    backups_to_keep = -1  # -1 to keep all backups
    HOUR = 60*60
    interval = HOUR*24

    now = None
    diff = None

    def __init__(self, source, destination,
                 dry_run=None,
                 backups_to_keep=None,
                 interval=None):
        self.tar = sh.Command("tar")
        self.rsync = sh.Command("rsync")
        self.now = datetime.datetime.utcnow()

        self.source = source
        self.destination = destination

        if dry_run is not None:
            self.dry_run = dry_run
        if backups_to_keep is not None:
            self.backups_to_keep = backups_to_keep
        if interval is not None:
            self.interval = self.HOUR*interval

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
        self.diff = self.now.timestamp() - modified

    def run(self):
        if self.source[-1:] == os.path.sep:
            # Strip trailing slash otherwise os.path.dirname breaks
            source_dir = os.path.dirname(self.source[:-1])
            source_base = os.path.basename(self.source[:-1])
        else:
            source_dir = os.path.dirname(self.source)
            source_base = os.path.basename(self.source)

        new_backup = os.path.join(self.destination, "bak-{}{}".format(
            datetime.datetime.strftime(self.now, self.timestamp_format),
            self.backup_file_format
        ))

        # Create new backup before removing previous backups
        print(0)
        if self.diff is None or self.diff > self.interval:
            args_tar_create["file_path"] = args_tar_create["file_path"]\
                .format(new_backup)
            print(1)
            if os.path.isdir(self.source):
                print(2)
                args_tar_create["directory_path"] = \
                    args_tar_create["directory_path"].format(source_dir)
                args_tar_create["pattern"] = args_tar_create["pattern"]\
                    .format(source_base)
            else:
                print(3)
                # TODO Support for file source
                raise Exception("File source not implemented")
            args = self.get_args(args_tar_create)
            if self.dry_run:
                print("tar {}".format(" ".join(args)))
            else:
                # TODO Support for rsync --no-compress arg
                # TODO Support for rsync remote destination
                self.tar(*args)
                print("Last backup was {} hours ago, new backup created".format(
                    round(self.diff / 60 / 60, 2)))

        # Remove old backups
        if self.backups_to_keep > -1:
            # Refresh list to include new backup
            self.set_backup_files()
            if len(self.backup_files) > self.backups_to_keep:
                for i in range(len(self.backup_files) - self.backups_to_keep):
                    backup_file = self.backup_files[i]
                    if os.path.isdir(backup_file):
                        raise Exception("Removing dir backup not implemented")
                    else:
                        if self.dry_run:
                            # TODO Use sh.rm instead?
                            print("os.remove {}".format(backup_file))
                        else:
                            os.remove(backup_file)


def main():
    args = parser.parse_args()

    b = Backup(
        args.source,
        args.destination,
        args.dry_run,
        args.keep)
    b.run()
