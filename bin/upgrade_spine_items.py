#!/usr/bin/env python

import os

print(
    """This is a script for upgrading spine-items.
Copyright (C) <2017-2021>  <Spine project consortium>
This program comes with ABSOLUTELY NO WARRANTY; This is free software, and you are welcome to redistribute it
under certain conditions; See files COPYING and COPYING.LESSER for details.
"""
)
print("")
os.system("pip uninstall -y spine-items")
print("")
os.system("pip install --upgrade git+https://github.com/Spine-project/spine-items.git#egg=spine_items")