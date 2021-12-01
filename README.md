# yasugai
メルカリとラクマの商品を価格とキーワードから絞り込み、新商品を通知してくれる監視モニターです。欲しい物を安買いしたいときに役立ちます。

## 通知対応サービス
- `Discord`
- `Twitter`
- `LINE`
- `Gmail`
- `Alertzy`

## ダウンロード方法
`git clone` でダウンロードすることを推奨しています。`git pull` で更新できるのでおすすめです。

## セットアップ
まずはじめに、通知に使用したいサービスを選定し、[/config](./config) 内に置いてあるテンプレートファイル (.example.json) を適宣書き換えてください。

#### ① おまかせ環境
[requirements.txt](./requirements.txt) に記載されている依存関係をインストールしてください。

- 起動: `python monitor.py --keywords "RTX3070,RTX3080" --min_prices "0,10" --max_prices "50000,100000"`

#### ② Docker 環境
- ビルド: `docker-compose build`
- 起動: `docker-compose run app monitor.py --keywords "RTX3070,RTX3080" --min_prices "0,10" --max_prices "50000,100000"`
  - `-d` を付けることでデタッチモードで起動することができます。

#### 監視間隔秒数
[config/settings.json](./config/settings.json) にて設定可能な `monitor_interval_seconds` の値です。

## ログファイル
`monitor.log` にログデータが保存される仕様です。

## Licence
MIT.
