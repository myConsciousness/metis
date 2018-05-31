# -*- coding: utf-8 -*-

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
import html.parser as htmlparser
import time
from datetime import date, timedelta
import sqlite3
from tqdm import tqdm
from log import LogLevel, Log
from cowsay import Cowsay
from common import *

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

class CrawlingHatena:
    '''Hatenaへのクローリング処理を定義するクラス'''

    # UserAgent定義
    DEF_USER_AGENT = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'}

    def __init__(self, *args, **kwargs):
        '''コンストラクタ

        Note
        ----
        コンストラクタ内で疎通確認に失敗した場合は後続処理を行わない。

        Args
        ----
        *args (tuple): タプルの可変長引数。
        **kwargs (dict): 辞書の可変長引数。

        '''

        # ログ出力のためインスタンス生成
        self.log = Log(child=True)
        # クラス名
        self.CLASS_NAME = self.__class__.__name__

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log.MSG_PROCESS_STARTED)

        try:
            # 疎通確認
            with urlopen('http://info.cern.ch/'):
                pass
        except URLError as e:
            self.root = tkinter.Tk()
            self.root.withdraw()
            self.root.iconbitmap('../common/icon/python_icon.ico')
            messagebox.showerror('ERR_INTERNET_DISCONNECTED', \
                                    'There is no Internet connection\r\n\r\n' \
                                    'Try:\r\n' \
                                    '■Checking the network cables, modem, and router\r\n' \
                                    '■Reconnecting to Wi-Fi')

            self.__handling_url_exception(e)
            return

        self.__execute()

    def __execute(self):
        '''クローリング処理を実行するメソッド'''

        try:
            conn, cursor = connect_to_database()

            # hatenaへのクローリング処理を開始
            self.__crawl_hatena(conn, cursor)

            self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                    self.log.location(), self.log.MSG_PROCESS_COMPLETED)
        except sqlite3.Error as e:
            conn.rollback()
            self.log.normal(LogLevel.ERROR.value, self.CLASS_NAME, \
                                    self.log.location(), self.log.MSG_ERROR)
            self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                    self.log.location(), self.log.MSG_ROLLBACK_COMPLETED)
            self.log.error(e)
        finally:
            conn.close()
            self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                    self.log.location(), self.log.MSG_CLOSE_COMPLETED)
            time.sleep(3)

    def __crawl_hatena(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        '''Hatenaに対してクローリング処理を行うメソッド

        Args
        ----
        conn (sqlite3.Connection): DBとのコネクション。
        cursor (sqlite3.Cursor): カーソル。

        '''

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log.MSG_CRAWLING_STARTED)

        # テック情報TBLの挿入用対応データ
        INSERT_COLUMNS_INFO_TECH_TBL = ['URL', 'TITLE', 'PUBLISHED_DATE', 'BOOKMARKS', 'TAG', 'RESERVED_DEL_DATE']
        # 削除予定日
        RESERVED_DEL_DATE = (date.today() + timedelta(21)).strftime('%Y%m%d')

        cowsay = Cowsay()
        quote = 'Dog goes woof\n' \
                'Cat goes meow\n' \
                'Bird goes tweet\n' \
                'And mouse goes squeek\n' \
                'Cow goes moo\n' \
                'Duck goes quack\n' \
                'And the solution will go to you'

        print(cowsay.cowsay(quote))

        # DBから検索ワードの取得
        SEARCH_WORDS = split(''.join(list(self.__select_params_by_primary_key(cursor, 'SEARCH_WORDS_FOR_TECH_ARTICLES'))), ',')
        for i, word in enumerate(tqdm(SEARCH_WORDS, ncols=60, leave=False, ascii=True, desc='Main process')):
            for page in tqdm(range(1, 6), ncols=60, leave=False, ascii=True, desc='Sub process'):

                # パラメータ生成用辞書
                params = {
                            'q' : word,
                            'page' : page,
                            'safe' : 'on',
                            'sort' : 'recent',
                            'users' : '1'
                        }

                # htmlを取得し抽出用に加工
                html = self.__edit_html(self.__get_html('http://b.hatena.ne.jp/search/tag', params))
                list_infos_of_hatena = self.__scrape_info_of_hatena(html)

                if list_infos_of_hatena:
                    count_duplication = 0
                    for list_article_infos in list_infos_of_hatena:
                        if count_duplication >= 10:
                            # 10回以上重複した場合は処理終了
                            break
                        else:
                            if not self.__select_by_primary_key(cursor, list_article_infos[0]):
                                list_article_infos.append(RESERVED_DEL_DATE)
                                # リストを結合し辞書を生成
                                list_article_infos = dict(zip(INSERT_COLUMNS_INFO_TECH_TBL, list_article_infos))
                                self.__insert_new_article_infos(cursor, list_article_infos)

                                count_duplication = 0
                            else:
                                # 重複している場合
                                count_duplication += 1
                    conn.commit()

            count_changes = conn.total_changes
            print(cowsay.cowsay('Search word is {}.\n{} {} were addded!' \
                                    .format(word, count_changes, 'records' if count_changes > 1 else 'record')))
        print(cowsay.cowsay('The crawling has been completed!'))

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log.MSG_CRAWLING_COMPLETED)

    def __scrape_info_of_hatena(self, html: str) -> list:
        '''HTMLソースに対してスクレイピング処理を行うメソッド

        Note
        ----
        返り値のデータ構造: Two-dimensional Arrays
            [[URL, TITLE, PUBILISHED_DATE, BOOKMARKS, TAG],
            [[URL, TITLE, PUBILISHED_DATE, BOOKMARKS, TAG],...]

        Args
        ----
        html (str): スクレイピング対象HTML。

        Returns
        -------
        スクレイピングした全記事情報を含むリスト。

        '''

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log.MSG_SCRAPING_STARTED)

        if not html:
            return []

        # 情報格納用リスト
        list_infos = []
        while True:
            # 記事に関する情報を抽出
            list_new_article_infos = self.__get_infos_of_article(html)
            if list_new_article_infos:
                # リストから探索処理の終了位置を取り出す
                last_index_of_search = list_new_article_infos.pop()
                list_infos.append(list_new_article_infos)

                if last_index_of_search != -1:
                    # 未取得の記事がある場合
                    html = html[last_index_of_search:]
                else:
                    # ページ内の全情報を取得し終えた場合
                    break
            else:
                # 記事情報を取得できなかった場合
                break

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log.MSG_SCRAPING_COMPLETED)

        return list_infos

    def __get_infos_of_article(self, html: str) -> list:
        '''HTMLソースに対してスクレイピング処理を行い記事情報を取得するメソッド

        Note
        ----
        返り値のデータ構造: Array
            [URL, TITLE, PUBILISHED_DATE, BOOKMARKS, TAG, LAST_INDEX]

        Args
        ----
        html (str): スクレイピング対象HTML。

        Returns
        ----
        スクレイピングした記事情報を含むリスト。
        URLを取得できなかった場合は、
        URL取得以降の処理を行わず空のリストを返す。

        '''

        # 記事情報格納用リスト
        list_article_infos = []
        # 探索開始インデックス
        start_search_index = html.find('centerarticle-entry-title')

        # URL部の取得
        start_index_of_url = html.find('"', html.find('<a', start_search_index))
        end_index_of_url = html.find('"', start_index_of_url+1)
        url = html[start_index_of_url+1:end_index_of_url]

        # 取得したURLが短縮化されていない場合
        if url and not 'ift.tt' in url:
            list_article_infos.append(url)

            # タイトル部の取得
            start_index_of_title = html.find('">', html.find('img', end_index_of_url+1))
            end_index_of_title = html.find('</a', start_index_of_title+1)
            title = html[start_index_of_title+2:end_index_of_title].strip()

            # 取得したタイトルをパースしてリストに格納
            parser = htmlparser.HTMLParser()
            list_article_infos.append(parser.unescape(title))

            # 日付部の取得
            start_index_of_date = html.find('>', html.find('class="entry-contents-date"', end_index_of_title+1))
            end_index_of_date = html.find('</', start_index_of_date+1)
            list_article_infos.append(html[start_index_of_date+1:end_index_of_date])

            # APIからブックマーク数の取得
            params = {'url' : url}
            count_bookmark = self.__get_html(url='http://api.b.st-hatena.com/entry.count', params=params)
            list_article_infos.append(count_bookmark if count_bookmark else '0')

            # 後続ループ処理のためタグ部分のみを抽出
            start_index_of_tag_element = html.find('<ul class="entrysearch-entry-tags">', end_index_of_date)
            html_of_tags = html[start_index_of_tag_element:html.find('</div>', start_index_of_tag_element)]

            # タグ格納用リスト
            list_of_tags = []
            # タグ部終了位置
            end_index_of_tag = ''
            # 最初のアンカータグ開始インデックス
            start_index_of_anchor = html_of_tags.find('<a')

            while start_index_of_anchor != -1:
                # タグの取得
                start_index_of_tag = html_of_tags.find('>', start_index_of_anchor+1)
                end_index_of_tag = html_of_tags.find('</a', start_index_of_tag+1)
                list_of_tags.append(html_of_tags[start_index_of_tag+1:end_index_of_tag])

                start_index_of_anchor = html_of_tags.find('<a', end_index_of_tag)
            else:
                # タグの取得処理完了後処理
                list_article_infos.append(','.join(list_of_tags))

            # 当該処理終了位置の取得と保存
            list_article_infos.append(html.find('class="bookmark-item', end_index_of_title))

        return list_article_infos

    def __get_html(self, url: str, params={}, headers=DEF_USER_AGENT) -> str:
        '''HTTP(s)通信を行いWebサイトからHTMLソースを取得するメソッド

        Note
        ----
        decode時に引数として'ignore'を渡しているのは、
        APIからプレーンテキストを取得する際に文字コードを取得できないことによって、
        プログラムが異常終了するのを防ぐため。

        Args
        ----
        url (str): 取得対象URL。
        params (dict): パラメータ生成用辞書。初期値は空の辞書。
        headers (dict): ヘッダ生成用辞書。初期値は定数"UserAgent定義"。

        Returns
        -------
        対象URLにHTTP(s)通信を行い取得したHTMLソース。
        接続エラー時には空文字を返す。

        '''

        try:
            with urlopen(Request(url='{}?{}'.format(url, urlencode(params)), headers=headers)) as source:
                # リソースから文字コードを取得
                charset = source.headers.get_content_charset(failobj='utf-8')
                # リソースをbytes型からString型にデコード
                html = source.read().decode(charset, 'ignore')
            return html
        except URLError as e:
            # 接続エラー
            self.__handling_url_exception(e, method_name)
            return ''

    def __edit_html(self, html: str) -> str:
        '''取得したHTMLをスクレイピング用に加工するメソッド

        Args
        ----
        html (str): 未加工のHTMLソース。

        Returns
        -------
        スクレイピング用に加工したHTMLソース。

        '''

        start_idx = html.find('<li', html.find('class="entrysearch-articles"'))
        end_idx = html.find('class="centerarticle-pager"', start_idx)

        return html[start_idx+1:end_idx]

    def __handling_url_exception(self, e, method_name: str):
        '''通信処理における例外を処理するメソッド

        Args
        ----
        e : 通信処理において発生した例外情報。

        '''

        if hasattr(e, 'reason'):
            self.log.normal(LogLevel.CRITICAL.value, self.CLASS_NAME, \
                                    self.log.location(), self.log.MSG_NO_SERVER_FOUND)
            self.log.error(e.reason)
        elif hasattr(e, 'code'):
            self.log.normal(LogLevel.CRITICAL.value, self.CLASS_NAME, \
                                    self.log.location(), self.log.MSG_NO_RESPONSE)
            logger.error(e.code)

    def __select_params_by_primary_key(self, cursor: sqlite3.Cursor, primary_key: str) -> tuple:
        '''主キーを用いてパラメータTBLから値を取得するクエリ

        Note
        ----
        返り値はtuple型。

        Args
        ----
        cursor (sqlite3.Cursor): カーソル。
        primary_key (str): 主キー。

        Returns
        -------
        主キーを用いて検索した結果。

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

    def __select_by_primary_key(self, cursor: sqlite3.Cursor, primary_key: str) -> tuple:
        '''主キーを使用してDBから記事情報を取得するクエリ

        Note
        ----
        返り値はtuple型。

        Args
        ----
        cursor (sqlite3.Cursor): カーソル。
        primary_key (str): 主キー。

        Returns
        -------
        主キーを用いて検索した結果。

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
                            INFO_TECH
                        WHERE
                            URL = ?
                        ''', (primary_key,))

        return cursor.fetchone()

    def __insert_new_article_infos(self, cursor: sqlite3.Cursor, article_infos: dict):
        '''取得した記事情報をDBへ挿入するクエリ

        Args
        ----
        cursor (sqlite3.Cursor): カーソル。
        article_infos (dict): カラムと挿入する記事情報の対応辞書。

        '''

        cursor.execute('''
                        INSERT INTO
                            INFO_TECH
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

    conn = sqlite3.connect('../common/db/USER01.db')
    cursor = conn.cursor()

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

if __name__ == '__main__':
    CrawlingHatena()
