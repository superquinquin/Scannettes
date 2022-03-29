

function get_browser_id() {
  var browser;
  let ua = navigator.userAgent.toLowerCase();
  let Sys = {};
  let s;
  (s = ua.match(/msie ([\d.]+)/)) ? Sys.ie = s[1] :
  (s = ua.match(/firefox\/([\d.]+)/)) ? Sys.firefox = s[1] :
  (s = ua.match(/chrome\/([\d.]+)/)) ? Sys.chrome = s[1] :
  (s = ua.match(/opera.([\d.]+)/)) ? Sys.opera = s[1] :
  (s = ua.match(/version\/([\d.]+).*safari/)) ? Sys.safari = s[1] : 0;

  if (Sys.ie) browser = 'IE: ' + Sys.ie;
  if (Sys.firefox) browser = 'Firefox: ' + Sys.firefox;
  if (Sys.chrome) browser = 'Chrome: ' + Sys.chrome;
  if (Sys.opera) browser ='Opera: ' + Sys.opera;
  if (Sys.safari) browser = 'Safari: ' + Sys.safari;

  return browser
}

function get_parent_id(element, level, type) {
  while (level-- > 0) {
    element = element.parentElement;
  }
  if (type == 'i') {
    return element.rowIndex;
  } else if (type == 'id') {
    return element.id;
  }
}


function header_traduction(trad, tableID) {
  let table = document.getElementById(tableID)

  for (var i=0; i < trad.length;i++) {
    table.rows[0].cells[i].innerHTML = trad[i]
  }
}