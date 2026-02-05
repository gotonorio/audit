//
// データの一括削除の確認用JavaScript
function confirmAndSubmit(year, month, className) {
    const message = `${year}年${month}月の「${className}」データを削除します。よろしいですか？`;
    if (confirm(message)) {
        document.getElementById('delete-form').submit();
    }
}