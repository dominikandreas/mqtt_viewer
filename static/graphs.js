class LineGraph{
    constructor(container, socket, name, hide_legend){
        this.chart = Highcharts.chart(container, {
            title: { text: name },
            xAxis: { type: 'datetime' },
            yAxis: { visible: !hide_legend},
            legend: {
                enabled: !hide_legend,
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle'
            },

            plotOptions: {  line: {  animation: false } },
            series: [],
            credits: { enabled: false },
            navigation: {
                buttonOptions: { enabled: !hide_legend }
            }
        });
        
        this.name = name;

        this.reload_data();

        this.socket = socket;
        this.socket.on('connect', function() {
            socket.emit('connected', {data: "I'm connected!"});
        });
        this.socket.on(this.name+'_view_update', this.append_data.bind(this));
    }

    append_data(e){
        console.log('[view_update]: ' + JSON.stringify(e));
        if (e.resolution === window.get_param("resolution", "seconds")){
            let series = undefined;
            for (let i=0; i<this.chart.series.length; i++)
                if (this.chart.series[i].name === e.name)
                    series = this.chart.series[i];
            if (series !== undefined){
                series.addPoint([e.data[0], e.data[1]], true, series.data.length>600, false);
            }else{
                console.log("missing series: ", e.name);
            }
        }
    }

    reload_data (){
        const req = new XMLHttpRequest();

        req.onreadystatechange = function () {
            if (req.readyState !== 4 || req.status !== 200) return;
            this.show_data(JSON.parse(req.responseText));
        }.bind(this);
        const resolution = window.get_param('resolution=', 'seconds');
        req.open("GET", "data?resolution="+resolution+"&graph_name="+this.name, true);
        req.send(null);
    };

    show_data(data){
        const seriesLength = this.chart.series.length;
        for(let i = seriesLength -1; i > -1; i--) {
            this.chart.series[i].remove();
        }
        for (let i= 0; i<data.length; i++){
            this.chart.addSeries({type:"line", data:data[i].data, name:data[i].name});
        }
    };

}

window.set_param = function(name, value){
    let url = window.location.href;
    if(value == null)
        value = '';
    const pattern = new RegExp('\\b('+name+'=).*?(&|$)');
    if(url.search(pattern)>=0){
        return url.replace(pattern,'$1' + value + '$2');
    }
    url = url.replace(/\?$/,'') + (url.indexOf('?')>0 ? '&' : '?') + name + '=' + value;
    window.location.replace(url);
    location.reload();
    return false;
};

window.get_param = function(name, default_value){
    const value = location.search.split('resolution=')[1];
    return value === undefined ? default_value : value;
};


