# 使用するベースイメージ。
FROM python:3.13-slim
# stdoutへの出力をバッファリングさせない。(errorやlogを直ちに出力して欲しいから)
ENV PYTHONUNBUFFERED 1
# コンテナ環境にホストのマウント用にディレクトリを作成する。
RUN mkdir /code
# /code/ディレクトリを作業用ディレクトリにする。
WORKDIR /code
# requirements.txtファイルを/code/ディレクトリにコピーする。
COPY requirements.txt /code/
# pipでpythonパッケージをインストールする。
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --requirement requirements.txt
# ホスト上のdjangoアプリ、データベースファイルなどを/code/ディレクトリにコピーする。
# しかしCOPYコマンドでは、親ディテクトリはコピーできないので、docker-composeでmountする。
# または、Dockerfileを親ディレクトリと同じ階層に配置して、djangoソースをコンテナ内にコピーする。
# COPY . /code/
