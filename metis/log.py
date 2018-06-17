# -*- coding: utf-8 -*-

'''
:copyright: (c) 2018 by Kato Shinya.
:license: MIT, see LICENSE for more details.
'''

from logging import getLogger
from logging import FileHandler
from logging import StreamHandler
from logging import Formatter
from datetime import datetime
from enum import Enum
from common import *
import inspect
import os.path
import os

__author__ = 'Kato Shinya'
__date__ = '2018/04/21'

class LogLevel(Enum):
    '''enum型としてログレベルを定義。'''

    NOTEST = 0
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class Log:
    '''ログ出力を行うクラス。'''

    def __init__(self, child=False):
        '''コンストラクタ。'''

        # config情報の取得
        config = read_config_file()
        # ログメッセージを取得
        self.message = read_log_message_file()

        self.PATH_DIR_LOG = config['path']['dir_log']
        # ログファイルへのパスを生成
        PATH_TO_LOG_FILE = self.PATH_DIR_LOG + datetime.today().strftime('%Y%m%d') + '.mlog'
        # ログファイルの有効性チェック
        self.__check_status_of_log_file(PATH_TO_LOG_FILE)

        if child:
            self.logger = getLogger(__name__).getChild(__name__)
        else:
            self.logger = getLogger(__name__)

        self.logger.setLevel(config['general']['log_level'])
        fh = FileHandler(PATH_TO_LOG_FILE)
        self.logger.addHandler(fh)
        fh.setFormatter(Formatter('%(asctime)s:%(levelname)s:%(message)s'))

    def normal(self, level: int, id: str, class_name: str, location: list):
        '''例外情報以外のログ出力を行うメソッド。

        :param int level: ログレベル。
        :param str id: メッセージ管理番号。
        :param str class_name: クラス名。
        :param list location: メソッド名/関数名と行番号が格納されたリスト。
        '''

        self.logger.log(level, self.message[str(level)][id].format(location[0], location[1], class_name))

    def debug(self, id: str, var_name: str, var_value, line_no: str):
        '''デバッグ情報のログ出力を行うメソッド。

        :param str id: メッセージ管理番号。
        :param str var_name: デバッグ対象の変数名。
        :param inferred-type var_value: デバッグ対象の値。
        :param str line_no: 実行中の行番号。
        '''

        self.logger.log(LogLevel.DEBUG.value, self.message['10'][id].format(line_no, var_name, var_value))

    def error(self, error_info):
        '''例外情報のログ出力を行うメソッド。

        :param Exception error_info: プロセス実行中に発生した例外情報。
        '''

        self.logger.exception(error_info)

    def location(self) -> list:
        '''実行中のメソッド名/関数名と行番号を返すメソッド。

        :rtype: list
        :return: 実行中のメソッド名/関数名と行番号を格納したリスト。
        '''

        frame = inspect.currentframe().f_back
        return [frame.f_lineno, frame.f_code.co_name]

    def get_lineno(self) -> str:
        '''実行中の行番号を返すメソッド。

        :rtype: str
        :return: 実行中の行番号。
        '''

        return inspect.currentframe().f_back.f_lineno

    def get_method_name(self) -> str:
        '''実行中のメソッド名/関数名を返すメソッド。

        :rtype: str
        :return: 実行中のメソッド名/関数名。
        '''

        return inspect.currentframe().f_back.f_code.co_name

    def __check_status_of_log_file(self, path_to_log: str):
        '''ログファイルの有効性を判定するメソッド。
        格納ディレクトリとログファイルが存在しない場合には生成処理を行う。

        :param str path_to_log: ログファイルへのパス。
        '''

        if not os.path.exists(self.PATH_DIR_LOG):
            # ディレクトリの作成
            os.mkdir(self.PATH_DIR_LOG)
            # logファイルの作成
            with open(path_to_log, 'w'):
                pass
        else:
            if not os.path.exists(path_to_log):
                # logファイルの作成
                with open(path_to_log, 'w'):
                    pass
