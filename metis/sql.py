# -*- coding: utf-8 -*-

'''

SQLite is a relational database management system contained in a C programming library.
In contrast to many other database management systems, SQLite is not a client–server database engine.
Rather, it is embedded into the end program.

SQLite is ACID-compliant and implements most of the SQL standard,
using a dynamically and weakly typed SQL syntax that does not guarantee the domain integrity.

SQLite is a popular choice as embedded database software
for local/client storage in application software such as web browsers.
It is arguably the most widely deployed database engine,
as it is used today by several widespread browsers, operating systems,
and embedded systems (such as mobile phones), among others.

SQLite has bindings to many programming languages.

'''

import sqlite3

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

class MstParameterDao:
    '''MST_PARAMETER.TBLへのトランザクション処理を定義するDAOクラス。'''

    def select_params_by_primary_key(self, cursor: sqlite3.Cursor, primary_key: str) -> tuple:
        '''主キーを用いてMST_PARAMETER.TBLから値を取得するクエリ。返り値はtuple型。

        :param sqlite3.Cursor cursor: カーソル。
        :param str primary_key: 検索ワード。
        :rtype: tuple
        :return: 検索結果。
        '''

        cursor.execute('''
                        SELECT
                            VALUE
                        FROM
                            MST_PARAMETER
                        WHERE
                            PARAM_NAME = ?
                        ''', (primary_key,))

        return cursor.fetchone()

class ManageSerialDao:
    '''MANAGE_SERIAL.TBLへのトランザクション処理を定義するDAOクラス。'''

    def insert_serial_no(self, cursor: sqlite3.Cursor, serial_no: str):
        '''生成したシリアル番号をMANAGE_SERIAL.TBLへ挿入するクエリ。

        :param sqlite3.Cursor cursor: カーソル。
        :param str serial_no: クローラ起動用のシリアル番号。
        '''

        cursor.execute('''
                        INSERT INTO
                            MANAGE_SERIAL
                        VALUES (
                            ?,
                            datetime('now', 'localtime')
                        )
                        ''',(serial_no,))

    def count_records_by_primary_key(self, cursor: sqlite3.Cursor, primary_key: str) -> tuple:
        '''主キーを用いてMANAGE_SERIAL.TBLから値を取得するクエリ。返り値はtuple型。

        :param sqlite3.Cursor cursor: カーソル。
        :param str primary_key: 検索ワード。
        :rtype: tuple
        :return: 検索結果。
        '''

        cursor.execute('''
                        SELECT
                            COUNT(1)
                        FROM
                            MANAGE_SERIAL
                        WHERE
                            SERIAL_NO = ?
                        ''', (primary_key,))

        return cursor.fetchone()

    def count_records(self, cursor: sqlite3.Cursor):
        '''MANAGE_SERIAL.TBLのレコード数を取得するクエリ。

        :param sqlite3.Cursor cursor: カーソル。
        :rtype: tuple
        :return: 取得件数。
        '''

        cursor.execute('''
                        SELECT
                            COUNT(1)
                        FROM
                            MANAGE_SERIAL
                        ''')

        return cursor.fetchone()

    def delete_records(self, cursor: sqlite3.Cursor):
        '''MANAGE_SERIAL.TBLから全レコードを削除するクエリ。

        :param sqlite3.Cursor cursor: カーソル。
        '''

        cursor.execute('''
                        DELETE FROM
                            MANAGE_SERIAL
                        ''')

class ArticleInfoHatenaDao:
    '''ARTICLE_INFO_HATENA.TBLへのトランザクション処理を定義するDAOクラス。'''

    def select_by_primary_key(self, cursor: sqlite3.Cursor, search_word: str) -> tuple:
        '''検索ワードを用いてARTICLE_INFO_HATENA.TBLから記事情報を取得するクエリ。返り値はtuple型。

        :param sqlite3.Cursor cursor: カーソル。
        :param str search_word: 検索ワード。
        :rtype: tuple
        :return: 検索結果。
        '''

        cursor.execute('''
                        SELECT
                            URL,
                            TITLE,
                            PUBLISHED_DATE,
                            BOOKMARKS,
                            TAG,
                            REGISTER_DATE,
                            UPDATED_DATE,
                            RESERVED_DEL_DATE
                        FROM
                            ARTICLE_INFO_HATENA
                        WHERE
                            URL = ?
                        ''', (search_word,))

        return cursor.fetchone()

    def select_all_url(self, cursor: sqlite3.Cursor) -> tuple:
        '''ARTICLE_INFO_HATENA.TBLから全URLを取得するクエリ。返り値はtuple型。

        :param sqlite3.Cursor cursor: カーソル。
        :rtype: tuple
        :return: 登録されている全URL。
        '''

        cursor.execute('''
                        SELECT
                            URL
                        FROM
                            ARTICLE_INFO_HATENA
                        ''')

        return cursor.fetchall()

    def update_bookmarks_by_primary_key(self, cursor: sqlite3.Cursor, bookmarks: str, primary_key: str):
        '''主キーを用いてARTICLE_INFO_HATENA.TBLのブックマーク数を更新するクエリ。返り値はtuple型。

        :param sqlite3.Cursor cursor: カーソル。
        :param str bookmarks: ブックマーク数。
        :param str primary_key: 主キー。
        '''

        cursor.execute('''
                        UPDATE
                            ARTICLE_INFO_HATENA
                        SET
                            BOOKMARKS = ?
                        WHERE
                            URL = ?
                        ''',(bookmarks, primary_key,))


    def insert_article_infos(self, cursor: sqlite3.Cursor, article_infos: dict):
        '''取得した記事情報をARTICLE_INFO_HATENA.TBLへ挿入するクエリ。

        :param sqlite3.Cursor cursor: カーソル。
        :param dict article_infos: カラムと挿入する記事情報の対応辞書。
        '''

        cursor.execute('''
                        INSERT INTO
                            ARTICLE_INFO_HATENA
                        VALUES (
                            :URL,
                            :TITLE,
                            :PUBLISHED_DATE,
                            :BOOKMARKS,
                            :TAG,
                            datetime('now', 'localtime'),
                            datetime('now', 'localtime'),
                            :RESERVED_DEL_DATE
                        )
                        ''',(article_infos))

    def select_infos_by_search_word(self, cursor: sqlite3.Cursor, search_word: str) -> tuple:
        '''ARTICLE_INFO_HATENA.TBLから記事情報を取得するクエリ。返り値はtuple型。

        :param sqlite3.Cursor cursor: カーソル。
        :param str search_word: 検索ワード。
        :rtype: tuple
        :return: 検索結果。
        '''

        cursor.execute('''
                        SELECT
                            URL,
                            TITLE,
                            PUBLISHED_DATE,
                            BOOKMARKS,
                            TAG,
                            REGISTER_DATE,
                            UPDATED_DATE,
                            RESERVED_DEL_DATE
                        FROM
                            ARTICLE_INFO_HATENA
                        WHERE
                            TAG
                        LIKE
                            ?
                        ''',(search_word,))

        return cursor.fetchall()

    def transfer_article_info_from_work(self, cursor: sqlite3.Cursor):
        '''WORK_ARTICLE_INFO_HATENA.TBLからARTICLE_INFO_HATENA.TBLへ記事情報を移行させるクエリ。

        :param sqlite3.Cursor cursor: カーソル。
        :param dict article_infos: カラムと挿入する記事情報の対応辞書。
        '''

        cursor.execute('''
                        INSERT INTO
                            ARTICLE_INFO_HATENA
                        SELECT
                            URL,
                            TITLE,
                            PUBLISHED_DATE,
                            BOOKMARKS,
                            TAG,
                            REGISTER_DATE,
                            UPDATED_DATE,
                            RESERVED_DEL_DATE
                        FROM
                            WORK_ARTICLE_INFO_HATENA
                        ''')

class WorkArticleInfoHatenaDao:
    '''WORK_ARTICLE_INFO_HATENA.TBLへのトランザクション処理を定義するDAOクラス。'''

    def count_records(self, cursor: sqlite3.Cursor):
        '''WORK_ARTICLE_INFO_HATENA.TBLのレコード数を取得するクエリ。

        :param sqlite3.Cursor cursor: カーソル。
        '''

        cursor.execute('''
                        SELECT
                            COUNT(1)
                        FROM
                            WORK_ARTICLE_INFO_HATENA
                        ''')

        return cursor.fetchone()

    def insert_article_infos(self, cursor: sqlite3.Cursor, article_infos: dict):
        '''取得した記事情報をWORK_ARTICLE_INFO_HATENA.TBLへ挿入するクエリ。

        :param sqlite3.Cursor cursor: カーソル。
        :param dict article_infos: カラムと挿入する記事情報の対応辞書。
        '''

        cursor.execute('''
                        INSERT INTO
                            WORK_ARTICLE_INFO_HATENA
                        VALUES (
                            :URL,
                            :TITLE,
                            :PUBLISHED_DATE,
                            :BOOKMARKS,
                            :TAG,
                            datetime('now', 'localtime'),
                            datetime('now', 'localtime'),
                            :RESERVED_DEL_DATE
                        )
                        ''',(article_infos))

    def delete_records(self, cursor: sqlite3.Cursor):
        '''WORK_ARTICLE_INFO_HATENA.TBLから全レコードを削除するクエリ。

        :param sqlite3.Cursor cursor: カーソル。
        '''

        cursor.execute('''
                        DELETE FROM
                            WORK_ARTICLE_INFO_HATENA
                        ''')
