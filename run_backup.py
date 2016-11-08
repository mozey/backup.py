#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Convenience wrapper for running backup.py directly from source tree."""
import sys

from backup.backup import main


if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:
        # Exit on KeyboardInterrupt
        # http://stackoverflow.com/a/21144662/639133
        print()
        print('Keyboard interrupt')
        sys.exit(0)
