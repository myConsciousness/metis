# -*- coding: utf-8 -*-

'''
The original Cowsays are written in the Perl programming language,
and as such are easily adaptable to system tasks in Unix.
They can perform functions such as telling users their home directories are full,
that they have new mail, etc.

Question) What does the cow say?

 _________________________________
< Do. Or do not. There is no try. >
 ---------------------------------
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||

'''

import re

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

class Cowsay:
    ''' Pythonを用いたCowsaysの実装クラス '''

    def __init__(self):
        ''' コンストラクタ '''

        self.COW = r'''
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
        '''

        self.MAX_LENGTH = 39

    def cowsay(self, text: str) -> str:
        '''牛のアスキー画像とテキストを融合させるメソッド

        Args
        ----
        text (str): 牛に喋らせる文章。

        Returns
        -------
        アスキー画像。

        '''

        lines = []
        for phrase in text.split('\n'):
            lines.extend(self.cut(phrase))

        length = max(len(line) for line in lines)
        cowquote = ['', ' ' + '_' * (length + 2)]

        if len(lines) == 1:
            cowquote.append(self.format_line(lines[0], length, '< ', ' >'))
        else:
            cowquote.append(self.format_line(lines[0], length, '/ ', ' \\'))
            for i in range(1, len(lines) - 1):
                cowquote.append(self.format_line(lines[i], length, '| ', ' |'))

            cowquote.append(self.format_line(lines[-1], length, '\\ ', ' /'))
        cowquote.append(''.join((' ', '-' * (length + 2), self.COW)))

        return '\n'.join(cowquote)

    def cut(self, phrase: str) -> list:
        '''文章を仕分けるメソッド

        Args
        ----
        phrase (str): 仕分け対象のフレーズ。

        Returns
        -------
        仕分けされたフレーズを格納したリスト。

        '''

        words = re.split(' +', phrase)
        words.reverse()
        lines = []

        while words:
            word = words.pop()
            length = len(word)

            if length > self.MAX_LENGTH:
                lines.append(word[:self.MAX_LENGTH])
                words.append(word[self.MAX_LENGTH:])
                continue

            line = [word]
            while words:
                length += 1 + len(words[-1])
                if length > self.MAX_LENGTH:
                    break

                line.append(words.pop())
            lines.append(' '.join(line))

        return lines

    def format_line(self, line: str, length: int, first: str, last: str) -> str:
        '''文章を覆う枠を作成するメソッド

        Args
        ----
        line (str): 文章。
        length (int): 文章中の最大文字列長。
        first (str): 開始枠。
        last (str): 終了枠。

        Returns
        -------
        枠に覆われた文章。

        '''

        return ''.join((first, line, ' ' * (length - len(line)), last))
