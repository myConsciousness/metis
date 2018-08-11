# -*- coding: utf-8 -*-

import os
import re
from tkinter import *

__author__ = 'Kato Shinya'
__date__ = '2018/08/11'

def make_tk_dpi_aware(master):
    '''Tkinterを高DPIに対応させる関数。'''

    master.DPI_X, master.DPI_Y, master.DPI_scaling = __get_hwnd_dpi(master.winfo_id())
    master.TkScale = lambda v: int(float(v) * master.DPI_scaling)
    master.TkGeometryScale = lambda s: __tkGeometry_scale(s, master.TkScale)

def __get_hwnd_dpi(window_handle):
    '''Tkinterを高DPIのディスプレイに対応させるため、DPIとスケーリングを再計算する関数。'''

    if os.name == 'nt':
        from ctypes import windll, pointer, wintypes
        try:
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            # Windows serverやバージョンの低いWindowsでは失敗する
            pass

        # 拡大率を100%に設定
        DPI100pc = 96
        # MDT_EFFECTIVE_DPI = 0, MDT_ANGULAR_DPI = 1, MDT_RAW_DPI = 2
        DPI_type = 0

        winH = wintypes.HWND(window_handle)
        monitorhandle = windll.user32.MonitorFromWindow(winH, wintypes.DWORD(2))

        X = wintypes.UINT()
        Y = wintypes.UINT()

        try:
            windll.shcore.GetDpiForMonitor(monitorhandle, DPI_type, pointer(X), pointer(Y))
            return X.value, Y.value, (X.value + Y.value) / (2 * DPI100pc)
        except Exception:
            # Windows標準のDPIとスケーリング
            return 96, 96, 1
    else:
        return None, None, 1

def __tkGeometry_scale(s, cvtfunc):
    '''座標の再設定を行う関数。'''

    # 形式 'WxH+X+Y'
    regex = r'(?P<W>\d+)x(?P<H>\d+)\+(?P<X>\d+)\+(?P<Y>\d+)'
    R = re.compile(regex).search(s)

    G = str(cvtfunc(R.group('W'))) + 'x'
    G += str(cvtfunc(R.group('H'))) + '+'
    G += str(cvtfunc(R.group('X'))) + '+'
    G += str(cvtfunc(R.group('Y')))

    return G
