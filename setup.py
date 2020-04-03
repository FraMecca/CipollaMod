import sys

from distutils.core import setup

packages = [
        'cipolla.authentication',
        'cipolla.authentication.services',
        'cipolla.authentication.services.vanilla',
        'cipolla.game',
        'cipolla.game.awards',
        'cipolla.game.client',
        'cipolla.game.command',
        'cipolla.game.command.commands',
        'cipolla.game.edit',
        'cipolla.game.gamemode',
        'cipolla.game.gamemode.bases',
        'cipolla.game.map',
        'cipolla.game.player',
        'cipolla.game.room',
        'cipolla.game.timing',
        'cipolla.permissions',
        'cipolla.protocol',
        'cipolla.punitive_effects',
        'cipolla.server',
        'cipolla.server.binding',
        'cipolla.server.lan_info',
        'cipolla.utils',
        'cipolla.mods',
]

packages.extend([
    'cipolla',
    'cube2map',
    'txENet',
    'twisted.plugins'
])

dependencies = [
    "twisted",
    "pyenet>=0.0.0",
    "python-Levenshtein",
]

setup(
    name="cipolla",
    version="0.1",
    packages=packages,
    package_dir={'' : 'src'},
    package_data={
        'twisted': ['plugins/cipolla_server.py'],
        'cipolla': ['data/*.json', 'data/*.cfg']
    },
    install_requires=dependencies,
    author="Chasm",
    author_email="fd.chasm@gmail.com",
    url="https://github.com/fdChasm/cipolla",
    license="MIT",
    description="A Python implementation of the Sauerbraten Cube 2 server on top of Twisted.",
    dependency_links = [
        'http://github.com/fdChasm/pyenet/tarball/master#egg=pyenet-0.1.0',
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Games/Entertainment :: First Person Shooters",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: zlib/libpng License",
        "Natural Language :: English"
    ],
)
