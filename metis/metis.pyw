# -*- coding: utf-8 -*-

import webbrowser
import pyperclip
from datetime import datetime
import os.path
import sqlite3
import tkinter
from tkinter import messagebox, Menu
import tkinter.ttk as ttk
from tkinter import N, S, W, E
import tkinter.scrolledtext as tkst
from log import LogLevel, Log
from crawler import CrawlingHatena

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

class Application(tkinter.Tk):
    '''GUIの出力処理を定義するクラス'''

    def __init__(self, *args, **kwargs):
        '''コンストラクタ

        Args
        ----
        *args (tuple): タプルの可変長引数。
        **kwargs (dict): 辞書の可変長引数。

        '''

        # ログ出力のためインスタンス生成
        self.log = Log()
        # クラス名
        self.CLASS_NAME = self.__class__.__name__

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log.MSG_PROCESS_STARTED)

        self.root = tkinter.Tk()
        self.root.protocol('WM_DELETE_WINDOW', self.__disable_close_button)
        self.root.bind('<Escape>', lambda x: self.__quit())

        # メニューバーの生成
        self.__create_menubar()

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

        Args
        ----
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

        open_button = ttk.Button(parent, text='Open', width=10, command=self.__open)
        open_button.place(width=150, relx=0.12, rely=0.86)

        flush_button = ttk.Button(parent, text='Flush', width=10, command=self.__flush)
        flush_button.place(width=150, relx=0.42, rely=0.86)

        quit_button = ttk.Button(parent, text='Quit', width=10, command=self.__quit)
        quit_button.place(width=150, relx=0.72, rely=0.86)

    def __refresh_tree_view(self):
        '''取得した記事情報からツリービューを生成するメソッド'''

        search_word = self.btnSearchTerms.get()
        if search_word:
            # ツリービューの初期化
            self.tree.delete(*self.tree.get_children())

            try:
                conn, cursor = connect_to_database()

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
                self.log.normal(LogLevel.ERROR.value, self.CLASS_NAME, \
                                        self.log.location(), self.log.MSG_ERROR)
                self.log.error(e)
            finally:
                conn.close()
                self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                        self.log.location(), self.log.MSG_CLOSE_COMPLETED)
        else:
            messagebox.showerror('ERR_EMPTY_REQUESTED', \
                                    'This field must not be empty.')

    def __create_log_gui(self, parent: tkinter.Frame):
        '''Log検索画面の出力を定義するメソッド

        Args
        ----
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

        read_button = ttk.Button(parent, text='Read', width=10, command=self.__read_log)
        read_button.place(relx=0.25, rely=0.88)

        list_button = ttk.Button(parent, text='List', width=10, command=self.__read_log_list)
        list_button.place(relx=0.45, rely=0.88)

        quit_button = ttk.Button(parent, text='Quit', width=10, command=self.__quit)
        quit_button.place(relx=0.65, rely=0.88)

    def __create_menubar(self):
        '''メニューバーの出力を定義するメソッド'''

        menubar = Menu(self.root)

        # ファイルメニュー
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label='Parameters')
        file_menu.add_separator()

        file_menu.add_command(label='Exit', command=self.__quit)
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

        if item_dict['values']:
            url = item_dict['values'][3]

            webbrowser.open_new_tab(url)

    def __flush(self):
        '''flushボタン押下時の処理を定義'''

        # ツリービューの初期化
        self.tree.delete(*self.tree.get_children())

    def __copy_url(self):
        '''URLをクリップボードに追加する処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())

        if item_dict['values']:
            url = item_dict['values'][3]

            pyperclip.copy(url)

    def __copy_title(self):
        '''タイトルをクリップボードに追加する処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())

        if item_dict['values']:
            title = item_dict['values'][1]

            pyperclip.copy(title)

    def __copy_informations(self):
        '''タイトル、URL、ブックマーク数をコピーする処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())

        if item_dict['values']:
            url = item_dict['values'][3]
            title = item_dict['values'][1]
            bookmarks = str(item_dict['values'][2])

            pyperclip.copy(' '.join([url, title, bookmarks]))

    def __open_by_double_click(self, event):
        '''左ダブルクリック時に発生する処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())

        if item_dict['values']:
            url = item_dict['values'][3]

            webbrowser.open_new_tab(url)

    def __copy_by_right_click(self, event):
        '''右クリック時に発生する処理を定義'''

        # フォーカス部分の要素を辞書として取得
        item_dict = self.tree.item(self.tree.focus())

        if item_dict['values']:
            url = item_dict['values'][3]

            pyperclip.copy(url)

    def __open_licence(self):
        '''ライセンスを記述したページを開く'''

        webbrowser.open_new_tab('https://github.com/myConsciousness/search-tech-articles/blob/master/LICENSE')

    def __open_readme(self):
        '''readmeを記述したページを開く'''

        webbrowser.open_new_tab('https://github.com/myConsciousness/search-tech-articles/blob/master/README.rst')

    def __execute_crawling_hatena(self):
        '''hatenaへのクローリング処理を実行する'''

        if messagebox.askyesno('CONFIRMATION', 'Are you sure you want to run?'):
            CrawlingHatena()

    def __read_log(self):
        '''readボタン押下時の処理を定義'''

        if self.OutputTextLog.get('1.0',tkinter.END):
            # テキストフォームの初期化
            self.OutputTextLog.delete('1.0', tkinter.END)

        input_date = self.inputDate.get()
        if '.log' in input_date:
            # ファイル名と拡張子を分割
            root, ext = os.path.splitext(input_date)
            date = ''.join(split_string(root, '-/., '))
            path_name = '../log/' + date + '.log'
        else:
            date = ''.join(split_string(input_date, '-/., '))
            path_name = '../log/' + date + '.log'

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

        self.log.normal(LogLevel.INFO.value, self.CLASS_NAME, \
                                self.log.location(), self.log.MSG_PROCESS_COMPLETED)

        # 処理終了
        self.root.destroy()

    def __disable_close_button(self):
        '''windowのcloseボタンを無効化する'''

        messagebox.showerror('ERR_BUTTON_LIMITED', \
                                'Use Quit button or Esc key to close the window.')

    def __select_infos_by_search_word(self, cursor: sqlite3.Cursor, search_word: str) -> tuple:
        '''検索ワードから記事情報を取得するクエリ

        Note
        ----
        返り値はtuple型。

        Args
        ----
        cursor (sqlite3.Cursor): カーソル。
        search_word (str): 検索ワード。

        Returns
        -------
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

def split_string(target: str, split_words: str) -> list:
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
    >>> split_string('test//sp"rit%st$ring', '/"%$')
    >>> ['test', 'sp', 'rit', 'st', 'ring']
    >>>
    >>> ''.join(split_string('test//sp"rit%st$ring', '/"%$'))
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
    Application()
