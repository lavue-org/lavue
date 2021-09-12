#!/usr/bin/env python
# Copyright (C) 2017  DESY, Christoph Rosemann, Notkestr. 85, D-22607 Hamburg
#
# lavue is an image viewing program for photon science imaging detectors.
# Its usual application is as a live viewer using hidra as data source.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation in  version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
#
# Authors:
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#

""" setup.py for setting Lavue"""

import codecs
import os
import sys
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from distutils.command.clean import clean
from distutils.util import get_platform
import shutil

try:
    from sphinx.setup_command import BuildDoc
except Exception:
    BuildDoc = None


def read(fname):
    """ read the file

    :param fname: readme file name
    :type fname: :obj:`str`
    """
    with codecs.open(os.path.join('.', fname), encoding='utf-8') as f:
        long_description = f.read()
    return long_description

# from sphinx.setup_command import BuildDoc


#: (:obj:`str`) package name
NAME = 'lavuelib'
#: (:obj:`module`) package name
lavuepackage = __import__(NAME)
#: (:obj:`str`) full release version
release = lavuepackage.__version__
#: (:obj:`str`) package version
version = ".".join(release.split(".")[:2])

#: (:obj:`str`) .ui file directory
UIDIR = os.path.join(NAME, "ui")
#: (:obj:`str`) .qrc file directory
QRCDIR = os.path.join(NAME, "qrc")
#: (:obj:`list` < :obj:`str` >) executable scripts
SCRIPTS = ['lavuemonitor', 'lavuezmqstreamfromtango',
           'LavueController', 'lavuezmqstreamtest']
#: (:obj:`list` < :obj:`str` >) executable GUI scripts
GUISCRIPTS = ['lavue', 'lavuetaurus']

needs_pytest = set(['test']).intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

install_requires = [
    'pyqtgraph>=0.10.0',
    'numpy>1.6.0',
    'pyzmq',
    'scipy',
    'h5py',
    'pytz',
    'requests',
    # 'pyside',
    # 'pyqt5',
    # 'fabio',
    # 'pytango',
    # 'pydoocs',
    # 'pillow',
    # 'hidra',
    # 'pninexus',
    # 'nxstools',
    # 'pyFAI',
]


class toolBuild(build_py):
    """ ui and qrc builder for python
    """

    @classmethod
    def makeqrc(cls, qfile, path):
        """  creates the python qrc files

        :param qfile: qrc file name
        :type qfile: :obj:`str`
        :param path:  qrc file path
        :type path: :obj:`str`
        """
        qrcfile = os.path.join(path, "%s.qrc" % qfile)
        rccfile = os.path.join(path, "%s.rcc" % qfile)

        compiled = os.system("rcc %s -o %s -binary" % (qrcfile, rccfile))
        if compiled == 0:
            print("Built: %s -> %s" % (qrcfile, rccfile))
        else:
            sys.stderr.write("Error: Cannot build  %s\n" % (rccfile))
            sys.stderr.flush()

    def run(self):
        """ runner

        :brief: It is running during building
        """

        try:
            qfiles = [(qfile[:-4], QRCDIR) for qfile
                      in os.listdir(QRCDIR) if qfile.endswith('.qrc')]
            for qrc in qfiles:
                if not qrc[0] in (".", ".."):
                    self.makeqrc(qrc[0], qrc[1])
        except TypeError:
            sys.stderr.write("No .qrc files to build\n")
            sys.stderr.flush()

        if get_platform()[:3] == 'win':
            for script in GUISCRIPTS:
                shutil.copy(script, script + ".pyw")
        build_py.run(self)


class toolClean(clean):
    """ cleaner for python
    """

    def run(self):
        """ runner

        :brief: It is running during cleaning
        """

        cfiles = [os.path.join(NAME, cfile) for cfile
                  in os.listdir("%s" % NAME) if cfile.endswith('.pyc')]
        for fl in cfiles:
            os.remove(str(fl))

        cfiles = [os.path.join(UIDIR, cfile) for cfile
                  in os.listdir(UIDIR) if (
                      cfile.endswith('.pyc') or
                      (cfile.endswith('.py')
                       and not cfile.endswith('__init__.py')))]
        for fl in cfiles:
            os.remove(str(fl))

        cfiles = [os.path.join(QRCDIR, cfile) for cfile
                  in os.listdir(QRCDIR) if (
                      cfile.endswith('.pyc')
                      or cfile.endswith('.rcc') or
                      (cfile.endswith('.py')
                       and not cfile.endswith('__init__.py')))]
        for fl in cfiles:
            os.remove(str(fl))

        if get_platform()[:3] == 'win':
            for script in SCRIPTS:
                if os.path.exists(script + ".pyw"):
                    os.remove(script + ".pyw")
        clean.run(self)


def get_scripts(scripts):
    """ provides windows names of python scripts

    :param scripts: list of script names
    :type scripts: :obj:`list` <:obj:`str`>
    """
    if get_platform()[:3] == 'win':
        return scripts + [sc + '.pyw' for sc in scripts]
    return scripts


#: (:obj:`dict` <:obj:`str`, :obj:`list` <:obj:`str`> > ) package data
package_data = {
    'lavuelib': ['ui/*.ui', 'qrc/*.rcc']
}


#: (:obj:`dict` <:obj:`str`, `any`>) metadata for distutils
SETUPDATA = dict(
    name='lavue',
    version=release,
    description='Live image viewer application for photon science detectors.',
    long_description=read('README.rst'),
    # long_description_content_type='text/x-rst',
    install_requires=install_requires,
    url='https://github.com/lavue-org/lavue',
    author='J.Kotanski, Ch.Rosemann, A.Rothkirch',
    author_email='jan.kotanski@desy.de, '
    'christoph.rosemann@desy.de, '
    'andre.rothkirch@desy.de ',
    license='GPLv2',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='live viewer photon science detector',
    packages=find_packages(exclude=['test']),
    package_data=package_data,
    # package_dir={'lauvelib': 'lavuelib'},
    # include_package_data=True, # do not include image an qrc files
    scripts=(get_scripts(GUISCRIPTS) + SCRIPTS),
    zip_safe=False,
    setup_requires=pytest_runner,
    tests_require=['pytest'],
    cmdclass={
        "build_py": toolBuild,
        "clean": toolClean,
        "build_sphinx": BuildDoc
    },
    command_options={
        'build_sphinx': {
            'project': ('setup.py', NAME),
            'version': ('setup.py', version),
            'release': ('setup.py', release)}},
)


def main():
    """ the main function
    """
    setup(**SETUPDATA)


if __name__ == '__main__':
    main()
