#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup


setup(
    name='torext-admin',
    description='admin system built on top of torext',
    author='reorx',
    packages=[
        'torext_admin'
    ],
    install_requires=[
        'torext'
    ]
)
