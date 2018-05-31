# -*- coding: utf-8 -*-

from logging import getLogger
from logging import FileHandler
from logging import StreamHandler
from logging import Formatter
from datetime import datetime
from enum import Enum
import configparser
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

    # プロセス開始
    MSG_PROCESS_STARTED = '[{}]:【START】The process has been started in {} method, {} class.'
    # クローリング開始
    MSG_CRAWLING_STARTED = '[{}]:【START】The crawling has been started in {} method, {} class.'
    # スクレイピング開始
    MSG_SCRAPING_STARTED = '[{}]:【START】The scraping has been started in {} method, {} class.'

    # ロールバック処理完了
    MSG_ROLLBACK_COMPLETED = '[{}]:【INFO】The database has been rollbacked in {}method, {} class.'
    # 開放処理完了
    MSG_CLOSE_COMPLETED = '[{}]:【INFO】The database has been closed in {} method, {} class.'

    # クローリング完了
    MSG_CRAWLING_COMPLETED = '[{}]:【END】The crawling has been completed in {} method, {} class.'
    # スクレイピング完了
    MSG_SCRAPING_COMPLETED = '[{}]:【END】The scraping has been completed in {} method, {} class.'
    # プロセス完了
    MSG_PROCESS_COMPLETED = '[{}]:【END】The process has been completed in {} method, {} class.'

    # エラー
    MSG_ERROR = '[{}]【ERROR】The error has been occurred in {} method, {} class.'

    # サーバーへの到達不能エラー
    MSG_NO_SERVER_FOUND = '[{}]:【CRITICAL】Failed to reach a server. It has been occurred in {} method, {} class.'
    # リクエストエラー
    MSG_NO_RESPONSE = '[{}]:【CRITICAL】The server couldn\'t fulfill the request. It has been occurred in {} method, {} class.'

    def __init__(self, child=False):
        '''コンストラクタ。'''

        config = configparser.ConfigParser()
        config.read('../env/config.ini')
        self.DIR_LOG = config['path']['dir_log']

        PATH_TO_LOG_FILE = self.DIR_LOG + datetime.today().strftime('%Y%m%d') + '.log'
        # ログファイルの有効性チェック
        self.__check_status_of_log_file(PATH_TO_LOG_FILE)

        if child:
            self.logger = getLogger(__name__)
        else:
            self.logger = getLogger(__name__).getChild(__name__)

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

        self.logger.log(level, message.format(location[1], location[0], class_name))

    def error(self, error_info):
        '''例外情報のログ出力を行うメソッド。

        :param Exception error_info: プロセス実行中に発生した例外情報。
        '''

        self.logger.exception(e)

    def location(self) -> list:
        '''実行中のメソッド名/関数名と行番号を返すメソッド。

        :rtype: list
        :return: 実行中のメソッド名/関数名と行番号を格納したリスト。
        '''

        frame = inspect.currentframe().f_back
        return [frame.f_code.co_name, frame.f_lineno]

    def __check_status_of_log_file(self, path_to_log: str):
        '''ログファイルの有効性を判定する関数。
        格納ディレクトリとログファイルが存在しない場合には生成処理を行う。

        :param str path_to_log: ログファイルへのパス。
        '''

        if not os.path.exists(self.DIR_LOG):
            # ディレクトリの作成
            os.mkdir(self.DIR_LOG)
            # logファイルの作成
            with open(path_to_log, 'w'):
                pass
        else:
            if not os.path.exists(path_to_log):
                # logファイルの作成
                with open(path_to_log, 'w'):
                    pass
