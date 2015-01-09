'''
Created on Jan 1, 2015

@author: Mark V Systems Limited
(c) Copyright 2015 Mark V Systems Limited, All rights reserved.
'''
import sys, os, datetime

setup_requires = []
# install_requires specifies a list of package dependencies that are 
# installed when 'python setup.py install' is run. On Linux/Mac systems 
# this also allows installation directly from the github repository 
# (using 'pip install -e git+git://github.com/rheimbuchArelle.git#egg=Arelle') 
# and the install_requires packages are auto-installed as well.
install_requires = []
options = {}
scripts = []
cxFreezeExecutables = []
cmdclass = {}

from distutils.command.build_py import build_py as _build_py


if sys.platform in ('darwin', 'linux2', 'linux', 'sunos5'): # works on ubuntu with hand-built cx_Freeze
    from setuptools import find_packages 
    try:
        from cx_Freeze import setup, Executable  
        cx_FreezeExecutables = [ 
            Executable( 
                script="CntlrAppSvr.py", 
                )                             
            ] 
    except:
        from setuptools import setup
        cx_FreezeExecutables = []

    packages = find_packages('.', # note that new setuptools finds plugin and lib unwanted stuff
                             exclude=['*.cli.*', '*.UI.*'])
    dataFiles = None 
    includeFiles = []
    if sys.platform == 'darwin':
        pass
    else: 
        if os.path.exists("/etc/redhat-release"):
            # extra libraries needed for red hat
            includeFiles.append(('/usr/local/lib/libexslt.so', 'libexslt.so'))
            includeFiles.append(('/usr/local/lib/libxml2.so', 'libxml2.so'))
            # for some reason redhat needs libxml2.so.2 as well
            includeFiles.append(('/usr/local/lib/libxml2.so.2', 'libxml2.so.2'))
            includeFiles.append(('/usr/local/lib/libxslt.so', 'libxslt.so'))
            includeFiles.append(('/usr/local/lib/libz.so', 'libz.so'))
            
    if os.path.exists("version.txt"):
        includeFiles.append(('version.txt', 'version.txt'))
        
    includeLibs = ['pg8000']
    if sys.platform != 'sunos5':
        try:
            import pyodbc # see if this is importable
            includeLibs.append('pyodbc')  # has C compiling errors on Sparc
        except ImportError:
            pass
    options = dict( build_exe =  { 
        "include_files": includeFiles,
        "includes": includeLibs,
        "packages": packages, 
        } ) 
    if sys.platform == 'darwin':
        options["bdist_mac"] = {"iconfile": 'arelle/images/arelle.icns',
                                "bundle_name": 'Arelle'}
        
    
elif sys.platform == 'win32':
    from setuptools import find_packages
    from cx_Freeze import setup, Executable 
    # py2exe is not ported to Python 3 yet
    # setup_requires.append('py2exe')
    # FIXME: this should use the entry_points mechanism
    packages = find_packages('.')
    print("packages={}".format(packages))
    dataFiles = None
    win32includeFiles = []
    if os.path.exists("version.txt"):
        win32includeFiles.append('version.txt')
        
    options = dict( build_exe =  {
        "include_files": win32includeFiles,
        "include_msvcr": True, # include MSVCR100
        "packages": packages,
        #
        # rdflib & isodate egg files: rename .zip cpy lib & egg-info subdirectories to site-packages directory
        #
        "includes": ['pg8000'], 
        } )
   
    # windows uses arelleGUI.exe to launch in GUI mode, arelleCmdLine.exe in command line mode
    cx_FreezeExecutables = [
        Executable(
                script="arelleApp.py",
                ),
        ]
else:  
    #print("Your platform {0} isn't supported".format(sys.platform)) 
    #sys.exit(1) 
    from setuptools import os, setup, find_packages
    packages = find_packages('.', # note that new setuptools finds plugin and lib unwanted stuff
                             exclude=['*.cli.*', '*.UI.*'])
    dataFiles = [('cli','cli'), 
                         ('cli\\images','cli/images'),
                         ('UI','UI')]
    cx_FreezeExecutables = []

timestamp = datetime.datetime.utcnow()
setup(name='Arelle',
      # for version use year.month.day.hour (in UTC timezone) - must be 4 integers for building
      version=timestamp.strftime("%Y.%m.%d.%H"),
      description='An open source XBRL platform',
      long_description=open('README.txt').read(),
      author='arelle.org',
      author_email='support@arelle.org',
      url='http://www.arelle.org',
      download_url='http://www.arelle.org/download',
      cmdclass=cmdclass,
      include_package_data = True,   # note: this uses MANIFEST.in
      packages=packages,
      data_files=dataFiles,
      platforms = ['OS Independent'],
      license = 'Apache-2',
      keywords = ['xbrl'],
      classifiers = [
          'Development Status :: 1 - Active',
          'Intended Audience :: End Users/Server',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache-2 License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Operating System :: OS Independent',
          'Topic :: XBRL Validation and Versioning',
          ],
      scripts=scripts,
      entry_points = {
          'console_scripts': [
              'arelle-app=svr.CntlrAppSvr:main',
          ]
      },
      setup_requires = setup_requires,
      install_requires = install_requires,
      options = options,
      executables = cx_FreezeExecutables,
     )

