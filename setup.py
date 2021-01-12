import os

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    long_description = f.read()

setup(
    name='2048',
    version='0.3.3',
    packages=['_2048'],
    package_data={
        '_2048': ['*.ttf'],
    },

    entry_points={
        'console_scripts': [
            '2048 = _2048.main:main',
        ],
        'gui_scripts': [
            '2048w = _2048.main:main'
        ]

    },
    install_requires=['pygame', 'appdirs'],

    author='quantum',
    author_email='quantum2048@gmail.com',
    url='https://github.com/quantum5/2048',
    description="Quantum's version of the 2048 game, with multi-instance support,"
                'restored from an old high school project.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='2048 pygame',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Games/Entertainment',
    ],
)
