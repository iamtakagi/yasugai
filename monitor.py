import argparse
import json
import logging
import os
import threading
from time import sleep
from typing import Union

import requests
from mailthon import postman, email

from requests_oauthlib import OAuth1Session

from mercari import Mercari
from mercari import Rakuma

# Logger
logger = logging.getLogger(__name__)


def get_script_arguments():
    """引数を解析し、メインプロセスに渡します
    Returns:
        [type]: [description]
    """

    # 引数解析
    parser = argparse.ArgumentParser(description='新しいアイテムが一致するたびに通知をします。'
                                                 '以下の引数が利用可能です')

    # キーワード引数
    parser.add_argument('--keywords', required=True,
                        type=str, help='キーワード指定 (カンマ区切)')

    # 上限価格引数
    parser.add_argument('--max_prices', required=True, type=str,
                        help='上限価格 (カンマ区切)')

    # 下限価格引数
    parser.add_argument('--min_prices', required=True, type=str,
                        help='下限価格 (カンマ区切)')

    # 通知モジュールの有効有無
    parser.add_argument('--disable_alertzy', action='store_true')
    parser.add_argument('--disable_gmail', action='store_true')
    parser.add_argument('--disable_discord', action='store_true')
    parser.add_argument('--disable_line', action='store_true')
    parser.add_argument('--disable_twitter', action='store_true')

    # 引数を渡す
    args = parser.parse_args()
    logger.info(args)
    return args


class Alertzy:
    """Alertzy通知モジュール
    """

    def __init__(self):
        """初期化
        Args:
            logger ([type]): [description]
        """
        self.use_module = True
        self.lock = threading.Lock()
        config_filename = 'config/alertzy.json'
        if os.path.isfile(config_filename):
            with open(config_filename, 'r') as r:
                self.alertzy_key = json.load(r)['alertzy_key']
        else:
            self.use_module = False
            logger.warning('[Alertzy] 通知は無効です。')

    def send(self, message, title):
        """Alertzy 送信
        Args:
            message ([type]): [description]
            title ([type]): [description]
        Returns:
            [type]: [description]
        """
        if self.use_module:
            with self.lock:
                assert self.alertzy_key is not None
                try:
                    requests.post('https://alertzy.app/send', data={
                        'accountKey': self.alertzy_key,
                        'title': title,
                        'message': message
                    })
                except Exception:
                    return False
                return True


class Gmail:
    """Gmail通知モジュール
    """

    def __init__(self):
        """初期化
        Args:
            logger (Logger): [description]
        """
        self.use_module = True
        self.lock = threading.Lock()
        config_filename = 'config/gmail.json'
        if os.path.isfile(config_filename):
            with open(config_filename, 'r') as f:
                config = json.load(f)
                self.gmail_password = config['gmail_password']
                self.gmail_user = config['gmail_user']
                if '@' not in self.gmail_user:
                    logger.error('[Gmail] 無効なユーザーです。')
                    exit(1)
                self.recipients = [
                    x.strip() for x in config['recipients'].strip().split(',')]
        else:
            self.use_module = False
            logger.warning('[Gmail] 通知は無効です。')

    def send(self, email_subject, email_content, attachment=None):
        """Gmailから送信
        Args:
            email_subject ([type]): [description]
            email_content ([type]): [description]
            attachment ([type], optional): [description]. Defaults to None.
        """
        if self.use_module:
            with self.lock:
                if attachment is not None:
                    attachment = [attachment]
                else:
                    attachment = ()
                for recipient in self.recipients:
                    p = postman(host='smtp.gmail.com', auth=(
                        self.gmail_user, self.gmail_password))
                    r = p.send(email(content=email_content,
                                     subject=email_subject,
                                     sender='{0} <{0}>'.format(
                                         self.gmail_user),
                                     receivers=[recipient],
                                     attachments=attachment))
                    self.logger.info(f'[Gmail] 件名: {email_subject}.')
                    self.logger.info(f'[Gmail] 内容: {email_content}.')
                    self.logger.info(f'[Gmail] 添付ファイル: {attachment}.')
                    self.logger.info(
                        f'[Gmail] 通知は {self.gmail_user} から {recipient} へ送信されました。')
                    assert r.ok


class Discord:
    """Discord 通知モジュール
    """

    def __init__(self):
        """初期化
        Args:
            logger ([type]): [description]
        """
        self.use_module = True
        self.lock = threading.Lock()
        config_filename = 'config/discord.json'
        if os.path.isfile(config_filename):
            with open(config_filename, 'r') as r:
                self.discord_webhook_url = json.load(r)['discord_webhook_url']
        else:
            self.use_module = False
            logger.warning('[Discord] 通知は無効です。')

    def send(self, title, text):
        """Discordに送信
        Args:
            title ([type]): [description]
            text ([type]): [description]

        Returns:
            [type]: [description]
        """
        if self.use_module:
            with self.lock:
                assert self.discord_webhook_url is not None
                headers = {'Content-Type': 'application/json'}
                payload = {'username': title, 'content': text}
                response = requests.post(self.discord_webhook_url,
                                         headers=headers,
                                         json=payload
                                         )
                return response.ok


class Line:
    """LINE 通知モジュール
    """

    def __init__(self):
        """初期化
        Args:
            logger ([type]): [description]
        """
        self.use_module = True
        self.lock = threading.Lock()
        config_filename = 'config/line.json'
        if os.path.isfile(config_filename):
            with open(config_filename, 'r') as r:
                self.line_access_token = json.load(r)['line_access_token']
        else:
            self.use_module = False
            logger.warning('[LINE] 通知は無効です。')

    def send(self, text):
        """[summary]

        Args:
            message ([type]): [description]

        Returns:
            [type]: [description]
        """

        url = 'https://notify-api.line.me/api/notify'
        headers = {'Authorization': 'Bearer ' + self.line_access_token}
        payload = {'message': text}
        response = requests.post(url, headers=headers, params=payload)

        return response.json()


class Twitter:
    """Twitter 通知モジュール
    """

    def __init__(self):
        """初期化
        Args:
            logger ([type]): [description]
        """
        self.use_module = True
        self.lock = threading.Lock()
        config_filename = 'config/twitter.json'
        if os.path.isfile(config_filename):
            with open(config_filename, 'r') as f:
                config = json.load(f)
                self.twitter_ck = config['twitter_ck']
                self.twitter_cs = config['twitter_cs']
                self.twitter_at = config['twitter_at']
                self.twitter_ats = config['twitter_ats']
        else:
            self.use_module = False
            logger.warning('[Twitter] 通知は無効です。')

    def send(self, text):
        twitter = OAuth1Session(
            self.twitter_ck, self.twitter_cs, self.twitter_at, self.twitter_ats)
        payload = {"status": text}
        req = twitter.post(
            "https://api.twitter.com/1.1/statuses/update.json", params=payload)
        return req.ok


class MonitorClient:
    """監視クライアント
    """

    def __init__(self, keyword: str, price_min: int, price_max: int,
                 gmail: Union[None, Gmail],
                 alertzy: Union[None, Alertzy],
                 discord: Union[None, Discord],
                 line: Union[None, Line],
                 twitter: Union[None, Twitter]):
        """初期化
        Args:
            keyword (str): [description]
            price_min (int): [description]
            price_max (int): [description]
            gmail (Union[None, Gmail]): [description]
            alertzy (Union[None, Alertzy]): [description]
            discord (Union[None, Discord]): [description]
            line (Union[None, Line]): [description]
            twitter (Union[None, Line]): [description]
        """
        self.keyword = keyword
        self.price_min = price_min
        self.price_max = price_max
        self.gmail = gmail
        self.alertzy = alertzy
        self.discord = discord
        self.line = line
        self.twitter = twitter
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.mercari = Mercari()
        self.rakuma = Rakuma()
        self.persisted_items = []

    def join(self):
        """スレッド待機
        """
        self.thread.join()

    def start_monitoring(self):
        """監視開始
        """
        self.thread.start()

    def scrape_outstanding_items(self):
        """未処理の商品をクリーンアップ
        """

        # メルカリとラクマから全検索
        for backend in [self.mercari, self.rakuma]:
            items = backend.fetch_all_items(
                keyword=self.keyword,
                price_min=self.price_min,
                price_max=self.price_max,
                max_items_to_fetch=100
            )

            # 上手いことマージさせる
            self.persisted_items.extend(items)

            # ログを流す
            logger.info(f'[{backend.name}] {len(items)} 個の商品が見つかりました。')
        logger.info(f'合計 {len(self.persisted_items)} 個の商品が見つかりました。')

    def check_for_new_items(self):
        """新商品を見つける
        """
        # メルカリとラクマから全検索
        for backend in [self.mercari, self.rakuma]:

            # 最初のページだけ
            items_on_first_page, _ = backend.fetch_items_pagination(
                keyword=self.keyword,
                price_min=self.price_min,
                price_max=self.price_max
            )

            # 配列を比較し、新商品の差分を出す
            new_items = set(items_on_first_page) - set(self.persisted_items)

            # 新商品分、通知をする
            for new_item in new_items:

                # ログを流す
                logger.info(f'[{self.keyword}] 新商品が見つかりました: {new_item}')

                # 保存
                self.persisted_items.append(new_item)

                # 商品情報取得
                item = backend.get_item_info(new_item)

                # 送信データ
                title = f'{item.name} {item.price}'
                email_subject_with_url = f'{title} {item.url}'
                email_content = f'{item.url}<br/><br/>{item.desc}'
                text = f'{item.url} {item.desc}'
                attachment = item.local_url

                # 各サービスに通知する

                # Alertzy
                if self.alertzy is not None:
                    res = self.alertzy.send(email_subject_with_url,
                                      title=self.keyword)

                # Gmail
                if self.gmail is not None:
                    self.gmail.send(title, email_content, attachment)

                # Discord
                if self.discord is not None:
                    self.discord.send(title, text)

                # LINE
                if self.line is not None:
                    self.line.send(title, text)

                # Twitter
                if self.twitter is not None:
                    self.twitter.send(title, text)

    def run(self):
        """スレッド処理
        """

        # ログを流す
        logger.info(f'[{self.keyword}] 監視を開始しました: 上限 {self.price_max} 円'
                    f'下限: {self.price_min} 円')

        # クリーンアップ
        self.scrape_outstanding_items()

        # 監視秒数
        time_between_two_requests = 30

        # ログを流す
        logger.info(f'最初のページのみを {time_between_two_requests} 秒毎に監視し、通知します。'
                    f'新商品が見つかったときも通知します。')
        logger.info('監視を開始しています...')

        # スレッドループ
        while True:
            sleep(time_between_two_requests)
            try:
                # 新商品検索
                self.check_for_new_items()
            except Exception:
                wait = 30
                logger.exception(f'例外エラーが発生しました。{wait}ms 待機します。')
                sleep(wait)


def init_logging():
    """ログ関連の初期化
    """
    format_str = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format_str)
    log_filename = 'monitor.log'
    print(f'ログ保存ファイル: [{log_filename}]')

    logging.basicConfig(
        format=format_str,
        filename=log_filename,
        level=logging.INFO
    )
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def main():
    """メインプロセス起動
    """

    # ログ関連の初期化
    init_logging()

    # コマンドライン引数の取得
    args = get_script_arguments()

    # キーワードを配列化
    keywords = args.keywords.strip().split(',')

    # 価格範囲を配列化
    max_prices = [int(v) for v in args.max_prices.strip().split(',')]
    min_prices = [int(v) for v in args.min_prices.strip().split(',')]

    # なんやかんや
    assert len(min_prices) == len(max_prices)
    assert all([m1 < m2 for m1, m2 in zip(min_prices, max_prices)])

    # 通知モジュール インスタンス生成
    gmail = None if args.disable_gmail else Gmail()
    alertzy = None if args.disable_alertzy else Alertzy()
    discord = None if args.disable_discord else Discord()
    line = None if args.disable_line else Line()
    twitter = None if args.disable_line else Twitter()

    # モニターインスタンス 格納配列
    monitors = []

    # モニターインスタンスをキーワード分だけ生成
    for keyword, min_price, max_price in zip(keywords, min_prices, max_prices):
        monitors.append(MonitorClient(keyword.strip(), min_price,
                        max_price, gmail, alertzy, discord, line, twitter))

    # 全てのモニターを起動
    for monitor in monitors:

        # 起動
        monitor.start_monitoring()

        # 適当に遅延
        sleep(5)

    # モニターを永遠に待機させる
    for monitor in monitors:
        monitor.join()


if __name__ == '__main__':
    main()