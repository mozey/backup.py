# WARNING

Under construction. Was going to use this to create backups of text file based
system like `taskwarrior` but using git on my home dir is more convenient.
 
That said, this project serves as an example of the layout for CLI python util
that can be published to PYPI or installed directly from github.


# backup.py

Wrapper around tar, ssh and rsync 

Create rolling backups of a file or folder


# tl;dr

Local only

    backup.py --dry-run /my/folder /backups

Local to remote
    
    backup.py --dry-run /my/folder user@server:/backups

Remote to local

    backup.py --dry-run user@server:/backups /my/folder 


# Install

[pip install from github repo branch](http://stackoverflow.com/a/20101940/639133)

    pip install git+https://github.com/mozey/backup.py.git


# Configuration

    TODO

