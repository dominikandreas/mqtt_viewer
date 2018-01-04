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


