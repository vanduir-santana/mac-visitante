<!doctype html>
<html lang="pt-BR">
<head>
<title>Liberar Visitantes</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
<link rel="stylesheet" href="/visitante/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
</head>
<body>
<div class="pricing-header px-3 py-3 pt-md-5 pb-md-4 mx-auto text-center">
  <h1 class="display-5">Liberar Internet Visitante</h1>
</div>

<div class="container">
  <div class="card-deck mb-3 text-center">
    <div class="card mb-4 shadow-sm">
      <div class="card-header">
        <h4 class="my-0 font-weight-normal">Aguardar conexões</h4>
      </div>
      <div class="card-body">
        <p class="lead">
        Clique no botão abaixo pra liberar Wi-Fi pra que os clientes ou visitantes conectem.
        </p>
        <div id="div-tempo">
          <h5 id="h5-tempo" class="my-0 font-weight-normal">00:00</h5>
        </div>
        <button type="button" id="btn_aguardar" disabled class="btn btn-lg btn-block btn-primary" onclick="btn_aguardar_click()">
          <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 
          Aguardar
        </button>
      </div>
    </div>
    <div class="card mb-4 shadow-sm">
       <div class="card-header">
        <h4 class="my-0 font-weight-normal">Visitantes Liberados</h4>
      </div>
      <div class="card-body">
        <p class="lead">
        Lista de visitantes liberados. Este recurso está sendo implementado!
        </p>
      </div>
    </div>
  </div>
</div>

<div id="div-log"
</div>

<script src="/visitante/js/jquery-3.4.1.slim.min.js" integrity="sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n" crossorigin="anonymous"></script>
<script src="/visitante/js/popper.min.js" integrity="sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo" crossorigin="anonymous"></script>
<script src="/visitante/js/bootstrap.min.js" integrity="sha384-wfSDF2E50Y2D1uUdj0O3uMBJnjuUD4Ih7YwaYd1iqfktj0Uod8GCExl3Og8ifwB6" crossorigin="anonymous"></script>
<script src="/visitante/js/util.js"></script>
<script type="text/javascript">
var tempo = 0;
var cont = 0;
var h5_tempo = document.getElementById('h5-tempo');
var div_log = document.getElementById('div-log');
var btn_aguardar = document.getElementById('btn_aguardar');
const url_tempo = '/visitante/tempo';
const url_solicitar_aguarde = '/visitante/solicitar_aguarde';
const url_solicitar_cancelamento = '/visitante/solicitar_cancelamento';
const url_existe_arq_aguarde = '/visitante/existe_arq_aguarde';
const T_AGUARDAR = 'Aguardar';
const T_CANCELAR = 'Parar';
const T_SPINNER = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
var timer_solicitacao_aguarde = {hnd: null, cb: timer_solicitacao_aguarde_cb, intervalo: 4000};
var timer_cont = {hnd: null, cb: timer_cont_cb, intervalo: 1000};
var timer_geral = {hnd: null, cb: timer_geral_cb, intervalo: 6000};
var contando = false;
var solicitando_aguarde = false;
var solicitando_cancelamento = false;
var t1 = null;        // calcular se teve atraso no timer, quando no android, por exemplo, é apertado o power
const debug = false;
const debug_console = true;


function obter_tempo() {
    tempo = 0;
    ajax(url_tempo,
         function(resp) {
            var r = JSON.parse(resp); 
            tempo = r.tempo;
            set_t1()
            iniciar_timer(timer_cont);
         },
         'GET');
}

function solicitar_aguarde() {
    solicitando_aguarde = true;
    ajax(url_solicitar_aguarde,
         function(resp) {
             var r = JSON.parse(resp);
             if (r.ok) {
                cont = 0;
                iniciar_timer(timer_solicitacao_aguarde);
             } else {
                aguarde_erro(r.erro);
             }
         },
         'GET');
}

function solicitar_cancelamento() {
    solicitando_cancelamento = true;
    ajax(url_solicitar_cancelamento,
         function(resp) {
             var r= JSON.parse(resp);
             if (r.ok) {
                 
             } else {
             }
         },
         'GET');
}

function existe_arq_aguarde() {
    ajax(url_existe_arq_aguarde,
         function(resp) {
             var r = JSON.parse(resp);
             if (!r.existe_arq_aguarde) {
                //// provavelmente a contagem foi cancelada por outro usuario
                if (contando) {
                    tempo = 0;    // para na proxima interacao de timer_cont
                    add_log('tempo = 0, parar timer_cont na proxima interacao!');
                    solicitando_cancelamento = false;
                }
             } else if (!contando) {
                // provavelmente foi iniciado aguarde por outro usuario
                add_log('obter_tempo()');
                obter_tempo();
             }
         },
         'GET');
}

var t_aguardar_spinner = T_SPINNER + ' ' + T_AGUARDAR;
var t_cancelar_spinner = T_SPINNER + ' ' + T_CANCELAR;
function btn_aguardar_click() {
    btn_aguardar.disabled = true;
    if (btn_aguardar.innerText == T_AGUARDAR || btn_aguardar.innerText == t_aguardar_spinner) {
        add_log('Aguarde...');
        //btn_aguardar.innerText = T_CANCELAR;
        btn_aguardar.innerHTML = t_cancelar_spinner;
        tempo = 0;
        cont = 0;
        solicitar_aguarde();
    } else {
        add_log('Cancelar...');
        //btn_aguardar.innerText = T_AGUARDAR;
        btn_aguardar.innerHTML = t_aguardar_spinner;
        solicitar_cancelamento();
    }
}

function iniciar_timer(timer) {
    nome_timer = timer.cb.name;
    if (!timer.hnd) {
        timer.hnd = setInterval(timer.cb, timer.intervalo);
        add_log(nome_timer + ' iniciado');
    } else {
        add_log(nome_timer + ' ja iniciado!');
    }
}

function parar_timer(timer) {
    nome_timer = timer.cb.name;
    if (timer) {
        if (timer.hnd) {
            clearInterval(timer.hnd);
            timer.hnd = null;
            add_log(nome_timer + ' parado!');
        } else {
            add_log(nome_timer + ' NAO parado, hnd = null');
        }
    } else {
        add_log('Nao foi possivel parar o ' + nome_timer + ' pq ele nao ta setado!');
    }
}

function timer_cont_cb() {
    //if (solicitando_aguarde) {
    if (solicitando_aguarde || solicitando_cancelamento ) {
        btn_aguardar.disabled = true;
        //add_log('Solicitando aguarde: nao executa rotina do timer_cont!');
        set_t1(); 
        return;
    //} else if (solicitando_cancelamento) {
    //    btn_aguardar.disabled = true;
    //    //add_log('Solicitando cancelamento: nao executa rotina do timer_cont!');
    //    return;
    } else {
        btn_aguardar.disabled = false;
    }
    if (tempo == 0) {
        parar_timer(timer_cont);
        btn_aguardar.innerText = T_AGUARDAR;
        h5_tempo.innerHTML = timeToStr(0);
        contando = false;
    } else {
        if (timer_cont_esta_atrasado()) {
            add_log('ATRASADO'); 
            obter_tempo();
            set_t1();
        }
        tempo--;
        btn_aguardar.innerText = T_CANCELAR;
        h5_tempo.innerHTML = timeToStr(tempo);
        contando = true;
        set_t1();
    }
}

function set_t1() {
     //add_log('antes: ' + t1);
     t1 = Date.now();
     //add_log('depois: ' + t1);
}

function timer_cont_esta_atrasado() {
    //tempo_atraso = timer_geral.intervalo + 5000; // 5 segundos a mais q o intervalo de tempo geral, 5. Entao 5 + 5 = 10
    tempo_atraso = 5000; // 5 segundos 
    return (Date.now() - t1 >= tempo_atraso); 
}

// timer de solicitacao de aguarde
// requisita o aguarde de conexoes de clientes
function timer_solicitacao_aguarde_cb() {
    if (cont <= 3) {
        if (tempo == 0) {
            obter_tempo();
        } else {
          add_log('tempo obtido: ' + timeToStr(tempo));
          parar_timer(timer_solicitacao_aguarde);
          solicitando_aguarde = false;
        }
    } else {
        add_log('tempo esgotado!');     
        btn_aguardar.disabled = false;
        parar_timer(timer_solicitacao_aguarde);
    }
    cont++;
}

// faz as seguintes checagens:
// aguarde cancelado?
// aguarde iniciado?
function timer_geral_cb() {
   existe_arq_aguarde(); 
}

function aguarde_erro(e) {
    add_log(e);
}

function add_log(texto) {
    if (debug) div_log.innerHTML += '<br> ' + texto;
        
    if (debug_console) console.log(texto);
}

obter_tempo();
iniciar_timer(timer_geral);
</script>
</body>
</html>
