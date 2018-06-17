# -*- coding: utf-8 -*-

'''

Tkinter is a Python binding to the Tk GUI toolkit. It is the standard Python interface to the Tk GUI toolkit,
and is de facto standard GUI of Python.
Tkinter is included with the standard Microsoft Windows and Mac OS X install of Python.

As with most other modern Tk bindings, Tkinter is implemented as a Python wrapper
around a complete Tcl interpreter embedded in the Python interpreter.
Tkinter calls are translated into Tcl commands which are fed to this embedded interpreter,
thus making it possible to mix Python and Tcl in a single application.

Python 2.7 and Python 3.1 incorporate the "themed Tk" ("ttk") functionality of Tk 8.5.
This allows Tk widgets to be easily themed to look like the native desktop environment in which the application is running,
thereby addressing a long-standing criticism of Tk (and hence of Tkinter).

Tkinter is free software released under a Python license.

:copyright: (c) 2018 by Kato Shinya.
:license: MIT, see LICENSE for more details.
'''

import webbrowser
import pyperclip
from datetime import datetime
import os.path
import sqlite3
import time
import tkinter as tk
from tkinter import *
from tkinter import messagebox, filedialog
import tkinter.ttk as ttk
from log import LogLevel, Log
import subprocess
from functools import partial
from common import *
from sql import ArticleInfoHatenaDao
from sql import ManageSerialDao

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

class MetisCustomText(Text):
    '''Tkinterテキストウィジェットの拡張クラス。'''

    def __init__(self, master, **kwargs):
        '''コンストラクタ。'''

        super().__init__(master, **kwargs)

        # onchangeイベントを有効化する
        self.tk.eval('''
                    proc widget_proxy {widget widget_command args} {
                        set result [uplevel [linsert $args 0 $widget_command]]
                        if {([lrange $args 0 1] == {xview moveto}) ||
                            ([lrange $args 0 1] == {xview scroll}) ||
                            ([lrange $args 0 1] == {yview moveto}) ||
                            ([lrange $args 0 1] == {yview scroll})} {
                            event generate  $widget <<Scroll>> -when tail
                        }
                        if {([lindex $args 0] in {insert replace delete})} {
                            event generate  $widget <<Change>> -when tail
                        }
                        return $result
                    }
                    ''')
        self.tk.eval('''
                        rename {widget} _{widget}
                        interp alias {{}} ::{widget} {{}} widget_proxy {widget} _{widget}
                    '''.format(widget=str(self)))

class MetisSearchForm(ttk.Frame):
    '''Metisにおけるテキストの検索フォームを定義するクラス。'''

    def __init__(self, master, text_form, *args, **kwargs):
        '''コンストラクタ。'''

        # 親クラスのコンストラクタを実行
        super().__init__(master, *args, **kwargs)

        self.target_text = text_form
        self.last_text = ''
        self.all_pos = []
        self.next_pos_index = 0

        # 検索フォームを生成
        self.__create_search_form()
        # 検索フォームの入力欄にフォーカスを設定する
        self.target_text.focus()

    def __create_search_form(self):
        '''検索フォームを生成するメソッド。'''

        # 検索フォームのフレーム
        frame_search_form = LabelFrame(self, bd=2, relief=RIDGE, labelanchor=N, text='Enter search word')
        frame_search_form.pack(fill=BOTH, pady=5)

        # 検索フォームの入力欄と紐付ける
        self.text_var = StringVar()
        self.search_form = ttk.Entry(frame_search_form, textvariable=self.text_var, width=70)
        self.search_form.pack(fill=BOTH)

        # 検索ボタン
        search_button = ttk.Button(frame_search_form, text='Search', width=70, command=self.__search)
        search_button.pack(fill=BOTH)

    def __search(self, event):
        '''対象ウィジェットに対して検索処理を行うメソッド。'''

        # 選択されているタグを解除
        self.target_text.tag_remove('sel', '1.0', END)
        # 検索フォームの値を取得
        search_word = self.text_var.get()

        if not search_word:
            # 取得した値が空の場合は処理しない
            pass
        elif search_word != self.last_text:
            # 前回入力された値と異なる場合
            self.__start_search(search_word)
        else:
            # 前回入力された値と同一の場合
            self.__continue_search(search_word)

        # 入力された値を保持する
        self.last_text = search_word

    def __start_search(self, search_word: str):
        '''先頭から検索処理を行うメソッド。

        :param str search_word: 検索ワード。
        '''

        self.next_pos_index = 0
        self.all_pos = []

        start_index = '1.0'
        while True:
            pos = self.target_text.search(search_word, start_index, stopindex=END)

            if not pos:
                # 全文を検索し終えた場合
                break

            self.all_pos.append(pos)
            # 最後から+1文字を起点に再検索を行う
            start_index = '{} + 1c'.format(pos)

        # 後続処理を開始する
        self.__continue_search(search_word)

    def __continue_search(self, search_word: str):
        '''検索途中の個所から検索を行うメソッド。

        :param str search_word: 検索ワード。
        '''

        try:
            # 一致部分を取得する
            pos = self.all_pos[self.next_pos_index]
        except IndexError:
            # all_posが空でなくIndexErrorの場合はすべての一致部分を確認済みの想定
            if self.all_pos:
                self.next_pos_index = 0
                self.__continue_search(search_word)
        else:
            # 一致部分を取得した場合
            start = pos
            end = '{} + {}c'.format(pos, len(search_word))

            # 一致部分を範囲選択する
            self.target_text.tag_add('sel', start, end)

            # カーソルを合わせ一致箇所までスクロールさせる
            self.target_text.mark_set('insert', start)
            self.target_text.see('insert')

            self.target_text.focus()

            # 後続処理のためインデックスを更新
            self.next_pos_index += 1

class MetisBase:
    '''Metisにおける最基底クラス。'''

    def __init__(self):
        '''コンストラクタ。'''

        self.master = Tk()

        # ログ出力のためインスタンス生成
        self.log = Log()

        # 設定ファイルの読み込み
        self.config = read_config_file()

        # ドキュメントへのURL
        self.URL_DOCS = 'https://myconsciousness.github.io/metis/index.html'
        # ライセンスを定義したテキストへのURL
        self.URL_LICENSE = 'https://github.com/myConsciousness/metis/blob/master/LICENSE'
        # readmeを定義したmdファイルへのURL
        self.URL_README = 'https://github.com/myConsciousness/metis/blob/master/README.md'

        # MANAGE_SERIAL.TBLのDAOクラス
        self.manage_serial_dao = ManageSerialDao()
        # ARTICLE_INFO_HATENA.TBLのDAOクラス
        self.article_info_hatena_dao = ArticleInfoHatenaDao()

    def set_window_basic_config(self, master, title='Metis', icon='../common/icon/python_icon.ico', expand=True, width=1200, height=710):
        '''ウィンドウにおける基本情報を設定するメソッド。

        :param tkinter.Tk master: 画面のフレーム。
        :param str title: 画面タイトル。
        :param str icon: 画面左上に表示するアイコンへのパス。
        :param bool expand: 画面の拡張 / 縮小可否。
        :param int width: 初期表示時の画面の幅。
        :param int height: 初期表示時の画面の高さ。
        '''

        if expand:
            # 拡張 / 縮小できるように設定
            master.resizable(1, 1)
        else:
            # 拡張 / 縮小できないように設定
            master.resizable(0, 0)

        # タイトルの設定
        master.title(title)
        # アイコンの設定
        master.iconbitmap(icon)
        # 初期表示位置をディスプレイの中央に設定（環境非依存）
        self.__center(master, width=width, height=height)

    def __center(self, master, width: int, height: int):
        '''初期表示時に画面を常に中央に表示するように設定するメソッド。

        :param tkinter.Tk master: 画面のフレーム。
        :param int width: 初期表示時の画面の幅。
        :param int height: 初期表示時の画面の高さ。
        '''

        master.update_idletasks()

        # 画面を表示する幅を求める
        frm_width = master.winfo_rootx() - master.winfo_x()
        win_width = width + 2 * frm_width

        # 画面を表示する高さを求める
        titlebar_height = master.winfo_rooty() - master.winfo_y()
        win_height = height + titlebar_height + frm_width

        # x軸を求める
        x = master.winfo_screenwidth() // 2 - win_width // 2
        # y軸を求める
        y = master.winfo_screenheight() // 2 - win_height // 2

        master.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        master.deiconify()

class MetisCommandBase(MetisBase):
    '''Metisにおける基本コマンド処理を定義する基底クラス。'''

    def __init__(self):
        '''コンストラクタ。'''

        # 基底クラスのコンストラクタを実行
        super().__init__()

        # コマンド基底クラス名
        self.CLASS_NAME_COMMAND_BASE = 'MetisCommandBase'

    def undo(self, widget):
        '''取り消す機能の実装メソッド。

        :param inferred-type widget: 機能付加対象ウィジェット。
        '''

        try:
            widget.edit_undo()
        except TclError:
            # 取り消す対象がない場合
            pass

    def redo(self, widget):
        '''やり直すメソッドの実装メソッド。

        :param inferred-type widget: 機能付加対象ウィジェット。
        '''

        try:
            widget.edit_redo()
        except TclError:
            # やり直す対象がない場合
            pass

    def copy(self, menu, label, widget):
        '''コピー機能の実装メソッド。

        :param inferred-type widget: 機能付加対象ウィジェット。
        '''

        menu.entryconfigure(label, command=lambda: widget.event_generate('<<Copy>>'))

    def cut(self, menu, label, widget):
        '''カット機能の実装メソッド。

        :param inferred-type widget: 機能付加対象ウィジェット。
        '''

        menu.entryconfigure(label, command=lambda: widget.event_generate('<<Cut>>'))

    def paste(self, menu, label, widget):
        '''貼り付け機能の実装メソッド。

        :param inferred-type widget: 機能付加対象ウィジェット。
        '''

        menu.entryconfigure(label, command=lambda: widget.event_generate('<<Paste>>'))

    def open(self, widget):
        '''ファイルダイアログからファイル名を取得するメソッド。

        :param inferred-type widget: 機能付加対象ウィジェット。
        '''

        fTyp = [('Metis log file', '*.mlog')]
        path_name = filedialog.askopenfilename(filetypes=fTyp, initialdir='./')

        if os.path.exists(path_name):
            with open(path_name, 'r') as f:
                text = f.read()

            widget.delete('1.0', END)
            widget.insert('insert', text)
        else:
            # ログファイルが存在しなかった場合
            messagebox.showerror('ERR_NO_FILE_FOUND',
                                    'Failed to open log file.\r\n' \
                                    'No such file or directory.')

    def open_new_tab(self, url):
        '''引数で渡されたURLを新しいタブで開く。

        :param str url: 対象URL。
        '''

        webbrowser.open_new_tab(url)

    def quit(self, master):
        '''quitボタン押下時の処理を定義。

        :param tkinter.Tk master: 画面のフレーム。
        '''

        self.log.normal(LogLevel.INFO.value, 'LINF0008', self.CLASS_NAME_COMMAND_BASE, self.log.location())

        # 処理終了
        master.destroy()

    def disable_close_button(self):
        '''windowのcloseボタンを無効化する'''

        messagebox.showerror('ERR_BUTTON_LIMITED', \
                                'Use Quit button or Esc key to close the window.')

    def open_popup(self, event, popup):
        '''ポップアップメニューを表示するメソッド。

        :param tkinter.Menu popup: メニューオブジェクト。
        '''

        popup.post(event.x_root, event.y_root)

    def create_cancel_menu(self, popup, widget):
        '''取り消し系統のメニューを作成するメソッド。

        :param tkinter.Menu popup: メニューオブジェクト。
        :param inferred-type widget: 機能付加対象ウィジェット。
        '''

        popup.add_command(label='Undo', command=partial(self.undo, widget))
        popup.add_command(label='Redo', command=partial(self.redo, widget))

    def create_basic_menu(self, popup, widget):
        '''基本メニューを作成するメソッド。

        :param tkinter.Menu popup: メニューオブジェクト。
        :param inferred-type widget: 機能付加対象ウィジェット。
        '''

        popup.add_command(label='Cut', command=partial(self.cut, popup, 'Cut', widget))
        popup.add_command(label='Copy', command=partial(self.copy, popup, 'Copy', widget))
        popup.add_command(label='Paste', command=partial(self.paste, popup, 'Paste', widget))

    def create_xy_scrollbar(self, master, widget):
        '''XY軸のスクロールバーを生成するメソッド。

        :param tkinter.Tk master: 画面のフレーム。
        :param inferred-type widget: 機能付加対象ウィジェット。
        '''

        xsb = Scrollbar(master, orient=HORIZONTAL, command=widget.xview)
        ysb = Scrollbar(master, orient=VERTICAL, command=widget.yview)

        widget.configure(xscrollcommand=xsb.set)
        widget.configure(yscrollcommand=ysb.set)

        xsb.pack(side=BOTTOM, fill=X)
        ysb.pack(side=RIGHT, fill=Y)

class Command(MetisCommandBase):
    '''アプリケーションのコマンド処理を定義するクラス。'''

    def __init__(self):
        '''コンストラクタ。'''

        # クラス名
        self.CLASS_NAME_COMMAND = 'Command'

        # 最基底クラスのコンストラクタを実行
        super().__init__()

        # 現在のソート状態
        self.current_sort_state = None
        # ソート用検索ワード
        self.search_word_for_sort = None

        # 昇順オーダ
        self.SORT_ASC = 'ASC'
        # 降順オーダ
        self.SORT_DESC = 'DESC'

        # ログファイルを格納したファイルへのパス
        self.PATH_DIR_LOG = self.config['path']['dir_log']
        # クローラモジュールを格納したファイルへのパス
        self.PATH_CRAWLER_MODULE = self.config['path']['crawler_module']

    def open_url(self, treeview):
        '''openボタン押下時の処理を定義。

        :param tkinter.ttk.Treeview treeview: 情報取得元ツリービュー。
        '''

        # フォーカス部分の要素を辞書として取得
        item_dict = treeview.item(treeview.focus())

        if item_dict['values']:
            url = item_dict['values'][3]

            self.open_new_tab(url)

    def flush(self, treeview):
        '''flushボタン押下時の処理を定義。

        :param tkinter.ttk.Treeview treeview: 情報取得元ツリービュー。
        '''

        # ツリービューの初期化
        treeview.delete(*treeview.get_children())
        # ソート状態を初期化
        self.current_sort_state = None
        # ソート用検索ワードを初期化
        self.search_word_for_sort = None

    def copy_url(self, treeview):
        '''URLをクリップボードに追加する処理を定義。

        :param tkinter.ttk.Treeview treeview: 情報取得元ツリービュー。
        '''

        # フォーカス部分の要素を辞書として取得
        item_dict = treeview.item(treeview.focus())

        if item_dict['values']:
            url = item_dict['values'][3]

            pyperclip.copy(url)

    def copy_title(self, treeview):
        '''タイトルをクリップボードに追加する処理を定義。

        :param tkinter.ttk.Treeview treeview: 情報取得元ツリービュー。
        '''

        # フォーカス部分の要素を辞書として取得
        item_dict = treeview.item(treeview.focus())

        if item_dict['values']:
            title = item_dict['values'][1]

            pyperclip.copy(title)

    def copy_all(self, treeview):
        '''タイトル、URL、ブックマーク数をコピーする処理を定義。

        :param tkinter.ttk.Treeview treeview: 情報取得元ツリービュー。
        '''

        # フォーカス部分の要素を辞書として取得
        item_dict = treeview.item(treeview.focus())

        if item_dict['values']:
            url = item_dict['values'][3]
            title = item_dict['values'][1]
            bookmarks = str(item_dict['values'][2])

            pyperclip.copy(' '.join([url, title, bookmarks]))

    def open_by_double_click(self, treeview):
        '''左ダブルクリック時に発生する処理を定義。

        :param tkinter.ttk.Treeview treeview: 情報取得元ツリービュー。
        '''

        # フォーカス部分の要素を辞書として取得
        item_dict = treeview.item(treeview.focus())

        if item_dict['values']:
            url = item_dict['values'][3]

            self.open_new_tab(url)

    def read_log(self, text_form, textarea):
        '''readボタン押下時の処理を定義。

        :param tkinter.ttk.Entry text_form: 日付取得元テキストフォーム。
        :param MetisCustomText textarea: 出力先テキストエリア。
        '''

        if textarea.get('1.0', END):
            # テキストフォームの初期化
            textarea.delete('1.0', END)
        # 入力された値の取得
        input_date = text_form.get()

        split_words = '-/., '
        if '.mlog' in input_date:
            # ファイル名と拡張子を分割
            root, ext = os.path.splitext(input_date)
            date = ''.join(split(root, split_words))
            path_name = self.PATH_DIR_LOG + date + '.mlog'
        else:
            date = ''.join(split(input_date, split_words))
            path_name = self.PATH_DIR_LOG + date + '.mlog'

        if os.path.exists(path_name):
            text_lines = ''
            with open(path_name, 'r') as f:
                text_lines = f.readlines()

            # 取得した行数分だけ処理
            for line in text_lines:
                textarea.insert(END, line)
            textarea.pack()
        else:
            # ログファイルが存在しなかった場合
            messagebox.showerror('ERR_NO_FILE_FOUND',
                                    'Failed to open log file.\r\n' \
                                    'No such file or directory.')

    def get_log_list(self, textarea):
        '''listボタン押下時の処理を定義

        :param MetisCustomText textarea: 出力先テキストエリア。
        '''

        if textarea.get('1.0', END):
            # テキストフォームの初期化
            textarea.delete('1.0', END)

        # logディレクトリ内のファイルを取得
        log_files = os.listdir(self.PATH_DIR_LOG)
        for log in log_files:
            # ファイル名と拡張子を分割
            _, ext = os.path.splitext(log)
            if ext == '.mlog':
                textarea.insert(END, log + '\r\n')
        textarea.pack()

    def execute_crawler(self, order: str):
        '''処理オーダに応じたクローリング処理を行う。

        :param str order: クローラの振る舞いを決定する処理オーダ。
        '''

        try:
            conn, cursor = connect_to_database()
            # シリアル番号の生成
            serial_number = create_serial_number()

            # シリアル番号登録前の管理テーブルは常に空であることを想定している
            # 空でない場合はレコードの削除処理を行う
            if self.manage_serial_dao.count_records(cursor) != 0:
                self.manage_serial_dao.delete_records(cursor)

            # クローラ起動のためのシリアル番号を管理テーブルに登録する
            self.manage_serial_dao.insert_serial_no(cursor, serial_number)
            conn.commit()

        except sqlite3.Error as e:
            self.log.normal(LogLevel.ERROR.value, 'LERR0001', self.CLASS_NAME_COMMAND, self.log.location())
            self.log.error(e)
        finally:
            conn.close()
            self.log.normal(LogLevel.INFO.value, 'LINF0005', self.CLASS_NAME_COMMAND, self.log.location())

        if messagebox.askyesno('CONFIRMATION', 'Are you sure you want to run?'):
            cmd = 'python {} {} {}'
            subprocess.Popen(cmd.format(self.PATH_CRAWLER_MODULE, order, serial_number))

    def create_search_form(self, master, textarea):
        '''子画面として検索フォームを生成するメソッド。

        :param tkinter.Tk master: 画面のフレーム。
        :param MetisCustomText textarea: 検索対象テキストエリア。
        '''

        search_form = Toplevel(master=master)

        # ウィンドウの設定
        self.set_window_basic_config(master=search_form, title='Metis - Search Form', expand=False, width=400, height=80)
        search_form.transient(master)

        # 検索フォームの生成
        metis_search_form = MetisSearchForm(search_form, textarea)
        metis_search_form.pack()

    def update_line_numbers(self, canvas, textarea):
        '''イベント発生時に行番号を更新しキャンバスを再描画するメソッド。

        :param tkinter.Canvas canvas: 行番号描画用キャンバス。
        :param MetisCustomText textarea: 座標取得元テキストエリア。
        '''

        # キャンバスの初期化
        canvas.delete(ALL)

        # 0,0座標が何行目かを取得
        #
        first_row = textarea.index('@0,0')
        current_number = int(split(first_row, '.')[0])

        while True:
            # 行の位置と大きさを取得
            dline = textarea.dlineinfo('{0}.0'.format(current_number))

            if dline is None:
                # 行が存在しない場合
                # または行が見えない場合
                break
            else:
                # y座標の取得
                y = dline[1]

            # 行番号をキャンバスへ描画する
            canvas.create_text(3, y, anchor=NW, text=current_number)
            current_number += 1

    def create_treeview_menu(self, popup, treeview):
        '''ツリービュー系統のメニューを作成するメソッド。

        :param tkinter.Menu popup: メニューオブジェクト。
        :param tkinter.ttk.Treeview treeview: 処理付加対象ツリービュー。
        '''

        popup.add_command(label='Copy Path', command=partial(self.copy_url, treeview))
        popup.add_command(label='Copy Title', command=partial(self.copy_title, treeview))
        popup.add_command(label='Copy All', command=partial(self.copy_all, treeview))

class Application(Command):
    '''GUIの出力処理を定義するクラス。'''

    def __init__(self, *args, **kwargs):
        '''コンストラクタ。

        :param tuple args: タプルの可変長引数。
        :param dict kwargs: 辞書の可変長引数。
        '''

        # 基底クラスのコンストラクタを実行
        super().__init__()

        # クラス名
        self.CLASS_NAME = 'Application'

        # 処理オーダ : クローリング
        self.ORDER_CRAWLING = '0'
        # 処理オーダ : ブックマーク更新
        self.ORDER_UPDATE_BOOKMARKS = '1'

    def execute_application(self):
        '''アプリケーションを実行するメソッド。'''

        self.log.normal(LogLevel.INFO.value, 'LINF0001', self.CLASS_NAME, self.log.location())

        # セットアップ開始時間
        start = time.time()

        # ウィンドウの閉じるボタンを無効化
        self.master.protocol('WM_DELETE_WINDOW', self.disable_close_button)
        # エスケープキーに画面を閉じる機能を割り当て
        self.master.bind('<Escape>', lambda x: self.quit(self.master))

        # ウィンドウの構築
        self.__create_window()
        # メニューバーの生成
        self.__create_menubar()

        # セットアップ完了時間
        elapsed_time = time.time() - start
        # ステータスバーに反映
        self.status['text'] = 'Setup elapsed time : {} [sec]'.format(elapsed_time)

        self.master.mainloop()

    def __create_menubar(self):
        '''メニューバーを生成するメソッド。'''

        menubar = Menu(self.master)

        # ファイルメニュー
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label='Exit', command=partial(self.quit, self.master))
        menubar.add_cascade(label='File', menu=file_menu)

        # トップ画面の編集メニュー
        edit_top_menu = Menu(menubar, tearoff=0)
        search_form_menu = Menu(menubar, tearoff=0)
        treeview_menu = Menu(menubar, tearoff=0)
        sort_treeview_menu = Menu(menubar, tearoff=0)
        edit_top_menu.add_cascade(label='Search Form', menu=search_form_menu)
        edit_top_menu.add_cascade(label='Treeview', menu=treeview_menu)
        self.create_basic_menu(search_form_menu, self.btn_search_terms)
        self.create_treeview_menu(treeview_menu, self.btn_search_terms)
        treeview_menu.add_separator()
        treeview_menu.add_cascade(label='Sort', menu=sort_treeview_menu)
        sort_treeview_menu.add_command(label='Ascending', command=partial(self.__handle_sort_treeview, self.SORT_ASC))
        sort_treeview_menu.add_command(label='Descending', command=partial(self.__handle_sort_treeview, self.SORT_DESC))
        menubar.add_cascade(label='Edit Top', menu=edit_top_menu)

        # ログ参照画面の編集メニュー
        edit_log_menu = Menu(menubar, tearoff=0)
        date_search_form_menu = Menu(menubar, tearoff=0)
        text_area_menu = Menu(menubar, tearoff=0)
        edit_log_menu.add_cascade(label='Date Search Form', menu=date_search_form_menu)
        edit_log_menu.add_cascade(label='Textarea', menu=text_area_menu)
        self.create_basic_menu(date_search_form_menu, self.input_date)
        self.create_cancel_menu(text_area_menu, self.output_text_log)
        text_area_menu.add_separator()
        self.create_basic_menu(text_area_menu, self.output_text_log)
        menubar.add_cascade(label='Edit Log', menu=edit_log_menu)

        # クローラメニュー
        crawler_menu = Menu(menubar, tearoff=0)
        start_crawling = Menu(menubar, tearoff=0)
        update_bookmarks = Menu(menubar, tearoff=0)
        crawler_menu.add_cascade(label='Hatena', menu=start_crawling)
        start_crawling.add_command(label='Start Crawling', command=partial(self.execute_crawler, self.ORDER_CRAWLING))
        start_crawling.add_command(label='Update Bookmarks', command=partial(self.execute_crawler, self.ORDER_UPDATE_BOOKMARKS))
        menubar.add_cascade(label='Crawler', menu=crawler_menu)

        # helpメニュー
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label='Document', command=partial(self.open_new_tab, self.URL_DOCS))
        help_menu.add_command(label='About Software', command=partial(self.open_new_tab, self.URL_README))
        help_menu.add_separator()
        help_menu.add_command(label='License', command=partial(self.open_new_tab, self.URL_LICENSE))
        menubar.add_cascade(label='Help', menu=help_menu)

        self.master.config(menu=menubar)

    def __create_window(self):
        '''ウィンドウを構築するメソッド。'''

        notebook = ttk.Notebook(self.master)
        # top画面用のフレーム
        frame_update_articles = Frame(notebook, bd=2, relief=GROOVE)
        # log検索画面用のフレーム
        frame_show_log = Frame(notebook, bd=2, relief=GROOVE)

        # top画面用のタブ
        notebook.add(frame_update_articles, text='Top')
        # log検索画面用のタブ
        notebook.add(frame_show_log, text='Log')
        notebook.pack(expand=1, fill=BOTH, anchor=NW)

        # TOP画面の作成
        self.__create_top_gui(frame_update_articles)
        # ログ出力画面の作成
        self.__create_log_gui(frame_show_log)

        # ステータスバー
        self.status = Label(self.master, relief=FLAT)
        self.status.pack(side=BOTTOM, fill=X)

        # ウィンドウの設定
        self.set_window_basic_config(master=self.master)

    def __create_top_gui(self, parent: Frame):
        '''TOP画面の出力を定義するメソッド。

        :param tkinter.Frame parent: 画面の親フレーム。
        '''

        # 検索フォームのフレーム
        frame_search_terms = LabelFrame(parent, labelanchor=N, relief=FLAT, text='Enter search terms')
        frame_search_terms.pack(pady=20)

        # 最大表示件数入力フォームの設定
        self.btn_search_terms = ttk.Entry(frame_search_terms, justify=CENTER, width=40)
        # リターンキー押下で検索を開始するように設定
        self.btn_search_terms.bind('<Return>', lambda x: self.__refresh_tree_view())
        # 画面開設時のフォーカスを入力欄に設定する
        self.btn_search_terms.focus_set()
        self.btn_search_terms.pack(side=LEFT, padx=5)

        # 検索フォームでのポップアップメニューを設定
        popup_search_terms = Menu(parent, tearoff=0)
        self.create_basic_menu(popup_search_terms, self.btn_search_terms)

        # 検索フォーム上での右クリックでポップアップメニューを表示する
        self.btn_search_terms.bind('<ButtonRelease-3>', lambda event: self.open_popup(event, popup_search_terms))

        # 検索ボタン
        search_button = ttk.Button(frame_search_terms, text='Search', width=10, command=self.__refresh_tree_view)
        search_button.pack(side=LEFT)

        # ツリービューの構築
        self.__create_tree_view(parent)

        # ボタンのフレーム
        frame_button = Frame(parent, relief=FLAT)
        frame_button.pack(side=BOTTOM, pady=30)

        # 開くボタン
        open_button = ttk.Button(frame_button, text='Open', width=20, command=partial(self.open_url, self.treeview))
        open_button.pack(side=LEFT, padx=60)
        # 初期化ボタン
        flush_button = ttk.Button(frame_button, text='Flush', width=20, command=partial(self.flush, self.treeview))
        flush_button.pack(side=LEFT, padx=60)
        # 終了ボタン
        quit_button = ttk.Button(frame_button, text='Quit', width=20, command=partial(self.quit, self.master))
        quit_button.pack(side=LEFT, padx=60)

    def __create_tree_view(self, parent: Frame):
        '''ツリービューの構築を行うメソッド。

        :param tkinter.Frame parent: 画面の親フレーム。
        '''

        # ツリービューのフレーム
        frame_tree_view = Frame(parent, relief=RIDGE)
        frame_tree_view.pack(fill=BOTH, expand=True)

        # ツリービューのオブジェクトを生成
        self.treeview = ttk.Treeview(frame_tree_view)

        # スクロールバーの生成
        self.create_xy_scrollbar(frame_tree_view, self.treeview)

        # カラムの設定
        self.treeview['columns'] = (1, 2, 3, 4)
        self.treeview.column(1, width=50)
        self.treeview.column(2, width=1000)
        self.treeview.column(3, width=50)
        self.treeview.column(4)

        # ヘッダの設定
        self.treeview['show'] = 'headings'
        self.treeview.heading(1, text='No.')
        self.treeview.heading(2, text='Title')
        self.treeview.heading(3, text='Bookmarks', command=partial(self.__refresh_tree_view, True))
        self.treeview.heading(4)
        self.treeview.configure(style='my.Treeview', displaycolumns=(1, 2, 3))

        # ポップアップメニューの設定
        popup_treeview = Menu(parent, tearoff=0)
        self.create_treeview_menu(popup_treeview, self.treeview)

        # ダブルクリックでページを開くように設定
        self.treeview.bind('<Double-1>', lambda x: self.open_by_double_click(self.treeview))
        # 右クリックでポップアップメニューを表示する
        self.treeview.bind('<ButtonRelease-3>', lambda event: self.open_popup(event, popup_treeview))

        # ツリービューのレイアウト設定
        style = ttk.Style(parent)
        style.configure('my.Treeview', rowheight=30)
        style.configure('Treeview', font=('Consolas', 10))
        style.configure('Treeview.Heading', font=('Consolas', 10, 'bold'))

        self.treeview.pack(fill=BOTH, expand=True)

    def __refresh_tree_view(self, is_sort=False):
        '''取得した記事情報からツリービューを生成するメソッド。

        :param bool is_sort: ソート可否フラグ (True/ False)。初期値はFalse。
        '''

        # ステータスバーに反映する初期文言
        status_msg = 'Elapsed time : {} [sec]'
        # 処理開始時間
        start = time.time()

        search_word = ''
        if not is_sort:
            # ソートを行わない場合に検索ワードを取得
            search_word = self.btn_search_terms.get()

        # 検索時とヘッダーのbookmarks押下によるソート時で処理が異なる
        if search_word or (self.search_word_for_sort and is_sort):
            # ツリービューの初期化
            self.treeview.delete(*self.treeview.get_children())

            try:
                # データベースへ接続
                conn, cursor = connect_to_database()
                # 記事情報
                article_infos = None

                if is_sort:
                    # ソートする場合
                    if self.current_sort_state == self.SORT_ASC or not self.current_sort_state:
                        # 降順にソートしたレコードを取得
                        article_infos = self.article_info_hatena_dao.select_order_by_bookmarks_desc(cursor, '%{}%'.format(self.search_word_for_sort))
                        self.current_sort_state = self.SORT_DESC
                    else:
                        # 昇順にソートしたレコードを取得
                        article_infos = self.article_info_hatena_dao.select_order_by_bookmarks_asc(cursor, '%{}%'.format(self.search_word_for_sort))
                        self.current_sort_state = self.SORT_ASC
                else:
                    # ソートしない場合
                    article_infos = self.article_info_hatena_dao.select_by_search_word(cursor, '%{}%'.format(search_word))
                    # ソート状態を初期化
                    self.current_sort_state = None
                    # ソート用検索ワードを更新
                    self.search_word_for_sort = search_word

                if article_infos:
                    # TreeViewに記事情報を反映させる
                    for i, infos in enumerate(article_infos):
                        value = (str(i+1), infos[1], infos[3], infos[0])
                        self.treeview.insert('', END, tags=i, values=value)

                        if i & 1:
                            # 偶数行の背景色を変更
                            self.treeview.tag_configure(i, background='#CCFFFF')

                    self.treeview.pack(fill=BOTH, expand=True)

                    # 取得数
                    count_records = len(article_infos)
                    # 処理完了時間
                    elapsed_time = time.time() - start
                    # ステータスバーに反映する文言を更新
                    status_msg = 'Sort elapsed time : {} [sec] | {} {}' if is_sort else 'Search elapsed time : {} [sec] | {} {}'

                    # ソート時の処理時間をステータスバーに反映
                    self.status['text'] = status_msg.format(elapsed_time, count_records, 'records' if count_records > 1 else 'record')
                else:
                    # ソート用検索ワードを初期化
                    self.search_word_for_sort = None

                    # 処理完了時間
                    elapsed_time = time.time() - start
                    # ステータスバーに反映
                    self.status['text'] = status_msg.format(elapsed_time)

                    messagebox.showinfo('NO_RESULTS_FOUND',
                                            'Your search - ' \
                                            + search_word \
                                            + ' - did not match any documents.')
            except sqlite3.Error as e:
                self.log.normal(LogLevel.ERROR.value, 'LERR0001', self.CLASS_NAME, self.log.location())
                self.log.error(e)
            finally:
                conn.close()
                self.log.normal(LogLevel.INFO.value, 'LINF0005', self.CLASS_NAME, self.log.location())
        else:
            # 処理完了時間
            elapsed_time = time.time() - start
            # ステータスバーに反映
            self.status['text'] = status_msg.format(elapsed_time)

            if is_sort:
                # ソート時
                messagebox.showerror('ERR_NO_ITEM_FOUND', 'Sorting is not available.\r\n' \
                                                            'There are no items in the tree view.')
            else:
                # 検索時
                messagebox.showerror('ERR_EMPTY_REQUESTED', 'This field must not be empty.')

    def __create_log_gui(self, parent: Frame):
        '''Log検索画面の出力を定義するメソッド。

        :param tkinter.Frame parent: 画面の親フレーム。
        '''

        # 検索フォームのフレーム
        frame_log_file = LabelFrame(parent, labelanchor=N, relief=FLAT, text='Enter the date')
        frame_log_file.pack(pady=20)

        # 日付入力フォームの生成
        self.input_date = ttk.Entry(frame_log_file, font=('Consolas', 10), justify=CENTER, width=20)
        self.input_date.insert(END, datetime.today().strftime('%Y/%m/%d'))

        # 出力用テキストエリアの生成
        self.__create_custom_text_area(parent)

        # リターン時にファイルの読み込み処理を行う
        self.input_date.bind('<Return>', lambda x: self.read_log(self.input_date, self.output_text_log))
        self.input_date.focus_set()
        self.input_date.pack(side=LEFT, padx=5)

        # 読み込みボタン
        search_button = ttk.Button(frame_log_file, text='Read', width=10, command=partial(self.read_log, self.input_date, self.output_text_log))
        search_button.pack(side=LEFT)

        # ボタンのフレーム
        frame_button = Frame(parent, relief=FLAT)
        frame_button.pack(side=BOTTOM, pady=30)

        # ファイルダイアログを開くボタン
        open_button = ttk.Button(frame_button, text='Open', width=20, command=partial(self.open, self.output_text_log))
        open_button.pack(side=LEFT, padx=60)
        # ファイルのリストを取得するボタン
        list_button = ttk.Button(frame_button, text='List', width=20, command=partial(self.get_log_list, self.output_text_log))
        list_button.pack(side=LEFT, padx=60)
        # 終了ボタン
        quit_button = ttk.Button(frame_button, text='Quit', width=20, command=partial(self.quit, self.master))
        quit_button.pack(side=LEFT, padx=60)

    def __create_custom_text_area(self, parent):
        '''カスタムテキストエリアを生成するメソッド。

        :param tkinter.Frame parent: 画面の親フレーム。
        '''

        # 出力用フォームの設定
        frame_text_log = Frame(parent, pady=10, bd=0)
        frame_text_log.pack(fill=BOTH, expand=True)

        # 行番号出力用キャンバス
        line_numbers = Canvas(frame_text_log, width=30)
        line_numbers.pack(side=LEFT, fill=BOTH)

        # 拡張テキストエリアの生成
        self.output_text_log = MetisCustomText(frame_text_log, font=('Consolas', 10))

        # ポップアップメニューの設定
        popup_text_log = Menu(parent, tearoff=0)
        popup_text_log.add_command(label='Open', command=partial(self.open, self.output_text_log))
        popup_text_log.add_separator()
        self.create_cancel_menu(popup_text_log, self.output_text_log)
        popup_text_log.add_separator()
        self.create_basic_menu(popup_text_log, self.output_text_log)

        # 右クリックでポップアップメニューを表示する
        self.output_text_log.bind('<ButtonRelease-3>', lambda event: self.open_popup(event, popup_text_log))

        # テキストエリアの行番号描画イベントのバインド用リスト
        list_events_textarea = ['<<Scroll>>', '<<Change>>', '<Configure>', '<FocusIn>']
        for event in list_events_textarea:
            # on_changeイベントとイベント発生時処理の紐付け
            self.output_text_log.bind(event, lambda x: self.update_line_numbers(canvas=line_numbers, textarea=self.output_text_log))

        # スクロールバーの生成
        self.create_xy_scrollbar(frame_text_log, self.output_text_log)

        # テキストエリア上でCtrl+F押下時に検索ボックスを開くように設定
        self.output_text_log.bind('<Control-f>', lambda x: self.create_search_form(self.master, self.output_text_log))
        self.output_text_log.pack(side=LEFT, fill=BOTH, expand=True)

    def __handle_sort_treeview(self, order: str):
        '''オーダ毎にソート順を決定するメソッド。

        :param str order: ソート順を決定する処理オーダ。
        '''

        # ソート順を設定しツリービューを再表示する
        self.current_sort_state = order
        self.__refresh_tree_view(True)

if __name__ == '__main__':
    app = Application()
    app.execute_application()
