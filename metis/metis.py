# -*- coding: utf-8 -*-

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
import html.parser as htmlparser
import webbrowser
import pyperclip
from datetime import date, datetime, timedelta
import json
import os.path
import sqlite3
from logging import getLogger, FileHandler, StreamHandler, Formatter
import tkinter
from tkinter import messagebox, Menu
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

class SearchArticlesOfTech(tkinter.Tk):
    '''GUIの出力処理を定義するクラス'''

    def __init__(self, *args, **kwargs):
        '''コンストラクタ

        Args:
            *args (tuple): タプルの可変長引数。
            **kwargs (dict): 辞書の可変長引数。

        '''

        # ログファイルの有効性チェック
        check_status_of_log_file(PATH_TO_LOG_FILE)

        self.root = tkinter.Tk()
        # closeボタンの無効化
        self.root.protocol('WM_DELETE_WINDOW', self.__disable_close_button)
        # エスケープキーで処理終了するように設定
        self.root.bind('<Escape>', lambda x: self.__quit())

        # ファイルメニューの生成
        self.__create_file_menu()

        notebook = ttk.Notebook(self.root, height=700, width=999)
        # top画面用のフレーム
        frameUpdateArticles = tkinter.Frame(notebook, bd=2, relief='groove')
        # log検索画面用のフレーム
        frameShowLog = tkinter.Frame(notebook, bd=2, relief='groove')

        # top画面用のタブ
        notebook.add(frameUpdateArticles, text='Top')
        # log検索画面用のタブ
        notebook.add(frameShowLog, text='Log')

        # TOP画面の作成
        self.__create_top_gui(frameUpdateArticles)
        # ログ出力画面の作成
        self.__create_log_gui(frameShowLog)

        notebook.grid(row=0, column=0, sticky=N+S+W+E)

        # ウィンドウの設定
        self.root.resizable(0, 0)
        self.root.iconbitmap('../common/icon/python_icon.ico')
        self.root.title('Metis')
        self.root.geometry('1000x680+400+150')

        self.root.mainloop()

    def __create_top_gui(self, parent: tkinter.Frame):
        '''TOP画面の出力を定義するメソッド

        Args:
            parent (tkinter.Frame): 画面の親フレーム。

        '''

        tkinter.Label(parent).pack()
        # 最大表示件数入力フォームの設定
        lblSearchTerms = tkinter.Label(parent, font=('Consolas', 10),text='Enter search terms')
        lblSearchTerms.pack()
        self.btnSearchTerms = ttk.Entry(parent, justify='center', width=40)
        # リターンキー押下で検索を開始するように設定
        self.btnSearchTerms.bind('<Return>', lambda x: self.__refresh_tree_view())
        self.btnSearchTerms.pack()

        # 検索ボタン
        search_button = ttk.Button(parent, text='Search', width=10, command=self.__refresh_tree_view)
        search_button.place(relx=0.63, rely=0.058)

        # ツリービューの作成
        self.tree = ttk.Treeview(parent, height=15)
        self.scroll = tkinter.Scrollbar(parent, orient=tkinter.VERTICAL, command=self.tree.yview)
        self.scroll.place(relx=0.962, y=95, height=474.45)
        self.tree['columns'] = (1, 2, 3, 4)
        self.tree['show'] = 'headings'
        self.tree.column(1, width=70)
        self.tree.column(2, width=700)
        self.tree.column(3, width=100)
        self.tree.column(4)
        self.tree.heading(1, text='No.')
        self.tree.heading(2, text='Title')
        self.tree.heading(3, text='Bookmarks')
        self.tree.heading(4)
        self.tree.configure(style='my.Treeview', displaycolumns=(1,2,3), yscroll=self.scroll.set)
        # ダブルクリックでページを開くように設定
        self.tree.bind('<Double-1>', self.__open_by_double_click)
        # 右クリックでURLをコピーするように設定
        self.tree.bind('<ButtonRelease-3>', self.__copy_by_right_click)
        self.tree.pack(fill='x', padx=20, pady=30)

        # ツリービューのレイアウト設定
        style = ttk.Style(parent)
        style.configure('my.Treeview', rowheight=30)
        style.configure('Treeview', font=('Consolas', 10))
        style.configure('Treeview.Heading', font=('Consolas', 10, 'bold'))

        # ブラウザで開くボタン
        open_button = ttk.Button(parent, text='Open', width=10, command=self.__open)
        open_button.place(width=150, relx=0.12, rely=0.86)
        # 初期化ボタン
        flush_button = ttk.Button(parent, text='Flush', width=10, command=self.__flush)
        flush_button.place(width=150, relx=0.42, rely=0.86)
        # 終了ボタン
        quit_button = ttk.Button(parent, text='Quit', width=10, command=self.__quit)
        quit_button.place(width=150, relx=0.72, rely=0.86)

    def __refresh_tree_view(self):
        '''取得した記事情報からツリービューを生成するメソッド'''

        # 検索ワードの取得
        search_word = self.btnSearchTerms.get()
        if search_word:
            # ツリービューの初期化
            self.tree.delete(*self.tree.get_children())
            # DB接続を行う
            conn, cursor = connect_to_database()

            try:
                article_infos = self.__select_infos_by_search_word(cursor, '%' + search_word + '%')
                if article_infos:
                    # TreeViewの生成
                    for i, infos in enumerate(article_infos):
                        value = (str(i+1), infos[1], infos[3], infos[0])
                        self.tree.insert('', 'end', tags=i, values=value)

                        if i & 1:
                            # 偶数行の背景色を変更
                            self.tree.tag_configure(i, background='#CCFFFF')
                    self.tree.pack(fill='x', padx=20, pady=30)
                else:
                    messagebox.showinfo('NO_RESULTS_FOUND',
                                            'Your search - ' \
                                            + search_word \
                                            + ' - did not match any documents.')
            except sqlite3.Error as e:
                logger.error(e)
                logger.exception(e)
            finally:
                # 開放処理
                conn.close()
                logger.log(20, 'データベースの開放処理を完了しました。')
        else:
            messagebox.showerror('ERR_EMPTY_REQUESTED', \
                                    'This field must not be empty.')

    def __create_log_gui(self, parent: tkinter.Frame):
        '''Log検索画面の出力を定義するメソッド

        Args:
            parent (tkinter.Frame): 画面の親フレーム

        '''

        # 入力フォームの設定
        lblDate = tkinter.Label(parent, font=('Consolas', 10), text='Enter the date')
        lblDate.pack()
        self.inputDate = ttk.Entry(parent, font=('Consolas', 10), justify='center', width=20)
        self.inputDate.insert(tkinter.END, datetime.today().strftime('%Y/%m/%d'))
        self.inputDate.bind('<Leave>', lambda x: self.__read_log())
        self.inputDate.pack()

        # 出力用フォームの設定
        frameTextLog = tkinter.Frame(parent, pady=10, bd=0)
        frameTextLog.pack()
        self.OutputTextLog = tkst.ScrolledText(frameTextLog, font=('Consolas', 10), height=35, width=130)
        self.OutputTextLog.pack()

        # readボタン
        read_button = ttk.Button(parent, text='Read', width=10, command=self.__read_log)
        read_button.place(relx=0.25, rely=0.88)
        # 一覧ボタン
        list_button = ttk.Button(parent, text='List', width=10, command=self.__read_log_list)
        list_button.place(relx=0.45, rely=0.88)
        # 終了ボタン
        quit_button = ttk.Button(parent, text='Quit', width=10, command=self.__quit)
        quit_button.place(relx=0.65, rely=0.88)

    def __create_file_menu(self):
        '''メニューバーの出力を定義するメソッド'''

        menubar = Menu(self.root)

        file_menu = Menu(menubar, tearoff=0)
        # パラメータ設定画面
        file_menu.add_command(label='Parameters')
        file_menu.add_separator()
        # 終了コマンド
        file_menu.add_command(label='Exit', command=quit)
        menubar.add_cascade(label='File', menu=file_menu)

        # 編集メニュー
        edit_menu = Menu(menubar, tearoff=0)
        edit_menu.add_command(label='Copy Path', command=self.__copy_url)
        edit_menu.add_command(label='Copy Title', command=self.__copy_title)
        edit_menu.add_command(label='Copy Informations', command=self.__copy_informations)
        menubar.add_cascade(label='Edit', menu=edit_menu)

        # 更新メニュー
        update_menu = Menu(menubar, tearoff=0)
        start_crawling = Menu(menubar, tearoff=0)
        update_bookmarks = Menu(menubar, tearoff=0)
        update_menu.add_cascade(label='Start Crawling', menu=start_crawling)
        start_crawling.add_command(label='Hatena', command=self.__execute_crawling_hatena)
        update_menu.add_cascade(label='Update Bookmarks', menu=update_bookmarks)
        update_bookmarks.add_command(label='Hatena')
        menubar.add_cascade(label='Update', menu=update_menu)

        # helpメニュー
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label='Document')
        help_menu.add_command(label='About Software', command=self.__open_readme)
        help_menu.add_separator()
        help_menu.add_command(label='Licence', command=self.__open_licence)

        menubar.add_cascade(label='Help', menu=help_menu)

        self.root.config(menu=menubar)

    def __open(self):
        '''openボタン押下時の処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())
        # valuesキーが要素を持っている場合
        if item_dict['values']:
            # URLの取得
            url = item_dict['values'][3]
            # ブラウザで開く
            webbrowser.open_new_tab(url)

    def __flush(self):
        '''flushボタン押下時の処理を定義'''

        # ツリービューの初期化
        self.tree.delete(*self.tree.get_children())

    def __copy_url(self):
        '''URLをクリップボードに追加する処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())
        # valuesキーが要素を持っている場合
        if item_dict['values']:
            # URLの取得
            url = item_dict['values'][3]
            # クリップボードへ追加
            pyperclip.copy(url)

    def __copy_title(self):
        '''タイトルをクリップボードに追加する処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())
        # valuesキーが要素を持っている場合
        if item_dict['values']:
            # タイトルの取得
            title = item_dict['values'][1]
            # クリップボードへ追加
            pyperclip.copy(title)

    def __copy_informations(self):
        '''タイトル、URL、ブックマーク数をコピーする処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())
        # valuesキーが要素を持っている場合
        if item_dict['values']:
            url = item_dict['values'][3]
            # タイトルの取得
            title = item_dict['values'][1]
            # ブックマーク数の取得
            bookmarks = str(item_dict['values'][2])

            # クリップボードへ追加
            pyperclip.copy(' '.join([url, title, bookmarks]))

    def __open_by_double_click(self, event):
        '''左ダブルクリック時に発生する処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())
        # valuesキーが要素を持っている場合
        if item_dict['values']:
            # URLの取得
            url = item_dict['values'][3]
            # ブラウザで開く
            webbrowser.open_new_tab(url)

    def __copy_by_right_click(self, event):
        '''右クリック時に発生する処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())
        # valuesキーが要素を持っている場合
        if item_dict['values']:
            # URLの取得
            url = item_dict['values'][3]
            # クリップボードへ追加
            pyperclip.copy(url)

    def __open_licence(self):
        '''ライセンスを記述したページを開く'''

        webbrowser.open_new_tab('https://github.com/myConsciousness/search-tech-articles/blob/master/LICENSE')

    def __open_readme(self):
        '''readmeを記述したページを開く'''

        webbrowser.open_new_tab('https://github.com/myConsciousness/search-tech-articles/blob/master/README.rst')

    def __execute_crawling_hatena(self):
        '''hatenaへのクローリング処理を実行する'''

        # クローリング処理を実行
        CrawlingAndScrapingArticlesOfTech()

    def __read_log(self):
        '''readボタン押下時の処理を定義'''

        # 出力用テキストフォームが空ではない場合
        if self.OutputTextLog.get('1.0',tkinter.END):
            # テキストフォームの初期化
            self.OutputTextLog.delete('1.0', tkinter.END)

        input_date = self.inputDate.get()
        if '.log' in input_date:
            # ファイル名と拡張子を分割
            root, ext = os.path.splitext(input_date)
            # 入力された日付を処理用に加工
            date = ''.join(split_string(root, '-/., '))
            # 参照するログのパス
            path_name = '../log/' + date + '.log'
        else:
            # 入力された日付を処理用に加工
            date = ''.join(split_string(input_date, '-/., '))
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
            self.OutputTextLog.insert(tkinter.END, 'Failed to open log file\r\nNo such file or directory')

    def __read_log_list(self):
        '''listボタン押下時の処理を定義'''

        # 出力用テキストフォームが空ではない場合
        if self.OutputTextLog.get('1.0',tkinter.END):
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

    def __quit(self):
        '''quitボタン押下時の処理を定義'''

        # 処理を終了
        self.root.destroy()

    def __disable_close_button(self):
        '''windowのcloseボタンを無効化する'''

        messagebox.showerror('ERR_BUTTON_LIMITED', \
                                'Use Quit button or Esc key to close the window.')

    def __select_infos_by_search_word(self, cursor: sqlite3.Cursor, search_word: str) -> tuple:
        '''検索ワードから記事情報を取得するクエリ

        Note:
            返り値はtuple型。

        Args:
            cursor (sqlite3.Cursor): カーソル。
            search_word (str): 検索ワード。

        Returns:
            検索結果。

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
                            TAG
                        LIKE
                            ?
                        ''',(search_word,))
        return cursor.fetchall()

class CrawlingAndScrapingArticlesOfTech:
    '''クローリングとスクレイピングの処理を定義するクラス'''

    # UserAgent定義
    DEF_USER_AGENT = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0'}

    def __init__(self, *args, **kwargs):
        '''コンストラクタ

        Note:
            コンストラクタ内で疎通確認に失敗した場合は後続処理を行わない。

        Args:
            *args (tuple): タプルの可変長引数。
            **kwargs (dict): 辞書の可変長引数。

        '''

        # ログファイルの有効性チェック
        check_status_of_log_file(PATH_TO_LOG_FILE)

        try:
            # 疎通確認
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

        # 処理実行
        self.__main()

    def __main(self):

        # DB接続を行う
        conn, cursor = connect_to_database()

        try:
            # hatenaへのクローリング処理を開始
            self.__crawl_hatena(conn, cursor)
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

    def __crawl_hatena(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        '''Hatenaに対してクローリング処理を行うメソッド

        Args:
            conn (sqlite3.Connection): DBとのコネクション。
            cursor (sqlite3.Cursor): カーソル。

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

    def __handling_url_exception(self, e):
        '''通信処理における例外を処理するメソッド

        Args:
            e (urllib.error.URLError): 通信処理において発生した例外情報

        '''

        if hasattr(e, 'reason'):
            logger.log(50, 'Failed to reach a server.')
            logger.error(e.reason)
            logger.exception(e)
        elif hasattr(e, 'code'):
            logger.log(50, 'The server couldn\'t fulfill the request.')
            logger.error(e.code)
            logger.exception(e)

    def __select_params_by_primary_key(self, cursor: sqlite3.Cursor, primary_key: str) -> tuple:
        '''主キーを用いてパラメータTBLから値を取得するクエリ

        Note:
            返り値はtuple型。

        Args:
            cursor (sqlite3.Cursor): カーソル。
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

    def __select_by_primary_key(self, cursor: sqlite3.Cursor, primary_key: str) -> tuple:
        '''主キーを使用してDBから記事情報を取得するクエリ

        Note:
            返り値はtuple型。

        Args:
            cursor (sqlite3.Cursor): カーソル。
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

    def __insert_new_article_infos(self, cursor: sqlite3.Cursor, article_infos: dict):
        '''取得した記事情報をDBへ挿入するクエリ

        Args:
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

def connect_to_database():
    '''データベースへ接続する関数

    Note:
        コネクションの開放処理は別途行うこと。

    Returns:
        コネクション、カーソルオブジェクトを格納したリスト。

    '''

    # トレースバックの設定
    sqlite3.enable_callback_tracebacks(True)
    # データベースへの接続
    conn = sqlite3.connect('../common/db/USER01.db')
    # カーソル
    cursor = conn.cursor()

    return conn, cursor

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
    SearchArticlesOfTech()
