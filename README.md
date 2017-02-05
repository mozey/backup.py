# backupy

Wrapper around tar, ssh and rsync 

Create rolling backups of a file or folder


# tl;dr

Local only

    # Run from source
    backupy/run_back.py --dry-run backupy/test_data /tmp

    # If installed with pip, see below
    backupy --dry-run backupy/test_data /tmp 

TODO Local to remote
    
    backupy --dry-run /my/folder user@server:/backups

TODO Remote to local

    backupy --dry-run user@server:/backups /my/folder 


# Install

[pip install from github repo branch](http://stackoverflow.com/a/20101940/639133)

    pip install git+https://github.com/mozey/backupy.git


