var chart;

function clearCanvas(){
    // canvas要素を取り出す。
    const canvas = document.getElementById("stage");
    if (!canvas.getContext) {
        return;
    }
    const existingChart = Chart.getChart(canvas);
    if (existingChart) {
        existingChart.destroy();
    }
}
/*
****************************************************************
* 多次元配列による予算実績対比グラフ表示 by N.Goto
****************************************************************
*/
function createBudgetActualChart(data){
    // (1) chart.jsのdataset用の配列を用意。
    var xLabels = [], budget = [], actual = [];

    for (const row of data) {
        xLabels.push(row[0]);
        budget.push(row[1]);
        actual.push(row[2]);
    }
    // (2) データオブジェクトを用意。
    const chartData = {
        labels: xLabels,                 // x軸ラベル配列。
        datasets: [
            {
                label: '予算',           // 凡例ラベル
                backgroundColor: "grey",
                borderColor: "grey",    // 線の色
                borderWidth: 1,         // 線の太さ
                // borderRadius: 2,        // 棒の角を少し丸くする
                data: budget,
            },
            {
                label: '実績',           // 凡例ラベル
                backgroundColor: "red",
                borderColor: "red",     // 線の色
                borderWidth: 1,         // 線の太さ
                // borderRadius: 2,        // 棒の角を少し丸くする
                data: actual,
            },
        ]
    };
    // (3) チャートオプション
    const myChartOption = {
        // canvasサイズを固定する。(trueの場合windowの大きさに連動する)
        responsive:true,
        // コンテナの幅に合わせて比率を維持する
        maintainAspectRatio: true,
        // 比率の設定　2:3（幅が高さの1.5倍）にしたいので「1.5」を指定
        aspectRatio: 1.5,
        // 横棒グラフとする
        indexAxis: 'y',

        plugins: {
            title: {
                display: false,
                font:{size:14},
                text: '工事費支出グラフ'
            },
            legend: {   // 凡例
                display: true,
                labels: { boxWidth: 10, padding: 20 }
            },
            tooltip: {
                enabled: true,
                mode: 'index',
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
            },
        },
        scales: {
            x: { // 値軸
                beginAtZero: true,
                ticks: {
                    color: "black",
                    callback: function(value) { 
                            return value.toLocaleString();
                        }
                    },
                title: {
                    display: true,
                    text: '支出金額 (円)'
                }
            },
            y: { // カテゴリ軸
                grid: { display: false },
                title: {
                    display: true,
                    text: '工事種別'
                }
            }
        }
    }

    // (4) チャート描画。
    clearCanvas();
    chart = new Chart(document.getElementById('stage'), {
        type: 'bar',  
        data: chartData,
        options: myChartOption
    });
}
