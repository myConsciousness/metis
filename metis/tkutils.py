# -*- coding: utf-8 -*-

'''
:copyright: (c) 2018 by Kato Shinya.
:license: MIT, see LICENSE for more details.
'''

from tkinter import *
import tkinter.ttk as ttk

__author__ = 'Kato Shinya'
__date__ = '2018/08/11'

class CustomText(Text):
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

class SearchForm(ttk.Frame):
    '''検索フォームを定義するクラス。'''

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
        self.search_form.focus()

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

    def __search(self):
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
