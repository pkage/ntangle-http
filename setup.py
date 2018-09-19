#!/usr/bin/env python

from setuptools import setup

setup(name='ntangle-http',
        version='1.0',
        description='ntangle to http bridge',
        author='Patrick Kage',
        author_email='patrick.r.kage@gmail.com',
        packages=['nhttp'],
        install_requires=[
            'pyzmq',
            'msgpack-python',
            'click',
            'aiohttp',
            'cchardet'
        ],
        entry_points={
            'console_scripts': [
                'nhttp=nhttp:main'
                ]
            }
        )
