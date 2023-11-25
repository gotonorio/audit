マンション会計システムKuraselの監査用システム

### 工事中

### 1．初期設定

- プロジェクト層にlogs、bbackupDBという名前で空ディレクトリを作っておく。
- マイグレーションファイルを全て削除する。
- makemigrationsとmigrateを行う。
- createsuperuserで管理者ユーザを作成する。
- settings.pyの管理組合毎の定数を設定する。
    - 未収金額
    - 前受金額
    - 未払金額

### 2． 管理画面での設定（管理画面上で行う）
 管理画面で下記の必要な設定を行う。

##### (1) groupとパーミッションの作成
管理者画面で以下のgroupとpermissionを作成する。

- chairman
    - register|ユーザー|Can add user
    - record|transaction|Can add transaction
    - record|transaction|Can view transaction
- data_manager
    - record|transaction|Can add transaction
    - record|transaction|Can view transaction
- director
    - record|transaction|Can view transaction

##### (2) コントロールの初期設定

- 仮登録メニューを表示するため、管理画面で1個だけレコードを作成する。


##### (3) 口座情報の登録

- Kuraselでは1つの口座を使いますので、Kuraselの資産管理画面を参考に「銀行」「口座名」「口座番号」等を登録する。

##### (4) 会計区分マスタの登録

- 「管理会計」「修繕会計」「駐車場会計」「町内会/自治会会計」など必要な会計区分を登録する。


### マスタデータの設定（プログラム上で行う）

##### (1) 費目マスタの登録

- Kuraselで登録した「費目」を登録してください。
- 費目マスタの登録がない場合、Kuraselデータの取り込みをスキップします。
- 費目マスタをcsvファイルから登録することもできます。
- csvファイルは「会計区分名」「費目コード」「費目名」の3列データです。
- csvで読み込んだ後は、以下の各フラグの修正をしてください。
    - 入金費目フラグ（入金費目ならチェックする）
    - 有効フラグ（使わなくなった費目はチェックを外す）
    - 集計フラグ（前受金以外はチェックする）
    - 承認必要フラグ（理事長の支払い承認が必要な費目はチェックする）

##### (2) 貸借対照表 科目マスタの登録

- Kuraselの貸借対照表で使われる「項目」（ex. 資産保持用の銀行口座名、未収金、未払金など）を会計区分毎に登録。

##### (3) 振込依頼者名の登録

- Kuraselの「入出金明細データ」取込時に費目を推定するための「振込依頼者名」を登録する。



