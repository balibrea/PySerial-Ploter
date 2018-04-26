# -*- coding: utf-8 -*-

# A simple setup script to create an executable using PyQt4

import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': 'atexit',
        'excludes': ['Tkinter']
    }
}

executables = [
    #Executable('program.py', base=base, icon="icon[64x64].ico")
    Executable('program.py', icon="icon[64x64].ico")
]

setup(name='Espectro_fotometro',
      version='0.1',
      description='Graficar desde el puerto serie',
      options=options,
      executables=executables
      )
