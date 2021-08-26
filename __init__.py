#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :__init__.py.py
# @Time      :2021/8/26 9:39
# @Author    :Zhao Bing
# @Email     :zhaobingtech@163.com


# from __future__ import absolute_import

# __all__ = ['HeadFile', 'HeadFileLib', 'trans_hdf_2_tdms']

# Make version number available
# from .version import __version_info__, __version__
print("You have imported mypackage")
# Export public objects
from .HeadFileLib.HeadConvertLib import trans_hdf_2_tdms
    # HeadFile

print('lib_init')
