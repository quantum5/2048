from setuptools import setup


setup(
    name='2048',
    version='0.1',
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
    keywords='2048 pygame',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Games/Entertainment',
    ],
)