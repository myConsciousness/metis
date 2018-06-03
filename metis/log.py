# -*- coding: utf-8 -*-

from logging import getLogger
from logging import FileHandler
from logging import StreamHandler
from logging import Formatter
from datetime import datetime
from enum import Enum
from common import *
import inspect
import os.path

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

        # 設定ファイルの読み込み
        config = read_config_file()
        self.PATH_DIR_LOG = config['path']['dir_log']

        PATH_TO_LOG_FILE = self.PATH_DIR_LOG + datetime.today().strftime('%Y%m%d') + '.log'
        # ログファイルの有効性チェック
        self.__check_status_of_log_file(PATH_TO_LOG_FILE)

        if child:
            self.logger = getLogger(__name__).getChild(__name__)
        else:
            self.logger = getLogger(__name__)

        self.logger.setLevel(int(config['general']['log_level']))
        fh = FileHandler(PATH_TO_LOG_FILE)
        self.logger.addHandler(fh)
        fh.setFormatter(Formatter('%(asctime)s:%(levelname)s:%(message)s'))

    def normal(self, level: int, class_name: str, location: list, message: str):
        '''例外情報以外のログ出力を行うメソッド。
        ログレベルと出力するメッセージに関しては、当該モジュールで定義された値を用いること。

        :param int level: ログレベル。
        :param str class_name: クラス名。
        :param list location: メソッド名/関数名と行番号が格納されたリスト。
        :param str message: 出力するログメッセージ。
        '''

        self.logger.log(level, message.format(location[0], location[1], class_name))

    def debug(self, message: str):
        '''デバッグ情報のログ出力を行うメソッド。

        :param str message: デバッグ情報。
        '''

        self.logger.log(LogLevel.DEBUG.value, message)

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

class LogMessage:
    '''ログ用メッセージの管理クラス'''

    def __init__(self):
        '''コンストラクタ。'''

        # プロセス開始
        self.__MSG_PROCESS_STARTED = '[{}]:【START】The process has been started in {} method, {} class.'
        # クローリング開始
        self.__MSG_CRAWLING_STARTED = '[{}]:【START】The crawling has been started in {} method, {} class.'
        # スクレイピング開始
        self.__MSG_SCRAPING_STARTED = '[{}]:【START】The scraping has been started in {} method, {} class.'

        # ロールバック処理完了
        self.__MSG_ROLLBACK_COMPLETED = '[{}]:【INFO】The database has been rollbacked in {}method, {} class.'
        # 開放処理完了
        self.__MSG_CLOSE_COMPLETED = '[{}]:【INFO】The database has been closed in {} method, {} class.'

        # クローリング完了
        self.__MSG_CRAWLING_COMPLETED = '[{}]:【END】The crawling has been completed in {} method, {} class.'
        # スクレイピング完了
        self.__MSG_SCRAPING_COMPLETED = '[{}]:【END】The scraping has been completed in {} method, {} class.'
        # プロセス完了
        self.__MSG_PROCESS_COMPLETED = '[{}]:【END】The process has been completed in {} method, {} class.'

        # エラー
        self.__MSG_ERROR = '[{}]【ERROR】The error has been occurred in {} method, {} class.'

        # サーバーへの到達不能エラー
        self.__MSG_NO_SERVER_FOUND = '[{}]:【CRITICAL】Failed to reach a server. It has been occurred in {} method, {} class.'
        # リクエストエラー
        self.__MSG_NO_RESPONSE = '[{}]:【CRITICAL】The server couldn\'t fulfill the request. It has been occurred in {} method, {} class.'

        # デバッグ開始
        self.__MSG_DEBUG_START = '[{}]:【DEBUG START】The debug has been started in {} method, {} class.'
        # 変数値のデバッグ情報
        self.__MSG_DEBUG_VALUE = '[{}]: A variable "{}" has a value "{}".'
        # デバッグ終了
        self.__MSG_DEBUG_COMPLETED = '[{}]:【DEBUG END】The debug has been completed in {} method, {} class.'

    @property
    def MSG_PROCESS_STARTED(self):
        '''プロセス開始メッセージのプロパティ。'''

        return self.__MSG_PROCESS_STARTED

    @property
    def MSG_CRAWLING_STARTED(self):
        '''クローリング開始メッセージのプロパティ。'''

        return self.__MSG_CRAWLING_STARTED

    @property
    def MSG_SCRAPING_STARTED(self):
        '''スクレイピング開始メッセージのプロパティ。'''

        return self.__MSG_SCRAPING_STARTED

    @property
    def MSG_ROLLBACK_COMPLETED(self):
        '''ロールバック処理完了メッセージのプロパティ。'''

        return self.__MSG_ROLLBACK_COMPLETED

    @property
    def MSG_CLOSE_COMPLETED(self):
        '''開放処理完了メッセージのプロパティ。'''

        return self.__MSG_CLOSE_COMPLETED

    @property
    def MSG_CRAWLING_COMPLETED(self):
        '''クローリング完了メッセージのプロパティ。'''

        return self.__MSG_CRAWLING_COMPLETED

    @property
    def MSG_SCRAPING_COMPLETED(self):
        '''スクレイピング完了メッセージのプロパティ。'''

        return self.__MSG_SCRAPING_COMPLETED

    @property
    def MSG_PROCESS_COMPLETED(self):
        '''プロセス完了メッセージのプロパティ。'''

        return self.__MSG_PROCESS_COMPLETED

    @property
    def MSG_ERROR(self):
        '''エラーメッセージのプロパティ。'''

        return self.__MSG_ERROR

    @property
    def MSG_NO_SERVER_FOUND(self):
        '''サーバーへの到達不能エラーメッセージのプロパティ。'''

        return self.__MSG_NO_SERVER_FOUND

    @property
    def MSG_NO_RESPONSE(self):
        '''リクエストエラーメッセージのプロパティ。'''

        return self.__MSG_NO_RESPONSE

    @property
    def MSG_DEBUG_START(self):
        '''デバッグ開始メッセージのプロパティ。'''

        return self.__MSG_DEBUG_START

    @property
    def MSG_DEBUG_VALUE(self):
        '''変数値のデバッグ情報メッセージのプロパティ。'''

        return self.__MSG_DEBUG_VALUE

    @property
    def MSG_DEBUG_COMPLETED(self):
        '''デバッグ終了メッセージのプロパティ。'''

        return self.__MSG_DEBUG_COMPLETED
