諸々の徳（ハディース集）② — QC修正版

閲覧・編集用の完成ファイル
qc_v1/output/ja_ketab_elfadael_corrected.pdf   閲覧用PDF、30ページ
qc_v1/output/ja_ketab_elfadael_corrected.docx  編集用Word、ネイティブ脚注58件
qc_v1/output/ja_ketab_elfadael_corrected.txt   UTF-8全文テキスト
qc_v1/output/ja_ketab_elfadael_corrected.json 原本と修正後の文言、行ID、脚注、伝承出現箇所

原本全25ページの内容を保持し、本文・脚注10項目と見出し分類2箇所の修正を反映しました。
修正前後と根拠URLはPDF・Word・TXTの巻末、およびcorrections.jsonに記載しています。
脚注47に対応する剰余物の句の修訳と、脚注50に対応する天使の句の補足は、AIによる追加編集として明示しています。
原著者・原訳者の表記は原本に基づきます。今回の追加編集は原本の翻訳者による変更ではありません。

確認した範囲
原本25ページ、621の文字単位、脚注1〜58、57の伝承出現箇所、主要ハディース集への93件の参照。
最終PDF全30ページの表示確認と、Word/PDFの全文・脚注の内容保持を検証しました。
全文の学術的な逐語訳監修ではありません。二次的校訂集の4参照番号1957、2280、2379、1300は未照合です。
補足した天使の句を原本が省略した意図は未確定です。

原本と抽出記録
upload/ja_ketab_elfadael.pdf                     原本PDF、変更なし
output/ja_ketab_elfadael/                        修正前の文字抽出・検証記録
qc_v1/reviews/                                 原本と参照番号の照合、完成版の表示確認記録
qc_v1/output/ja_ketab_elfadael_QC_report.*        QC結果と確認の限界
qc_v1/output/ja_ketab_elfadael_*validation.json  最終ファイル検証

データ上の注意
JSONのunit_idと座標は原本への参照です。修正版PDFの座標ではありません。
original_textは原本の抽出文字列、text/corrected_textはこの編集版の文字列です。
57の伝承出現箇所は重複排除していません。本文の通しハディース番号を新設していません。
原訳のAI利用状況は不明です。今回の2箇所の修訳・補足だけを該当フィールドで明示しています。
Bankへのインポート・公開は実施していません。

再生成用コード
qc_v1/build_corrected.py       修正版TXT/JSONと修正・QC記録の構築
qc_v1/build_documents.py       Word構築と脚注配置
qc_v1/verify_deliverables.py   Word/PDF内容保持の検証
qc_v1/finalize_package.py      最終パッケージ構築
コードは実施内容の記録として同梱しています。DOCXからPDFへの変換にはLibreOffice、Noto CJK/Arabicフォントが必要です。
PDFレンダリング画像とOCR中間画像は容量を抑えるためこのパッケージに同梱していません。
最終PDFは収録されており、レビュー記録に各ページ画像のSHA256を保持しています。
MANIFEST.jsonに同梱ファイルのSHA256を記録しています。
