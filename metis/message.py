# -*- coding: utf-8 -*-

'''
:copyright: (c) 2018 by Kato Shinya.
:license: MIT, see LICENSE for more details.
'''

import tkinter
from tkinter import messagebox
from common import *

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

class ShowMessages:
    '''メッセージの出力を行うクラス。'''

    def __init__(self):
        '''コンストラクタ。'''

        # メッセージ情報の取得
        self.message = read_message_file()

        # メッセージダイアログの設定
        self.root = tkinter.Tk()
        self.root.withdraw()
        self.root.iconbitmap('../common/icon/python_icon.ico')

        # キー : タイトル
        self.KEY_TITLE = 'title'
        # キー : メッセージ
        self.KEY_MESSAGE = 'message'
        # キー : Info
        self.KEY_INFO = 'info'
        # キー : Error
        self.KEY_ERROR = 'error'
        # キー : Echo
        self.KEY_ECHO = 'echo'

    def showinfo(self, id: str, *option_words: tuple):
        '''infoダイアログを出力するメソッド。

        :param id str: タイトル / メッセージ管理番号。
        :param tuple option_words: メッセージ中にバインドする単語を含むタプル。
        '''

        if option_words:
            messagebox.showinfo(self.message[self.KEY_TITLE][self.KEY_INFO][id], self.message[self.KEY_MESSAGE ][self.KEY_INFO][id].format(option_words))
        else:
            messagebox.showinfo(self.message[self.KEY_TITLE][self.KEY_INFO][id], self.message[self.KEY_MESSAGE ][self.KEY_INFO][id])

    def showerror(self, id: str):
        '''errorダイアログを出力するメソッド。

        :param id str: タイトル / メッセージ管理番号。
        '''

        messagebox.showerror(self.message[self.KEY_TITLE][self.KEY_ERROR][id], self.message[self.KEY_MESSAGE ][self.KEY_ERROR][id])

    def askyesno(self, id: str):
        '''質問ダイアログを出力するメソッド。

        :param id str: タイトル / メッセージ管理番号。
        :rtype: bool
        :return: True / False
        '''

        return messagebox.askyesno(self.message[self.KEY_TITLE][self.KEY_INFO][id], self.message[self.KEY_MESSAGE ][self.KEY_INFO][id])

    def get_echo(self, id: str, *option_words: tuple):
        '''エコーメッセージを取得するメソッド。

        :param id str: タイトル / メッセージ管理番号。
        :param tuple option_words: メッセージ中にバインドする単語を含むタプル。
        :rtype: str
        :return: エコーメッセージ。
        '''

        echo_msg = ''
        if option_words:
            echo_msg = self.message[self.KEY_ECHO][id].format(option_words)
        else:
            echo_msg = self.message[self.KEY_ECHO][id]

        return echo_msg
