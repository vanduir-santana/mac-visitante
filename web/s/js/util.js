/*
author: Vanduir Santana
version: 0.8
*/
function timeToStr(s, arred_sec, exibir_h) {
  var h, m, s;
  
  h = Math.floor(s / 3600);
  s = s % 3600;

  m = Math.floor(s / 60);
  s = s % 60;
  if (!arred_sec) {
    s = Math.floor(s);
  }

  var str;
  if (h == 0 && !exibir_h) {
    str = '';  // nao exibe hora se nao existir
  } else if (h < 10) {
    str = '0' + h + ':';
  } else {
    str = h + ':';
  }

  if (s == 60) {
    s = 0; 
    m += 1; 
  }

  if (m < 10) m = '0' + m;

  if (s < 10) {
    if (!arred_sec) {
      s = '0' + s;
    } else {
      s = '0' + s.toFixed(3);   // arred. pra 3 casas (legenda vtt) 
    }
  } else if (arred_sec) {       // maior q 10 mais tem q arredondar pra 3 (caso contrario arredonda acima Math.floor)
    s = s.toFixed(3);
  }

  str += m + ':' + s;
  return str;
}

function getQueryParams(str) {
  str = str.substring(str.indexOf('?') + 1);
  
  var params = {}; 
  var partes = str.split('&');
  partes.forEach(function (parte) {
    var par = parte.split('=');
    par[0] = decodeURIComponent(par[0]);
    par[1] = decodeURIComponent(par[1]);
    params[par[0]] = ( par[1] !== 'undefinied' ) ? par[1] : true;
  });
  return params;
}

function getQueryParams2(str) {
  // pega parametros e comando
  var cmd = getQueryCmd(str);
  r = getQueryParams(str);
  r['cmd'] = cmd;
  return r;
}

function getQueryCmd(str) {
  var pos = str.indexOf('?');
  if (pos == -1) {
    return str;
  } else {
    return str.substring(0, pos);
  }
}

// altera parametro na url
function setParam(search, key, val){
  var newParam = key + '=' + val,
      params = '?' + newParam;

  // If the "search" string exists, then build params from it
  if (search) {
    // Try to replace an existance instance
    params = search.replace(new RegExp('([?&])' + key + '[^&]*'), '$1' + newParam);

    // If nothing was replaced, then add the new param to the end
    if (params === search) {
      params += '&' + newParam;
    }
  }
  return params;
};

function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
}

function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i=0; i<ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1);
        if (c.indexOf(name) == 0) return c.substring(name.length,c.length);
    }
    return "";
}

/////////////////////////////////////////////
// AJAX
function ajax(url, fn, metodo, tipo, dados) {
    /* Faz chamada ajax onde:
     * url: endereco a ser requisitado incluindo parametros
     * fn: funcao de callback
     * metodo: = "GET" ou "POST"
     * tipo: por enquanto soh json
     * dados: definir quando tipo = json. Tem q estar no formato JSON
    */
    var req = new XMLHttpRequest();
    req.onreadystatechange = function() {
      if (req.readyState == 4 && req.status == 200) {
          fn(req.responseText); // sucesso
      }
      // implementar erro (status != 200)
    };
    /*req.onloadend = function() {
      // terminou de carregar, enviou JSON
      if (req.readyState == 4 && req.status == 200) {
        fn(req.responseText);
      }
      // implementar erro (status != 200)
    };*/

    req.open(metodo, url, true);
    if (tipo === "json") {
        // muda cabecalho
        req.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
        // por enquanto so foi testado utilizando post
        if (metodo = 'POST') {
          req.send(JSON.stringify(dados));
        } else {
          // quando utilizar GET com json eh preciso executar JSON.stringify nos parametros da url
          req.send();
        }
    } else {
      req.send();
    }
}

// envia no formato JSON
//function

// FIM AJAX
