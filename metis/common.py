# -*- coding: utf-8 -*-

import sqlite3
import configparser

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

config = configparser.ConfigParser()
config.read('../env/config.ini')

def connect_to_database():
    '''データベースへ接続する関数

    Note
    ----
    コネクションの開放処理は別途行う。

    Returns
    -------
    コネクション、カーソルオブジェクト。

    '''

    # トレースバックの設定
    sqlite3.enable_callback_tracebacks(True)

    conn = sqlite3.connect(config['path']['database'])
    cursor = conn.cursor()

    print(type(conn))

    return conn, cursor

def split(target: str, split_words: str) -> list:
    '''組み込みsplit関数の拡張関数

    Note
    ----
    正規表現を使用しないため高速処理が可能。

    Args
    ----
    target (str): 対象文字列。
    splitlist (str): 区切り文字。

    Returns
    -------
    区切り文字によって分割された文字列のリスト。
    引数の型が正しくない場合はからのリストを返す。

    Examples
    --------
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
