##---------------------------------------------------------------------------##
##
## PySol -- a Python Solitaire game
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; see the file COPYING.
## If not, write to the Free Software Foundation, Inc.,
## 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
##---------------------------------------------------------------------------##

import sys, os, locale
import traceback
import gettext

# /***********************************************************************
# // init
# ************************************************************************/

def init():

    if os.name == 'nt' and not os.environ.has_key('LANG'):
        try:
            l = locale.getdefaultlocale()
            os.environ['LANG'] = l[0]
        except:
            pass
    ##locale.setlocale(locale.LC_ALL, '')

    ##locale_dir = 'locale'
    locale_dir = None
    if os.path.isdir(sys.path[0]):
        d = os.path.join(sys.path[0], 'locale')
    else:
        # i.e. library.zip
        d = os.path.join(os.path.dirname(sys.path[0]), 'locale')
    if os.path.exists(d) and os.path.isdir(d):
        locale_dir = d
    ##if locale_dir: locale_dir = os.path.normpath(locale_dir)
    gettext.install('pysol', locale_dir, unicode=True)

    ## init toolkit
    import settings
    if '--gtk' in sys.argv:
        settings.TOOLKIT = 'gtk'
        sys.argv.remove('--gtk')
    else:
        if '--tile' in sys.argv:
            settings.USE_TILE = True
            sys.argv.remove('--tile')
        elif settings.USE_TILE == 'auto':
            # check tile
            import Tkinter
            root = Tkinter.Tk()
            root.withdraw()
            settings.USE_TILE = False
            try:
                tile_version = root.tk.call('package', 'require', 'tile')
            except:
                pass
            else:
                if tile_version >= '0.7.8':
                    settings.USE_TILE = True
            #root.destroy()
            Tkinter._default_root = None
