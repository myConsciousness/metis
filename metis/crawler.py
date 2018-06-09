# -*- coding: utf-8 -*-

'''

A Web crawler, sometimes called a spider,
is an Internet bot that systematically browses the World Wide Web,
typically for the purpose of Web indexing (web spidering).

Web search engines and some other sites use Web crawling or spidering software
to update their web content or indices of others sites' web content.
Web crawlers copy pages for processing by a search engine
which indexes the downloaded pages so users can search more efficiently.

Web scraping, web harvesting, or web data extraction is data scraping used for extracting data from websites.
Web scraping software may access the World Wide Web directly using the Hypertext Transfer Protocol, or through a web browser.
While web scraping can be done manually by a software user,
the term typically refers to automated processes implemented using a bot or web crawler.
It is a form of copying, in which specific data is gathered and copied from the web,
typically into a central local database or spreadsheet, for later retrieval or analysis.

'''

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
import html.parser as htmlparser
import time
import sys
import tkinter
from tkinter import messagebox
from datetime import date, timedelta
import sqlite3
from tqdm import tqdm
from log import LogLevel, Log, LogMessage
from cowsay import Cowsay
from common import *
from sql import MstParameterDao
from sql import ArticleInfoHatenaDao
from sql import WorkArticleInfoHatenaDao
from sql import ManageSerialDao

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

class CrawlHandler:
    '''処理オーダ毎にクローラの振る舞いを決定するクラス。'''

    def __init__(self, *args, **kwargs):
        '''コンストラクタ。

        :param tuple args: タプルの可変長引数。
        :param dict kwargs: 辞書の可変長引数。
        '''

        # 処理オーダ
        self.__order = args[0][1]
        # 制御開始
        self.__handle_proc(args[0])

    def __handle_proc(self, args):
        '''処理オーダ毎にプロセスの処理を制御するメソッド。

        :param tuple args: コマンドライン引数。
        '''

        if self.__order == '0':
            # クローリングを行う
            crawler = CrawlingHatena(args)
            crawler.execute()
        elif self.__order == '1':
            # ブックマークの更新処理を行う
            crawler = UpdateBookmarks(args)
            crawler.execute()

class CommunicateBase:
    '''通信処理を定義する基底クラス。'''

    def __init__(self, *args, **kwargs):
        '''コンストラクタ。
        コンストラクタ内で疎通確認に失敗した場合は後続処理を行わない。

        :param tuple args: タプルの可変長引数。
        :param dict kwargs: 辞書の可変長引数。
        '''

        # ログ出力のためインスタンス生成
        self.log = Log(child=True)
        self.log_msg = LogMessage()

        # 基底クラス名
        self.BASE_CLASS_NAME = 'CommunicateBase'

        # インターネットとの疎通確認を行う
        self.__check_internet_connection()

        # MANAGE_SERIAL.TBLのDAOクラス
        self.manage_serial_dao = ManageSerialDao()
        # シリアル番号の整合性チェックを行う
        self.__check_serial_number(args)

        # UserAgent定義
        self.DEF_USER_AGENT = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'}
        # Hatenaブックマーク数取得API
        self.HATENA_BOOKMARK_API = 'http://api.b.st-hatena.com/entry.count'

        # MST_PARAMETER.TBLのDAOクラス
        self.mst_parameter_dao = MstParameterDao()
        # ARTICLE_INFO_HATENA.TBLのDAOクラス
        self.article_info_hatena_dao = ArticleInfoHatenaDao()
        # WORK_ARTICLE_INFO_HATENA.TBLのDAOクラス
        self.work_article_info_hatena_dao = WorkArticleInfoHatenaDao()

    def get_html(self, url: str, params={}, headers={}) -> str:
        '''HTTP(s)通信を行いWebサイトからHTMLソースを取得するメソッド。
        decode時に引数として'ignore'を渡しているのは、
        APIからプレーンテキストを取得する際に文字コードを取得できないことによって、
        プログラムが異常終了するのを防ぐため。
        接続エラー時には空文字を返す。

        :param str url: 取得対象URL。
        :param dict params: パラメータ生成用辞書。初期値は空の辞書。
        :param dict headers: ヘッダ生成用辞書。初期値は空の辞書。
        :rtype: str
        :return: 対象URLにHTTP(s)通信を行い取得したHTMLソース。
        '''

        # 接続先URL
        url = '{}?{}'.format(url, urlencode(params))

        # デバッグログ
        self.log.debug(self.log_msg.MSG_DEBUG_START.format(self.log.get_lineno(), self.log.get_method_name(), self.BASE_CLASS_NAME ))
        self.log.debug(self.log_msg.MSG_DEBUG_VALUE.format(self.log.get_lineno(), 'url', url))
        self.log.debug(self.log_msg.MSG_DEBUG_COMPLETED.format(self.log.get_lineno(), self.log.get_method_name(), self.BASE_CLASS_NAME))

        try:
            with urlopen(Request(url=url, headers=headers)) as source:
                # リソースから文字コードを取得
                charset = source.headers.get_content_charset(failobj='utf-8')
                # リソースをbytes型からString型にデコード
                html = source.read().decode(charset, 'ignore')
            return html
        except URLError as e:
            # 接続エラー
            self.__handling_url_exception(e)
            return ''

    def edit_html(self, html: str, start_name: str, end_name: str) -> str:
        '''取得したHTMLをスクレイピング用に加工するメソッド。

        :param str html: 編集対象HTML
        :param str start_name: 切り取り対象の開始名。
        :param str end_name: 切り取り対象の終了名。
        :rtype: str
        :return: スクレイピング用に加工したHTMLソース。
        '''

        start_idx = html.find(start_name)
        end_idx = html.find(end_name, start_idx)

        return html[start_idx+1:end_idx]

    def __handling_url_exception(self, e):
        '''通信処理における例外を処理するメソッド。

        :param urllib.error.URLError e: 通信処理において発生した例外情報。
        '''

        if hasattr(e, 'reason'):
            self.log.normal(LogLevel.CRITICAL.value, self.BASE_CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_NO_SERVER_FOUND)
            self.log.error(e.reason)
        elif hasattr(e, 'code'):
            self.log.normal(LogLevel.CRITICAL.value, self.BASE_CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_NO_RESPONSE)
            self.log.error(e.code)

    def __check_internet_connection(self):
        '''インターネットとの疎通確認を行うメソッド。
        疎通確認に失敗した場合は後続処理が不可能なためプロセスを終了させる。
        '''

        try:
            # 疎通確認
            with urlopen('http://info.cern.ch/'):
                pass
        except URLError as e:
            root = tkinter.Tk()
            root.withdraw()
            root.iconbitmap('../common/icon/python_icon.ico')
            messagebox.showerror('ERR_INTERNET_DISCONNECTED', \
                                    'There is no Internet connection.\r\n\r\n' \
                                    'Try:\r\n' \
                                    '■Checking the network cables, modem, and router\r\n' \
                                    '■Reconnecting to Wi-Fi')

            self.__handling_url_exception(e)
            # 後続処理継続不可のためプロセス終了
            sys.exit()

    def __check_serial_number(self, args: tuple):
        '''クローラ起動のための整合性チェックを行う。

        :param tuple args: 整合性チェック用のコマンドライン引数。
        '''

        try:
            # データベースへの接続
            conn, cursor = connect_to_database()

            if len(args[0]) < 3:
                # コマンドライン引数が指定数未満の場合
                root = tkinter.Tk()
                root.withdraw()
                root.iconbitmap('../common/icon/python_icon.ico')
                messagebox.showerror('ERR_INVALID_STARTUP', 'The application was unable to start correctly.')

                # 管理テーブルからシリアル番号を消去
                self.flush_serial_number(conn, cursor)
                # 不正な起動のためプロセス終了
                sys.exit()
            else:
                # シリアル番号の取得
                count_record = self.manage_serial_dao.count_records_by_primary_key(cursor, args[0][2])[0]

                if count_record == 0:
                    # 不正なシリアル番号の場合
                    root = tkinter.Tk()
                    root.withdraw()
                    root.iconbitmap('../common/icon/python_icon.ico')
                    messagebox.showerror('ERR_INVALID_SERIAL_NUMBER', 'The serial number is not valid for start up this module.')

                    # 管理テーブルからシリアル番号を消去
                    self.flush_serial_number(conn, cursor)
                    # 不正な起動のためプロセス終了
                    sys.exit()

        except sqlite3.Error as e:
            self.log.normal(LogLevel.ERROR.value, self.BASE_CLASS_NAME, \
                                    self.log.location(),self.log_msg.MSG_ERROR)
            self.log.error(e)
        finally:
            conn.close()
            self.log.normal(LogLevel.INFO.value, self.BASE_CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_CLOSE_COMPLETED)

    def flush_serial_number(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        '''シリアル番号管理テーブルから使用済みシリアル番号を削除するメソッド。

        :param sqlite3.Connection conn: DBとのコネクション。
        :param sqlite3.Cursor cursor: カーソルオブジェクト。
        '''

        # シリアル番号管理テーブルの中身を空にする
        self.manage_serial_dao.delete_records(cursor)
        conn.commit()

class CrawlingHatena(CommunicateBase):
    '''Hatenaへのクローリング処理を定義するクラス。'''

    def __init__(self, *args, **kwargs):
        '''コンストラクタ。
        基底コンストラクタ内で疎通確認に失敗した場合は後続処理を行わない。

        :param tuple args: タプルの可変長引数。
        :param dict kwargs: 辞書の可変長引数。
        '''

        # 基底クラスのコンストラクタを実行
        super().__init__(args[0])

        # クラス名
        self.CLASS_NAME = 'CrawlingHatena'

    def execute(self):
        '''クローリング処理を実行するメソッド。'''

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log_msg.MSG_PROCESS_STARTED)

        try:
            conn, cursor = connect_to_database()

            # 処理開始時においてワークテーブルにレコードが残っている場合は、
            # 前回処理が異常終了したとみなしバックアップ情報の移行処理を行う
            count_records = self.work_article_info_hatena_dao.count_records(cursor)[0]
            if count_records > 0:
                print('Detected an abnormal termination last time a program was run.')
                print('Start the backup operation.............')

                # ワークテーブルからバックアップ情報を移行させる
                self.__migrate_article_info_from_work(conn, cursor)

                print('{} {} were added!'.format(count_records, 'records' if count_records else 'record'))

            # hatenaへのクローリング処理を開始
            self.__crawl_hatena(conn, cursor)
            # 管理テーブルからシリアル番号を消去
            self.flush_serial_number(conn, cursor)
        except sqlite3.Error as e:
            conn.rollback()
            self.log.normal(LogLevel.ERROR.value, self.CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_ERROR)
            self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_ROLLBACK_COMPLETED)
            self.log.error(e)
        finally:
            conn.close()
            self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_CLOSE_COMPLETED)
            self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_PROCESS_COMPLETED)
            time.sleep(3)

    def __crawl_hatena(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        '''Hatenaに対してクローリング処理を行うメソッド。

        :param sqlite3.Connection conn: DBとのコネクション。
        :param sqlite3.Cursor cursor: カーソル。
        '''

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log_msg.MSG_CRAWLING_STARTED)

        cowsay = Cowsay()
        cowquote =  'Dog goes woof\n' \
                    'Cat goes meow\n' \
                    'Bird goes tweet\n' \
                    'And mouse goes squeek\n' \
                    'Cow goes moo\n' \
                    'Duck goes quack\n' \
                    'And the solution will go to you'

        # 処理開始メッセージ
        print(cowsay.cowsay(cowquote))

        # DBから検索ワードの取得
        search_word = split(''.join(list(self.mst_parameter_dao.select_params_by_primary_key(cursor, 'SEARCH_WORDS_4_HATENA'))), ',')
        for i, word in enumerate(tqdm(search_word, ncols=60, leave=False, ascii=True, desc='Main process')):
            count_inserted = 0
            for page in tqdm(range(1, 6), ncols=60, leave=False, ascii=True, desc='Sub process'):

                # デバッグログ
                self.log.debug(self.log_msg.MSG_DEBUG_START.format(self.log.get_lineno(), self.log.get_method_name(), self.CLASS_NAME))
                self.log.debug(self.log_msg.MSG_DEBUG_VALUE.format(self.log.get_lineno(), 'word', word))
                self.log.debug(self.log_msg.MSG_DEBUG_VALUE.format(self.log.get_lineno(), 'page', page))
                self.log.debug(self.log_msg.MSG_DEBUG_COMPLETED.format(self.log.get_lineno(), self.log.get_method_name(), self.CLASS_NAME))

                # パラメータ生成用辞書
                params = {
                            'page' : page,
                            'q' : word,
                            'safe' : 'on',
                            'sort' : 'recent',
                            'users' : '1'
                        }

                # htmlを取得し抽出用に加工
                html = self.get_html(url='http://b.hatena.ne.jp/search/tag', params=params, headers=self.DEF_USER_AGENT)
                # 取得したhtmlをスクレイピング用に加工する
                html = self.edit_html(html, 'class="entrysearch-articles"', 'class="centerarticle-pager"')

                # スクレイピング処理
                article_infos = self.__scrape_info_of_hatena(html)
                # ワークテーブルへ記事情報を登録
                count_inserted += self.__insert_article_info_to_work(conn, cursor, article_infos)

            # ワークテーブルから記事情報を移行させる
            self.__migrate_article_info_from_work(conn, cursor)

            print(cowsay.cowsay('Search word is {}.\n{} {} were addded!' \
                                    .format(word, count_inserted, 'records' if count_inserted > 1 else 'record')))
        print(cowsay.cowsay('The crawling has been completed!'))

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log_msg.MSG_CRAWLING_COMPLETED)

    def __scrape_info_of_hatena(self, html: str) -> list:
        '''HTMLソースに対してスクレイピング処理を行うメソッド。

        :param str html: スクレイピング対象HTML。
        :rtype: list
        :return: スクレイピングした全記事情報を含むリスト。

        >>> scrape_info_of_hatena(html)
        >>> [[URL, TITLE, PUBILISHED_DATE, BOOKMARKS, TAG], [URL, TITLE, PUBILISHED_DATE, BOOKMARKS, TAG],...]
        '''

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log_msg.MSG_SCRAPING_STARTED)

        if not html:
            return []

        # 情報格納用リスト
        list_infos = []

        while True:
            # 記事に関する情報を抽出
            list_new_article_infos = self.__get_infos_of_article(html)

            if len(list_new_article_infos) == 1:
                # リストから探索処理の終了位置を取り出す
                last_index_of_search = list_new_article_infos[0]

                if last_index_of_search != -1:
                    # 記事情報を取得できなかった場合
                    html = html[last_index_of_search:]
                else:
                    # ページ内の全情報を取得し終えた場合
                    break
            else:
                # リストから探索処理の終了位置を取り出す
                last_index_of_search = list_new_article_infos.pop()
                list_infos.append(list_new_article_infos)

                if last_index_of_search != -1:
                    # 未取得の記事がある場合
                    html = html[last_index_of_search:]
                else:
                    # ページ内の全情報を取得し終えた場合
                    break

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log_msg.MSG_SCRAPING_COMPLETED)

        return list_infos

    def __get_infos_of_article(self, html: str) -> list:
        '''HTMLソースに対してスクレイピング処理を行い記事情報を取得するメソッド。
        URLを取得できなかった場合は、URL取得以降の処理を行わず空のリストを返す。

        :param str html: スクレイピング対象HTML。
        :rtype: list
        :return: スクレイピングした記事情報を含むリスト。

        >>> get_infos_of_article(html)
        >>> [URL, TITLE, PUBILISHED_DATE, BOOKMARKS, TAG, LAST_INDEX]
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
            # UnicodeDecodeError回避のために変換処理を行う
            title = parser.unescape(title).encode('cp932', 'ignore').decode('cp932')
            list_article_infos.append(parser.unescape(title))

            # 日付部の取得
            start_index_of_date = html.find('>', html.find('class="entry-contents-date"', end_index_of_title+1))
            end_index_of_date = html.find('</', start_index_of_date+1)
            date = html[start_index_of_date+1:end_index_of_date]
            list_article_infos.append(date)

            # APIからブックマーク数の取得
            params = {'url' : url}
            count_bookmark = self.get_html(url=self.HATENA_BOOKMARK_API, params=params, headers=self.DEF_USER_AGENT)
            # ブックマーク数が0の場合はAPIが空を返すため値の変換処理を行う
            count_bookmark = count_bookmark if count_bookmark else '0'
            list_article_infos.append(count_bookmark)

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

                # アンカータグの開始インデックスを更新
                start_index_of_anchor = html_of_tags.find('<a', end_index_of_tag)
            else:
                # タグの取得処理完了後処理
                tags = ','.join(list_of_tags).encode('cp932', 'ignore').decode('cp932')
                # UnicodeDecodeError回避のために変換処理を行う
                tags = tags.encode('cp932', 'ignore').decode('cp932')
                list_article_infos.append(tags)

            # 当該処理終了位置の取得と保存
            last_index = html.find('class="bookmark-item', end_index_of_title)
            list_article_infos.append(last_index)

            # デバッグログ
            self.log.debug(self.log_msg.MSG_DEBUG_START.format(self.log.get_lineno(), self.log.get_method_name(), self.CLASS_NAME))
            self.log.debug(self.log_msg.MSG_DEBUG_VALUE.format(self.log.get_lineno(), 'url', url))
            self.log.debug(self.log_msg.MSG_DEBUG_VALUE.format(self.log.get_lineno(), 'title', title))
            self.log.debug(self.log_msg.MSG_DEBUG_VALUE.format(self.log.get_lineno(), 'date', date))
            self.log.debug(self.log_msg.MSG_DEBUG_VALUE.format(self.log.get_lineno(), 'tags', tags))
            self.log.debug(self.log_msg.MSG_DEBUG_VALUE.format(self.log.get_lineno(), 'count_bookmark', count_bookmark))
            self.log.debug(self.log_msg.MSG_DEBUG_VALUE.format(self.log.get_lineno(), 'last_index', last_index))
            self.log.debug(self.log_msg.MSG_DEBUG_COMPLETED.format(self.log.get_lineno(), self.log.get_method_name(), self.CLASS_NAME))

        else:
            # デバッグログ
            self.log.debug(self.log_msg.MSG_DEBUG_START.format(self.log.get_lineno(), self.log.get_method_name(), self.CLASS_NAME))
            self.log.debug(self.log_msg.MSG_DEBUG_VALUE.format(self.log.get_lineno(), 'url', url))
            self.log.debug(self.log_msg.MSG_DEBUG_COMPLETED.format(self.log.get_lineno(), self.log.get_method_name(), self.CLASS_NAME))

            # 次処理の探索開始位置をリストで返す
            return [html.find('class="bookmark-item', start_search_index)]

        return list_article_infos

    def __insert_article_info_to_work(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor, article_infos: list) -> int:
        '''ワークテーブルへ記事情報を登録するメソッド。

        :param sqlite3.Connection conn: DBとのコネクション。
        :param sqlite3.Cursor cursor: カーソルオブジェクト。
        :param list article_infos: 記事情報が格納されたリスト。
        :rtype: int
        :return: ワークテーブルへの登録数。
        '''

        if not article_infos:
            return 0

        # 登録数
        count_inserted = 0
        # 重複数
        count_duplication = 0

        # ARTICLE_INFO_TBLの挿入用対応データ
        INSERT_COLUMNS_INFO_TECH_TBL = ['URL', 'TITLE', 'PUBLISHED_DATE', 'BOOKMARKS', 'TAG', 'RESERVED_DEL_DATE']
        # 削除予定日
        RESERVED_DEL_DATE = (date.today() + timedelta(21)).strftime('%Y%m%d')

        for article_info in article_infos:
            if count_duplication >= 10:
                # 10回以上重複した場合は処理終了
                break
            else:
                if not self.article_info_hatena_dao.select_by_primary_key(cursor, article_info[0]):
                    article_info.append(RESERVED_DEL_DATE)
                    # リストを結合し辞書を生成
                    article_info = dict(zip(INSERT_COLUMNS_INFO_TECH_TBL, article_info))
                    # ワークテーブルへ移行対象データを登録
                    self.work_article_info_hatena_dao.insert_article_infos(cursor, article_info)

                    # 移行用データ作成のため登録毎にコミット
                    conn.commit()

                    count_inserted += 1
                    count_duplication = 0
                else:
                    # 重複している場合
                    count_duplication += 1

        return count_inserted

    def __migrate_article_info_from_work(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        '''ワークテーブルからメインテーブルへ記事情報を移行させるメソッド。

        :param sqlite3.Connection conn: DBとのコネクション。
        :param sqlite3.Cursor cursor: カーソルオブジェクト。
        '''

        # ワークテーブルから記事情報を移行させる
        self.article_info_hatena_dao.transfer_article_info_from_work(cursor)
        # ワークテーブル内の情報を削除する
        self.work_article_info_hatena_dao.delete_records(cursor)
        # 移行処理終了
        conn.commit()

class UpdateBookmarks(CommunicateBase):
    '''クローリング済みブックマーク数の更新処理を定義するクラス。'''

    def __init__(self, *args, **kwargs):
        '''コンストラクタ。
        基底コンストラクタ内で疎通確認に失敗した場合は後続処理を行わない。

        :param tuple args: タプルの可変長引数。
        :param dict kwargs: 辞書の可変長引数。
        '''

        # 基底クラスのコンストラクタを実行
        super().__init__(args[0])

        # クラス名
        self.CLASS_NAME = 'UpdateBookmarks'

    def execute(self):
        '''ブックマーク数の更新処理を実行するメソッド。'''

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log_msg.MSG_PROCESS_STARTED)

        try:
            conn, cursor = connect_to_database()

            # ブックマーク数の更新処理を開始
            self.__update_bookmarks(conn, cursor)
            # 管理テーブルからシリアル番号を消去
            self.flush_serial_number(conn, cursor)
        except sqlite3.Error as e:
            conn.rollback()
            self.log.normal(LogLevel.ERROR.value, self.CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_ERROR)
            self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_ROLLBACK_COMPLETED)
            self.log.error(e)
        finally:
            conn.close()
            self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_CLOSE_COMPLETED)
            self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                    self.log.location(), self.log_msg.MSG_PROCESS_COMPLETED)
            time.sleep(3)

    def __update_bookmarks(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        '''ブックマーク数の更新処理を行うメソッド。

        :param sqlite3.Connection conn: DBとのコネクション。
        :param sqlite3.Cursor cursor: カーソル。
        '''

        # テーブルからURLの取得
        urls = self.article_info_hatena_dao.select_all_url(cursor)
        # tuple構造からリスト構造へと変換する
        urls = [url for tuple_url in urls for url in tuple_url]

        if urls:
            cowsay = Cowsay()
            print(cowsay.cowsay('Updating {} {}.' \
                                    .format(len(urls), 'records' if len(urls) > 1 else 'record')))

            for url in tqdm(urls, ncols=60, leave=False, ascii=True, desc='Updating...'):
                # APIからブックマーク数の取得
                params = {'url' : url}
                count_bookmark = self.get_html(url=self.HATENA_BOOKMARK_API, params=params, headers=self.DEF_USER_AGENT)
                # ブックマーク数が0の場合はAPIが空を返すため値の変換処理を行う
                count_bookmark = count_bookmark if count_bookmark else '0'

                # 更新処理
                self.article_info_hatena_dao.update_bookmarks_by_primary_key(cursor, count_bookmark, url)

            conn.commit()
            print(cowsay.cowsay('The update has been completed!'))
        else:
            root = tkinter.Tk()
            root.withdraw()
            root.iconbitmap('../common/icon/python_icon.ico')
            messagebox.showerror('ERR_NO_RECORD_FOUND', 'There is no record in the database.')

if __name__ == '__main__':
    CrawlHandler(sys.argv)
