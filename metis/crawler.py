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
from datetime import date, timedelta
import sqlite3
from tqdm import tqdm
from log import LogLevel, Log
from cowsay import Cowsay
from common import *
from sql import *

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

class CrawlingHatena:
    '''Hatenaへのクローリング処理を定義するクラス。'''

    # UserAgent定義
    DEF_USER_AGENT = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'}

    def __init__(self, *args, **kwargs):
        '''コンストラクタ。コンストラクタ内で疎通確認に失敗した場合は後続処理を行わない。

        :param tuple args: タプルの可変長引数。
        :param dict kwargs: 辞書の可変長引数。
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

            self.handling_url_exception(e)
            return

        self.execute()

    def execute(self):
        '''クローリング処理を実行するメソッド。'''

        try:
            conn, cursor = connect_to_database()

            # hatenaへのクローリング処理を開始
            self.crawl_hatena(conn, cursor)

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

    def crawl_hatena(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        '''Hatenaに対してクローリング処理を行うメソッド。

        :param sqlite3.Connection conn: DBとのコネクション。
        :param sqlite3.Cursor cursor: カーソル。
        '''

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log.MSG_CRAWLING_STARTED)

        # テック情報TBLの挿入用対応データ
        INSERT_COLUMNS_INFO_TECH_TBL = ['URL', 'TITLE', 'PUBLISHED_DATE', 'BOOKMARKS', 'TAG', 'RESERVED_DEL_DATE']
        # 削除予定日
        RESERVED_DEL_DATE = (date.today() + timedelta(21)).strftime('%Y%m%d')

        cowsay = Cowsay()
        cowquote =  'Dog goes woof\n' \
                    'Cat goes meow\n' \
                    'Bird goes tweet\n' \
                    'And mouse goes squeek\n' \
                    'Cow goes moo\n' \
                    'Duck goes quack\n' \
                    'And the solution will go to you'

        print(cowsay.cowsay(cowquote))

        # DBから検索ワードの取得
        SEARCH_WORDS = split(''.join(list(select_params_by_primary_key(cursor, 'SEARCH_WORDS_FOR_TECH_ARTICLES'))), ',')
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
                html = self.edit_html(self.get_html('http://b.hatena.ne.jp/search/tag', params))
                list_infos_of_hatena = self.scrape_info_of_hatena(html)

                if list_infos_of_hatena:
                    count_duplication = 0
                    for list_article_infos in list_infos_of_hatena:
                        if count_duplication >= 10:
                            # 10回以上重複した場合は処理終了
                            break
                        else:
                            if not select_by_primary_key(cursor, list_article_infos[0]):
                                list_article_infos.append(RESERVED_DEL_DATE)
                                # リストを結合し辞書を生成
                                list_article_infos = dict(zip(INSERT_COLUMNS_INFO_TECH_TBL, list_article_infos))
                                insert_new_article_infos(cursor, list_article_infos)

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

    def scrape_info_of_hatena(self, html: str) -> list:
        '''HTMLソースに対してスクレイピング処理を行うメソッド。

        :param str html: スクレイピング対象HTML。
        :rtype: list
        :return: スクレイピングした全記事情報を含むリスト。

        >>> scrape_info_of_hatena(html)
        >>> [[URL, TITLE, PUBILISHED_DATE, BOOKMARKS, TAG], [URL, TITLE, PUBILISHED_DATE, BOOKMARKS, TAG],...]
        '''

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log.MSG_SCRAPING_STARTED)

        if not html:
            return []

        # 情報格納用リスト
        list_infos = []
        while True:
            # 記事に関する情報を抽出
            list_new_article_infos = self.get_infos_of_article(html)
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

    def get_infos_of_article(self, html: str) -> list:
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
            list_article_infos.append(parser.unescape(title))

            # 日付部の取得
            start_index_of_date = html.find('>', html.find('class="entry-contents-date"', end_index_of_title+1))
            end_index_of_date = html.find('</', start_index_of_date+1)
            list_article_infos.append(html[start_index_of_date+1:end_index_of_date])

            # APIからブックマーク数の取得
            params = {'url' : url}
            count_bookmark = self.get_html(url='http://api.b.st-hatena.com/entry.count', params=params)
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

    def get_html(self, url: str, params={}, headers=DEF_USER_AGENT) -> str:
        '''HTTP(s)通信を行いWebサイトからHTMLソースを取得するメソッド。
        decode時に引数として'ignore'を渡しているのは、
        APIからプレーンテキストを取得する際に文字コードを取得できないことによって、
        プログラムが異常終了するのを防ぐため。
        接続エラー時には空文字を返す。

        :param str url: 取得対象URL。
        :param dict params: パラメータ生成用辞書。初期値は空の辞書。
        :param dict headers: ヘッダ生成用辞書。初期値は定数"UserAgent定義"。
        :rtype: str
        :return: 対象URLにHTTP(s)通信を行い取得したHTMLソース。
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
            self.handling_url_exception(e, method_name)
            return ''

    def edit_html(self, html: str) -> str:
        '''取得したHTMLをスクレイピング用に加工するメソッド。

        :param str html: 取得対象URL。
        :rtype: str
        :return: スクレイピング用に加工したHTMLソース。
        '''

        start_idx = html.find('<li', html.find('class="entrysearch-articles"'))
        end_idx = html.find('class="centerarticle-pager"', start_idx)

        return html[start_idx+1:end_idx]

    def handling_url_exception(self, e, method_name: str):
        '''通信処理における例外を処理するメソッド。

        :param urllib.error.URLError e: 通信処理において発生した例外情報。
        :param str method_name: メソッド名。
        '''

        if hasattr(e, 'reason'):
            self.log.normal(LogLevel.CRITICAL.value, self.CLASS_NAME, \
                                    self.log.location(), self.log.MSG_NO_SERVER_FOUND)
            self.log.error(e.reason)
        elif hasattr(e, 'code'):
            self.log.normal(LogLevel.CRITICAL.value, self.CLASS_NAME, \
                                    self.log.location(), self.log.MSG_NO_RESPONSE)
            logger.error(e.code)

if __name__ == '__main__':
    CrawlingHatena()
