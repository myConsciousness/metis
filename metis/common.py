# -*- coding: utf-8 -*-

import sqlite3
import configparser

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

config = configparser.ConfigParser()
config.read('../env/config.ini')

def connect_to_database():
    '''データベースへ接続する関数。
    コネクションの開放処理は呼び出し元で別途行う。

    :rtype: sqlite3.Cursor
    :rtype: sqlite3.Connection
    :return: コネクション。
    :return: カーソルオブジェクト。
    '''

    # トレースバックの設定
    sqlite3.enable_callback_tracebacks(True)

    conn = sqlite3.connect(config['path']['database'])
    cursor = conn.cursor()

    return conn, cursor

def split(target: str, split_words: str) -> list:
    '''組み込みsplit関数の拡張関数。
    正規表現を使用しないため高速処理が可能。

    :param str target: 対象文字列。
    :param str splitlist: 区切り文字。
    :rtype: list
    :return: 区切り文字によって分割された文字列のリスト。

    >>> split('test//sp"rit%st$ring', '/"%$')
    >>> ['test', 'sp', 'rit', 'st', 'ring']
    >>>
    >>> ''.join(split('test//sp"rit%st$ring', '/"%$'))
    >>> testspritstring

    '''

    output = []
    atsplit = True

    for char in target:
        if char in split_words:
            atsplit = True
        else:
            if atsplit:
                output.append(char)
                atsplit = False
            else:
                output[-1] += char
    return output
