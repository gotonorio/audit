# warehouse用Dockerfile by N.Goto

# 使用するベースイメージ。（最新版の一つ以上前のバージョンとする）
FROM python:3.11-slim

# 1. 環境変数の設定
# stdoutへの出力をバッファリングさせない。(errorやlogを直ちに出力して欲しいから)
ENV PYTHONUNBUFFERED=1

# 2. dockerコンテナのユーザ作成
ARG UID=1001
ARG GID=1001

# 3. システムライブラリのインストール（root権限が必要）
# build-essential（コンパイル用）とフォントをまとめてインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 4. ユーザ作成
RUN groupadd -g ${GID} appuser \
    && useradd -m -u ${UID} -g ${GID} appuser

# 5. /code/ディレクトリを作業用ディレクトリにする。
WORKDIR /code

# 6. Pythonライブラリのインストール
# 先にrequirementsだけコピーすると、コードを書き換えてもキャッシュが効いて高速です
COPY docker/requirements /code/requirements
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements/prod.txt

# 7. アプリケーションコードのコピー
# ホスト上の「django関連ファイル」を作業用ディレクトリ/code/にコピーする。
# データベースファイル、mediaなどは.djangoignoreで除外すること
# 注意することは、
# COPYコマンドでは、親ディテクトリはコピーできないので、compose.ymlのcontextをソース階層にする。
COPY . /code/

# 7. /codeの所有者をrootからappuserに変更する。
RUN chown -R ${UID}:${GID} /code

# 8. 最後にユーザの切り替え（COPYの後に切り替える)
USER appuser
