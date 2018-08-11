# -*- coding: utf-8 -*-

from tkinter import *
from dpi_awareness import *

__author__ = 'Kato Shinya'
__date__ = '2018/08/11'

class TkWinBase:
    '''Tkinterを用いたGUIアプリケーションの基礎定義を行うクラス。'''

    def __init__(self):
        pass

    def set_window_basic_config(self, master, title='Metis', icon='../common/icon/python_icon.ico', expand=True, width=1200, height=710):
        '''ウィンドウにおける基本情報を設定するメソッド。

        :param tkinter.Tk master: 画面のフレーム。
        :param str title: 画面タイトル。
        :param str icon: 画面左上に表示するアイコンへのパス。
        :param bool expand: 画面の拡張 / 縮小可否。
        :param int width: 初期表示時の画面の幅。
        :param int height: 初期表示時の画面の高さ。
        '''

        if expand:
            # 拡張 / 縮小できるように設定
            master.resizable(1, 1)
        else:
            # 拡張 / 縮小できないように設定
            master.resizable(0, 0)

        # タイトルの設定
        master.title(title)
        # アイコンの設定
        master.iconbitmap(icon)
        # 初期表示位置をディスプレイの中央に設定（環境非依存）
        self.__center(master, width=width, height=height)

    def __center(self, master, width: int, height: int):
        '''初期表示時に画面を常に中央に表示するように設定するメソッド。

        :param tkinter.Tk master: 画面のフレーム。
        :param int width: 初期表示時の画面の幅。
        :param int height: 初期表示時の画面の高さ。
        '''

        master.update_idletasks()

        # 画面を表示する幅を求める
        frm_width = master.winfo_rootx() - master.winfo_x()
        win_width = width + 2 * frm_width

        # 画面を表示する高さを求める
        titlebar_height = master.winfo_rooty() - master.winfo_y()
        win_height = height + titlebar_height + frm_width

        # x軸を求める
        x = master.winfo_screenwidth() // 2 - win_width // 2
        # y軸を求める
        y = master.winfo_screenheight() // 2 - win_height // 2

        master.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        master.deiconify()
