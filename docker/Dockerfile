# warehouse用Dockerfile by N.Goto

# 使用するベースイメージ。（最新版の一つ前のバージョンとする）
FROM python:3.13-slim

# 1. 環境変数の設定
# stdoutへの出力をバッファリングさせない。(errorやlogを直ちに出力して欲しいから)
ENV PYTHONUNBUFFERED=1
# Permission deniedのエラーが出る場合、下記を有効にしてみる。
# RUN mkdir /code && chown -R ${UID}:${GID} /code
# /code/ディレクトリを作業用ディレクトリにする。
WORKDIR /code

# 2. システムライブラリのインストール
# build-essential（コンパイル用）とフォントをまとめてインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 3. Pythonライブラリのインストール
# 先にrequirementsだけコピーすると、コードを書き換えてもキャッシュが効いて高速です
COPY requirements /code/requirements
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/prod.txt

# # 4. アプリケーションコードのコピー
# ホスト上のdjangoアプリ、データベースファイルなどを/code/ディレクトリにコピーする。
# しかしCOPYコマンドでは、親ディテクトリはコピーできないので、docker-composeでmountする。
# または、Dockerfileを親ディレクトリと同じ階層に配置して、djangoソースをコンテナ内にコピーする。
# COPY . /code/
