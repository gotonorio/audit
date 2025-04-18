マンション会計システムKuraselの監査用システム

### 工事中 2025-03-03

### 1．初期設定

1. プロジェクト層にlogs、backupDBという名前で空ディレクトリを作っておく。
2. python management.py migrateを行う。
    - migrateに失敗する場合は、マイグレーションファイルを全て削除する。
3. createsuperuserで管理者ユーザを作成する。
4. private_settings.pyにSECRET_KEYを記述して、settings.pyと同じ階層に置いてください。
    - SECRET_KEY = '**************'
5. 管理者でログインして、コントロールレコードの仮登録を有効にセットする。

### 2． 管理画面での設定（管理画面上で行う）
 管理画面で下記の必要な設定を行う。

##### (1) groupとパーミッションの作成
管理者画面で以下のgroupとpermissionを作成する。

- chairman（ユーザ管理・データ管理）
    - register|ユーザー|Can add user
    - record|transaction|Can add transaction
    - record|transaction|Can view transaction
    - budget|expense budget|Can view expensebudget
- data_manager（データ管理・個人情報閲覧可能）
    - record|transaction|Can add transaction
    - record|transaction|Can view transaction
    - budget|expense budget|Can view expensebudget
- director（個人情報以外閲覧可能）
    - record|transaction|Can view transaction
    - budget|expense budget|Can view expensebudget
- login（公開情報のみ閲覧可能）
    - budget|expense budget|Can view expensebudget

##### (2) コントロールの初期設定

- 仮登録メニューを表示するため、「コントロールレコード」を1つだけ追加作成する。


##### (3) 口座情報の登録(RECORD.Banks、RECORD.Accounts)

- Kuraselでは1つの口座を使いますので、Kuraselの資産管理画面を参考に「Banks」「Accounts」を登録する。
- Accountsでは「口座名（分かりやすい名前）」1つだけ設定する。

##### (4) 会計区分マスタの登録(RECORD.Accounting class)

- 「管理費会計」「修繕積立金会計」「駐車場会計」「町内会/自治会会計」など必要な会計区分を登録する。


### マスタデータの設定（プログラム上で行う）

##### (1) 費目マスタの登録

- 費目マスタを登録する前には、会計区分マスタが登録されている必要があります。以下は例です。
    - 管理費会計
    - 修繕積立金会計
    - 駐車場会計
    - 町内会費会計（自治会費会計）
- Kuraselで登録された「費目」を登録してください。
    - Kuraselの「費目」は、各会計区分の「収支状況」で「収入の部」「支出の部」で確認できます。
    - defaultとしての「費目」（is_defaultをcheck）を1つだけ設定してください。費目名は「不明」など自由でOKです。
    - 会計区分が異なっていても、同じ費目名は登録できません。
- 費目マスタの登録がない場合、Kuraselデータの取り込みができません。
- 費目マスタをcsvファイルから登録することもできます。
- csvファイルは「会計区分名」「費目コード」「費目名」の3列データです。
- csvで読み込んだ後は、以下の各フラグの修正をしてください。
    - 入金費目フラグ（入金費目ならチェックする）
    - 有効フラグ（使わなくなった費目はチェックを外す）
    - 集計フラグ（前受金以外はチェックする）
    - 承認必要フラグ（理事長の支払い承認が必要な費目はチェックする）
- 必要な「費目」を登録した

##### (2) 貸借対照表 科目マスタの登録

- Kuraselの貸借対照表で使われる「項目」（ex. 資産保持用の銀行口座名、未収金、未払金など）を会計区分毎に登録。

##### (3) 振込依頼者名の登録

- Kuraselの「入出金明細データ」取込時に費目を推定するための「振込依頼者名」を登録する。



