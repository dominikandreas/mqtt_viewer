
window.chart = Highcharts.chart('container', {
    title: { text: '' },
    xAxis: { type: 'datetime' },
    yAxis: { },
    legend: {
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle'
    },

    plotOptions: {  line: {  animation: false } },
    series: [],
});

window.set_param = function(name, value){
    var url = window.location.href;
    if(value == null)
        value = '';
    var pattern = new RegExp('\\b('+name+'=).*?(&|$)')
    if(url.search(pattern)>=0){
        return url.replace(pattern,'$1' + value + '$2');
    }
    url = url.replace(/\?$/,'') + (url.indexOf('?')>0 ? '&' : '?') + name + '=' + value
    window.location.replace(url);
    location.reload();
    return false;
}

window.get_param = function(name, default_value){
    var value = location.search.split('resolution=')[1];
    return value == undefined ? default_value : value;
}

window.show_data = function(data){
    var seriesLength = window.chart.series.length;
    for(var i = seriesLength -1; i > -1; i--) {
        window.chart.series[i].remove();
    }
    for (var i= 0; i<data.length; i++){
        window.chart.addSeries({type:"line", data:data[i].data, name:data[i].name});
    }
};

window.reload_data = function(){
    var req = new XMLHttpRequest();

    req.onreadystatechange = function () {
        if (req.readyState != 4 || req.status != 200) return;
        window.show_data(JSON.parse(req.responseText));
    };

    var name = location.search.split('name=')[1]
    var resolution = window.get_param('resolution=', 'seconds');
    req.open("GET", "data?resolution="+resolution+"&graph_name="+name, true);
    req.send(null);
};


window.reload_data();

window.socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function() {
    socket.emit('connected', {data: 'I\'m connected!'});
});

socket.on(window.graph_name+'_view_update', function(e){
    console.log('[view_update]: ' + JSON.stringify(e));
    if (e.resolution == window.get_param("resolution", "seconds")){
        series = undefined;
        for (var i=0; i<window.chart.series.length; i++)
            if (window.chart.series[i].name == e.name)
                series = window.chart.series[i];
        if (series != undefined){
            series.addPoint([e.data[0], e.data[1]], true, series.data.length>600, false);
        }else{
            console.log("missing series: ", e.name);
        }
    }
});