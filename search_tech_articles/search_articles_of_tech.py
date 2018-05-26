# -*- coding: utf-8 -*-

from urllib.request import Request, urlopen, URLError, HTTPError
from urllib.parse import urlencode
import html.parser as htmlparser
from datetime import date, datetime, timedelta
import json
import os.path
import sqlite3
from logging import getLogger, FileHandler, StreamHandler, Formatter
import tkinter
from tkinter import messagebox
import tkinter.ttk as ttk
from tkinter import N, S, W, E
import webbrowser
import pyperclip
import tkinter.scrolledtext as tkst
from tqdm import tqdm

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

# ログの設定
PATH_TO_LOG_FILE = '../log/' + datetime.today().strftime('%Y%m%d') + '.log'
logger = getLogger(__name__)
logger.setLevel(10)
fh = FileHandler(PATH_TO_LOG_FILE)
logger.addHandler(fh)
fh.setFormatter(Formatter('%(asctime)s:%(levelname)s:[%(lineno)d]%(name)s:%(message)s'))

# UserAgent定義
DEF_USER_AGENT = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'}

class SearchArticlesOfTech(tkinter.Tk):

    def __init__(self):
        # ログファイルの有効性チェック
        check_status_of_log_file(PATH_TO_LOG_FILE)

        self.root = tkinter.Tk()
        self.notebook = ttk.Notebook(self.root, height=500, width=999)

        # top画面用のフレーム
        frameUpdateArticles = tkinter.Frame(self.notebook, bd=2, relief='groove')
        # log検索画面用のフレーム
        frameShowLog = tkinter.Frame(self.notebook, bd=2, relief='groove')
        # top画面用のタブ
        self.notebook.add(frameUpdateArticles, text='Top')
        # log検索画面用のタブ
        self.notebook.add(frameShowLog, text='Log')

        # TOP画面の作成
        self.create_top_gui(frameUpdateArticles)
        # ログ出力画面の作成
        self.create_log_gui(frameShowLog)

        self.notebook.grid(row=0, column=0, sticky=N+S+W+E)

        # ウィンドウの設定
        self.root.resizable(0, 0)
        self.root.iconbitmap('../common/icon/python_icon.ico')
        self.root.title('Search Tech Articles')
        self.root.geometry('1000x500+400+250')

        self.root.mainloop()

    def create_top_gui(self, parent):
        '''
        TOP画面のGUIを作成する関数
        '''

        # エラー・メッセージ用ラベルの表示
        self.lblForError = tkinter.Label(parent, font=('Consolas', 10), foreground='#ff0000')
        self.lblForError.pack()


    def create_log_gui(self, parent):
        '''
        Log検索画面のGUIを作成する関数
        '''

        # 入力フォームの設定
        lblDate = tkinter.Label(parent, font=('Consolas', 10), text='Enter the date.')
        lblDate.pack()
        self.inputDate = ttk.Entry(parent, font=('Consolas', 10), justify='center', width=20)
        self.inputDate.insert(tkinter.END, datetime.today().strftime('%Y/%m/%d'))
        self.inputDate.bind('<Leave>', self.call_read_func)
        self.inputDate.pack()

        # 出力用フォームの設定
        frameTextLog = tkinter.Frame(parent, pady=10, bd=0)
        frameTextLog.pack()
        self.OutputTextLog = tkst.ScrolledText(frameTextLog, font=('Consolas', 10), height=24, width=130)
        self.OutputTextLog.pack()

        # readボタン
        read_button = ttk.Button(parent, text='Read', width=10, command=self.read_log_button)
        read_button.place(relx=0.25, rely=0.86)
        # 一覧ボタン
        list_button = ttk.Button(parent, text='List', width=10, command=self.list_log_button)
        list_button.place(relx=0.45, rely=0.86)
        # 終了ボタン
        quit_button = ttk.Button(parent, text='Quit', width=10, command=self.quit_button)
        quit_button.place(relx=0.65, rely=0.86)

    def read_log_button(self):
        '''
        readボタン押下時の処理を定義
        '''

        # 出力用テキストフォームが空ではない場合
        if self.MyUtil.required(self.OutputTextLog.get('1.0',tkinter.END)):
            # テキストフォームの初期化
            self.OutputTextLog.delete('1.0', tkinter.END)

        input_date = self.inputDate.get()
        if '.log' in input_date:
            # ファイル名と拡張子を分割
            root, ext = os.path.splitext(input_date)
            # 入力された日付を処理用に加工
            date = ''.join(self.MyUtil.split_string(root, '-/., '))
            # 参照するログのパス
            path_name = '../log/' + date + '.log'
        else:
            # 入力された日付を処理用に加工
            date = ''.join(self.MyUtil.split_string(input_date, '-/., '))
            # 参照するログのパス
            path_name = '../log/' + date + '.log'

        # 指定したパスが存在する場合
        if os.path.exists(path_name):
            text_lines = ''
            with open(path_name, 'r') as f:
                text_lines = f.readlines()

            # 取得した行数分だけ処理
            for line in text_lines:
                self.OutputTextLog.insert(tkinter.END, line)
            self.OutputTextLog.pack()
        else:
            # ログファイルが存在しなかった場合
            self.OutputTextLog.insert(tkinter.END, 'Failed to open log file\r\nno such file or directory')

    def call_read_func(self, event):
        '''
        log出力画面におけるマウスアウト時処理
        '''
        # readボタン押下時の処理を呼び出す
        self.read_log_button()

    def list_log_button(self):
        '''
        listボタン押下時の処理を定義
        '''

        # 出力用テキストフォームが空ではない場合
        if self.MyUtil.required(self.OutputTextLog.get('1.0',tkinter.END)):
            # テキストフォームの初期化
            self.OutputTextLog.delete('1.0', tkinter.END)

        # logディレクトリ内のファイルを取得
        log_files = os.listdir('../log')
        for log in log_files:
            # ファイル名と拡張子を分割
            _, ext = os.path.splitext(log)
            if ext == '.log':
                self.OutputTextLog.insert(tkinter.END, log + '\r\n')
        self.OutputTextLog.pack()


class CrawlingAndScrapingArticlesOfTech:
    '''クローリングとスクレイピングの処理を定義したクラス'''

    def __init__(self, conn: object, cursor: object, proc_mode: str):
        '''コンストラクタ

        Note:
            コンストラクタ内で疎通確認に失敗した場合は後続処理を行わない。

        Args:
            *args (list): コマンドライン引数1。
            **kwargs (dict): コマンドライン引数2。

        '''

        # ログファイルの有効性チェック
        check_status_of_log_file(PATH_TO_LOG_FILE)

        try:
            # インターネットへの疎通確認
            with urlopen('http://info.cern.ch/'):
                # 疎通成功の場合は何もしない
                pass
        except URLError as e:
            # 接続エラー時はエラーメッセージを出力し処理終了
            self.root = tkinter.Tk()
            self.root.withdraw()
            self.root.iconbitmap('../common/icon/python_icon.ico')
            messagebox.showerror('ERR_INTERNET_DISCONNECTED', \
                                    'There is no Internet connection\r\n\r\n' \
                                    'Try:\r\n' \
                                    '■Checking the network cables, modem, and router\r\n' \
                                    '■Reconnecting to Wi-Fi')

            # 通信処理時の例外制御
            self.__handling_url_exception(e)
            return

        # コネクションオブジェクト
        self.conn = conn
        # カーソルオブジェクト
        self.cursor = cursor
        # 処理モード
        self.proc_mode = proc_mode

        # 処理実行
        self.__main()

    def __main(self):

        # トレースバックの設定
        sqlite3.enable_callback_tracebacks(True)

        try:
            # hatenaへのクローリング処理を開始
            self.__crawl_hatena(self.conn, self.cursor)
        except sqlite3.Error as e:
            # ロールバック
            conn.rollback()
            logger.error(e)
            logger.exception(e)
            logger.log(20, 'ロールバック処理を完了しました。')
        finally:
            # 開放処理
            conn.close()
            logger.log(20, 'データベースの開放処理を完了しました。')

    def __crawl_hatena(self, conn: object, cursor: object):
        '''Hatenaに対してクローリング処理を行うメソッド

        Args:
            conn (object): DBとのコネクション
            cursor (object): カーソル。

        '''

        logger.log(10, 'クローリング処理を開始しました。')

        # テック情報TBLの挿入用対応データ
        INSERT_COLUMNS_INFO_TECH_TBL = ['URL', 'TITLE', 'PUBLISHED_DATE', 'BOOKMARKS', 'TAG', 'RESERVED_DEL_DATE']
        # 削除予定日
        RESERVED_DEL_DATE = (date.today() + timedelta(21)).strftime('%Y%m%d')

        # DBから検索ワードの取得
        SEARCH_WORDS = split_string(''.join(list(self.__select_params_by_primary_key(cursor, 'SEARCH_WORDS_FOR_TECH_ARTICLES'))), ',')
        for key_val in tqdm(SEARCH_WORDS):
            for query_page_val in range(1, 6):
                # パラメータ生成用辞書
                params = {'q' : key_val, 'page' : query_page_val, 'safe' : 'on', 'sort' : 'recent', 'users' : '1'}
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
                                # リストに削除予定日を追加
                                list_article_infos.append(RESERVED_DEL_DATE)
                                # リストを結合し辞書を生成
                                list_article_infos = dict(zip(INSERT_COLUMNS_INFO_TECH_TBL, list_article_infos))
                                # 登録処理
                                self.__insert_new_article_infos(cursor, list_article_infos)

                                # カウンタを初期化
                                count_duplication = 0
                            else:
                                # 重複している場合
                                count_duplication += 1
                    # コミット
                    conn.commit()

        logger.log(10, 'クローリング処理を完了しました。')

    def __scrape_info_of_hatena(self, html: str) -> list:
        '''HTMLソースに対してスクレイピング処理を行うメソッド

        Args:
            html (str): スクレイピング対象HTML。

        Returns:
            スクレイピングした全記事情報を含むリスト。

        '''

        logger.log(10, 'スクレイピング処理を開始しました。')

        # 取得したhtmlが空の場合
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
                # 記事情報をリストに格納
                list_infos.append(list_new_article_infos)

                if last_index_of_search != -1:
                    # htmlの更新
                    html = html[last_index_of_search:]
                else:
                    # ページ内の全情報を取得し終えた場合
                    break
            else:
                # 記事情報を取得できなかった場合
                break

        logger.log(10, 'スクレイピング処理を完了しました。')

        return list_infos

    def __get_infos_of_article(self, html: str) -> list:
        '''HTMLソースに対してスクレイピング処理を行い記事情報を取得するメソッド

        Args:
            html (str): スクレイピング対象HTML。

        Returns:
            スクレイピングした記事情報を含むリスト。
            URL部分を取得できなかった場合は空のリストを返す。

        '''

        # 記事情報格納用リスト
        list_article_infos = []
        # 探索開始インデックス
        start_search_index = html.find('centerarticle-entry-title')

        # URL部の取得
        start_index_of_url = html.find('"', html.find('<a', start_search_index))
        end_index_of_url = html.find('"', start_index_of_url+1)
        url = html[start_index_of_url+1:end_index_of_url]

        # 短縮されていないURLを取得した場合
        if url and not 'ift.tt' in url:
            # 取得したURLをリストに追加
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

            # 次のアンカータグがなくなるまでループ処理
            while start_index_of_anchor != -1:
                # タグの取得
                start_index_of_tag = html_of_tags.find('>', start_index_of_anchor+1)
                end_index_of_tag = html_of_tags.find('</a', start_index_of_tag+1)
                list_of_tags.append(html_of_tags[start_index_of_tag+1:end_index_of_tag])

                # インデックスの更新
                start_index_of_anchor = html_of_tags.find('<a', end_index_of_tag)
            else:
                # タグの取得処理完了後処理
                list_article_infos.append(','.join(list_of_tags))

            # 当該処理終了位置の取得と保存
            list_article_infos.append(html.find('class="bookmark-item', end_index_of_title))

        return list_article_infos

    def __get_html(self, url: str, params={}, headers=DEF_USER_AGENT) -> str:
        '''HTTP(s)通信を行いWebサイトからHTMLソースを取得するメソッド

        Args:
            url (str): 取得対象URL。
            params (dict): パラメータ生成用辞書。初期値は空の辞書。
            headers (dict): ヘッダ生成用辞書。初期値は定数"UserAgent定義"。

        Returns:
            対象URLにHTTP(s)通信を行い取得したHTMLソース

        '''

        try:
            # ページを開きリソースを取得
            with urlopen(Request(url='{}?{}'.format(url, urlencode(params)), headers=headers)) as source:
                # リソースから文字コードを取得
                charset = source.headers.get_content_charset(failobj='utf-8')
                # リソースをbytes型からString型にデコード
                html = source.read().decode(charset, 'ignore')
            return html
        except URLError as e:
            # 接続エラー
            self.__handling_url_exception(e)
            return ''

    def __edit_html(self, html: str) -> str:
        '''取得したHTMLをスクレイピング用に加工するメソッド

        Args:
            html (str): 未加工のHTMLソース。

        Returns:
            スクレイピング用に加工したHTMLソース。

        '''

        # 開始インデックス
        start_idx = html.find('<li', html.find('class="entrysearch-articles"'))
        # 終了インデックス
        end_idx = html.find('class="centerarticle-pager"', start_idx)

        return html[start_idx+1:end_idx]

    def __handling_url_exception(self, e: URLError):
        '''通信処理における例外を処理するメソッド

        Args:
            e (URLError): 通信処理において発生した例外情報

        '''

        if hasattr(e, 'reason'):
            logger.log(50, 'Failed to reach a server.')
            logger.error(e.reason)
            logger.exception(e)
        elif hasattr(e, 'code'):
            logger.log(50, 'The server couldn\'t fulfill the request.')
            logger.error(e.code)
            logger.exception(e)

    def __select_params_by_primary_key(self, cursor: object, primary_key: str) -> tuple:
        '''主キーを用いてパラメータTBLから値を取得するクエリ

        Note:
            返り値はtuple型。

        Args:
            cursor (object): カーソル。
            primary_key (str): 主キー。

        Returns:
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

        logger.log(10, '検索を完了しました。')

        return cursor.fetchone()

    def __select_by_primary_key(self, cursor: object, primary_key: str) -> tuple:
        '''主キーを使用してDBから記事情報を取得するクエリ

        Note:
            返り値はtuple型。

        Args:
            cursor (object): カーソル。
            primary_key (str): 主キー。

        Returns:
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

        logger.log(10, '検索を完了しました。')

        return cursor.fetchone()

    def __insert_new_article_infos(self, cursor: object, article_infos: dict):
        '''取得した記事情報をDBへ挿入するクエリ

        Args:
            cursor (object): カーソル。
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

        logger.log(10, '新規記事の登録処理を完了しました。')

def check_status_of_log_file(path_to_log: str):
    '''ログファイルの有効性を判定する関数

    Note:
        ログファイルが存在しない場合には生成処理を行う。

    Args:
        path_to_log (str): ログファイルへのパス。

    '''

    if not os.path.exists(PATH_TO_LOG_FILE):
        # logファイルの作成
        with open(PATH_TO_LOG_FILE):
            pass

def split_string(target: str, split_words: str) -> list:
    '''組み込みsplit関数の拡張関数

    Note:
        正規表現を使用しないため高速処理が可能。

    Args:
        target (str): 対象文字列。
        splitlist (str): 区切り文字。

    Returns:
        区切り文字によって分割された文字列のリスト。

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
    # GUIを呼び出す
    SearchArticlesOfTech = SearchArticlesOfTech()
