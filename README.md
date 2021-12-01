# yasugai
メルカリとラクマの商品を価格とキーワードから絞り込み、新商品を通知してくれる監視モニターです。欲しい物を安買いしたいときに役立ちます。

## 通知対応サービス
- `Discord`
- `Twitter`
- `LINE`
- `Gmail`
- `Alertzy`

## セットアップ

#### ① おまかせ環境
[requirements.txt](./requirements.txt) に記載されている依存関係をインストールしてください。

- 起動: `python monitor.py --keywords "RTX3070,RTX3080" --min_prices "0,10" --max_prices "50000,100000"`

#### ② Docker 環境
- ビルド: `docker-compose build`
- 起動: `docker-compose run app python monitor.py --keywords "RTX3070,RTX3080" --min_prices "0,10" --max_prices "50000,100000"`
  - `-d` を付けることでデタッチモードで起動することができます。

## ログファイル
`monitor.log` にログデータが保存される仕様です。

## Licence
MIT.