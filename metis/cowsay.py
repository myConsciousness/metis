# -*- coding: utf-8 -*-

'''

The original Cowsays are written in the Perl programming language,
and as such are easily adaptable to system tasks in Unix.
They can perform functions such as telling users their home directories are full,
that they have new mail, etc.

:copyright: (c) 2018 by Kato Shinya.
:license: MIT, see LICENSE for more details.
'''

import re

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

class Cowsay:
    ''' PythonでのCowsays実装クラス。 '''

    def __init__(self):
        ''' コンストラクタ。 '''

        self.COW = r'''
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
        '''

        self.MAX_LENGTH = 39

    def cowsay(self, text: str) -> str:
        '''牛のアスキー画像と引数として渡されたテキストを融合させるメソッド。

        :param str text: 牛に喋らせる文章。
        :rtype: str
        :return: アスキー画像。

        >>> cowsay('Hello World!')
        >>>  ______________
        >>> < Hello World! >
        >>>  --------------
        >>>     \   ^__^
        >>>      \  (oo)\_______
        >>>         (__)\       )\/\
        >>>             ||----w |
        >>>             ||     ||
        '''

        lines = []
        for phrase in text.split('\n'):
            lines.extend(self.__cut(phrase))

        length = max(len(line) for line in lines)
        cowquote = ['', ' ' + '_' * (length + 2)]

        if len(lines) == 1:
            cowquote.append(self.__format_line(lines[0], length, '< ', ' >'))
        else:
            cowquote.append(self.__format_line(lines[0], length, '/ ', ' \\'))
            for i in range(1, len(lines) - 1):
                cowquote.append(self.__format_line(lines[i], length, '| ', ' |'))

            cowquote.append(self.__format_line(lines[-1], length, '\\ ', ' /'))
        cowquote.append(''.join((' ', '-' * (length + 2), self.COW)))

        return '\n'.join(cowquote)

    def __cut(self, phrase: str) -> list:
        '''文章を仕分けるメソッド。

        :param str phrase: 仕分け対象のフレーズ。
        :trype: list
        :return: 仕分けされたフレーズを格納したリスト。
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

    def __format_line(self, line: str, length: int, first: str, last: str) -> str:
        '''文章を覆う枠を作成するメソッド。

        :param str line: 文章。
        :param int length: 文章中の最大文字列長。
        :param str first: 開始枠。
        :param str last: 終了枠。
        :rtype: str
        :return: 枠に覆われた文章。
        '''

        return ''.join((first, line, ' ' * (length - len(line)), last))
