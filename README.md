# Katashina DEM Analysis (Geo walker Part3)

## 概要
本リポジトリは、GIS 分析（DEM 取得・結合・勾配計算など）の再現コードを含みます。

コードを実行する前に、地理院データの取得および環境構築が必要です。

## 確認環境

- Python 3.14
- macOS 15
- [uv](https://github.com/astral-sh/uv) 0.8.23


### setup

```console
% brew install gdal
% uv sync
```

### uv.lock のレジストリURLを正規化する

Takumi Guard プロキシ経由で `uv sync` を実行すると `uv.lock` 内のURLが `pypi.flatt.tech` に書き換わる。ハッシュ検証が効くためコミットされたURLがプロキシである必要はなく、PyPI公式URLに戻しておくと差分レビューしやすい。コミット前に以下を実行する。

```console
% sed -i '' \
    -e 's|https://pypi.flatt.tech/files/packages|https://files.pythonhosted.org/packages|g' \
    -e 's|https://pypi.flatt.tech/simple|https://pypi.org/simple|g' \
    uv.lock
```

## ノートブックをMarkdownとして書き出す

論文や外部ドキュメントに埋め込みやすいよう、Jupyter Notebook を出力（図・テキスト結果）込みで Markdown に書き出せます。`docs/` 配下に `.md` と画像ファイルが生成されます。

```console
% uv run jupyter nbconvert --to markdown --output-dir docs 片品村.ipynb
```

生成物:

- `docs/片品村.md` — コードセル + テキスト出力 + 画像参照
- `docs/片品村_files/` — matplotlib 出力の PNG 画像

`docs/` ディレクトリごとコピーすれば画像参照が壊れずに移植できます。
