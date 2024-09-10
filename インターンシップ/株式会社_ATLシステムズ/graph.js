
// csvファイルをjsonファイルに変換
function load_data(txt) {
  $.ajax({
    url: "./data/data.csv",
    type: "GET",
  })
    .done("data", function (data) {
      const send_data = Papa.parse(data, { header: true, dynamicTyping: true });
      // pie_graph関数にデータを渡し描画
      pie_graph(send_data.data,txt);
    })
    .fail(function (data) {
      return null;
    });
}

function pie_graph(data,txt) {
  var width = 600;
  var height = 450; 
  var radius = Math.min(width, height - 50) / 2 - 10; 

  var svg = d3
    .select("#pie_graph")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  svg.append("text")
     .attr("x", width/2)
     .attr("y", 30) 
     .attr("text-anchor", "middle")
     .style("font-size", "18px") 
     .style("font-weight", "bold")
     .text(txt);

  // (0,0)が円の中心になっており、1/4しか表示されないため中心を移動
  g = svg
    .append("g")
    .attr("transform", "translate(" + width/2 + "," + (height / 2 + 20) + ")");

  // 色分け
  var color = d3.scaleOrdinal(d3.schemeCategory10);

  // パーセント表示のために合計を計算
  var total = d3.sum(data, function(d) {
    return d.val
  });
  
  // pie関数でデータを円グラフの形式に変換
  var pie = d3
    .pie()
    .value(function (d) {
      return d.val;
    })
    .sort(null);
  // pieクラスを選択し、データと関連付け、新しい要素gを作成しpieクラスを付与する
  var pieGraph = g
    .selectAll(".pie")
    .data(pie(data))
    .enter()
    .append("g")
    .attr("class", "pie");
  
  // 外側を半径の値内を中心で設定し、円の形状を定義
  var arc = d3.arc()
              .outerRadius(radius)
              .innerRadius(0);

  // pathに対して形状,色,透明度,境界線を設定
  pieGraph
    .append("path")
    .attr("d", arc)
    .attr("fill", function (d) {
      return color(d.index);
    })
    .attr("opacity", 1)
    .attr("stroke", "white");
  
  // ラベルの位置を設定
  var text = d3
    .arc()
    .outerRadius(radius - 40)
    .innerRadius(radius - 40);
  
  // テキストを追加し、表示
  pieGraph
    .append("text")
    .attr("fill", "black")
    .attr("transform", function (d) {
      return "translate(" + text.centroid(d) + ")";
    })
    .attr("dy", "5px")
    .attr("font-size", "10px")
    .attr("text-anchor", "middle")
    .text(function (d) {
      return d.data.key;
    });
  
  // パーセントをラベル(カラム)の下に表示
  pieGraph
    .append("text")
    .attr("fill", "black")
    .attr("transform", function (d) {
      return "translate(" + text.centroid(d) + ")";
    })
    .attr("dy", "2em")  
    .attr("font-size", "10px")
    .attr("text-anchor", "middle")
    .text(function (d) {
      var percentage = (d.value / total * 100).toFixed(1);  // 小数点以下1桁まで表示
      return percentage + "%";
    });
}

load_data("タイトル");