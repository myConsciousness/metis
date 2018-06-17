# -*- coding: utf-8 -*-

'''
:copyright: (c) 2018 by Kato Shinya.
:license: MIT, see LICENSE for more details.
'''

import sqlite3
import json
import string
import random
import hashlib

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

def read_config_file():
    '''構成管理ファイルを読み込む関数。

    :rtype: dict
    :return: 構成情報を格納した辞書。
    '''

    # 構成管理ファイルの読み込み
    with open('../env/userConfig.json', 'r') as f:
        return json.load(f)

def read_log_message_file():
    '''ログメッセージ管理ファイルを読み込む関数。

    :rtype: dict
    :return: ログメッセージ情報を格納した辞書。
    '''

    # ログメッセージ管理ファイルの読み込み
    with open('../env/logMessage.json', 'r') as f:
        return json.load(f)

def read_message_file():
    '''メッセージ管理ファイルを読み込む関数。

    :rtype: dict
    :return: メッセージ情報を格納した辞書。
    '''

    # メッセージ管理ファイルの読み込み
    with open('../env/message.json', 'r') as f:
        return json.load(f)

def create_serial_number():
    '''シリアル番号を生成する関数。

    :rtype: str
    :return: シリアル番号。
    '''

    return convert_to_hash_sha256(create_random_str(random.randint(40, 70)))

def create_random_str(num_letters: int) -> str:
    '''ランダムな文字列を生成する関数。

    :param str num_letters: 生成する文字列の長さ。
    :rtype: str
    :return: 生成されたランダムな文字列。
    '''

    return ''.join([random.choice(string.ascii_letters + string.digits) for i in range(num_letters)])

def convert_to_hash_sha256(message: str) -> str:
    '''SHA256アルゴリズムを用いて文字列をハッシュ化する関数。

    :param str message: ハッシュ化する文字列。
    :rtype: str
    :return: ハッシュ化された文字列。
    '''

    return hashlib.sha256(message.encode('cp932')).hexdigest()

def connect_to_database(isolation_level='EXCLUSIVE'):
    '''データベースへ接続する関数。
    コネクションの開放処理は呼び出し元で別途行う。

    :param str isolation_level: トランザクション分離レベルを指定する。初期値は'EXCLUSIVE'。
    :rtype: sqlite3.Cursor
    :rtype: sqlite3.Connection
    :return: コネクション。
    :return: カーソルオブジェクト。
    '''

    # 設定ファイルの読み込み
    config = read_config_file()

    # トレースバックの設定
    sqlite3.enable_callback_tracebacks(True)

    conn = sqlite3.connect(config['path']['database'], isolation_level=isolation_level)
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
