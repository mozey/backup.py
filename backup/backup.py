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
                    "Number of backups to keep (-1 to keep all backups)",
                    type=int, default=-1)


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

    args = {
        "tar_create": OrderedDict([
            ("mode", "-c"),  # Create
            ("verbose", "-v"),
            ("compress", "-z"),  # Gzip
            ("file", "-f"),  # File to create
            ("file_path", "{}"),
            ("directory", "-C"),  # Change to this dir
            ("directory_path", "{}"),
            ("pattern", "./{}"),  # Globbing pattern inside dir
        ]),
        # tar -tvzf FILE
        "tar_list": OrderedDict([
            ("mode", "-t"),  # List
            ("verbose", "-v"),
            ("compress", "-z"),  # Gzip
            ("file", "-f"),  # File to list
            ("file_path", "{}"),
        ]),
        "rsync_args": OrderedDict([
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
    }

    def __init__(self):
        self.tar = sh.Command("tar")
        self.rsync = sh.Command("rsync")
        self.now = datetime.datetime.utcnow()

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
        if self.diff > self.interval:
            tar_create = self.args["tar_create"]
            tar_create["file_path"] = tar_create["file_path"]\
                .format(new_backup)
            if os.path.isdir(self.source):
                tar_create["directory_path"] = tar_create["directory_path"]\
                    .format(source_dir)
                tar_create["pattern"] = tar_create["pattern"]\
                    .format(source_base)
            else:
                # TODO Support for file source
                raise Exception("File source not implemented")
            tar_create_args = self.get_args(tar_create)
            if self.dry_run:
                print("tar {}".format(" ".join(tar_create_args)))
            else:
                # TODO Use rsync to implement --no-compress arg
                # TODO Use rsync to support remote destination
                self.tar(*tar_create_args)
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
    b = Backup()

    args = parser.parse_args()
    b.dry_run = args.dry_run
    b.backups_to_keep = args.keep
    b.source = args.source
    b.destination = args.destination

    b.set_backup_files()
    b.set_last_timestamp()
    b.set_diff()

    b.run()
