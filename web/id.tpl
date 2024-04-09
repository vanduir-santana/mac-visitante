<!doctype html>
<html lang="pt-BR">
<head>
<title>{{captive_titulo}}</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
<link href="/visitante/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">

    <style>
      .bd-placeholder-img {
        font-size: 1.125rem;
        text-anchor: middle;
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
      }

      @media (min-width: 768px) {
        .bd-placeholder-img-lg {
          font-size: 3.5rem;
        }
      }

      .btn-primary {
        /*color: #ff0000ff;*/
        background-color: #ff0000ff;
        border-color: #5bc2c2;
      }
      input:-webkit-autofill 
      {    
        -webkit-box-shadow: 0 0 0px 1000px #f9fbfd inset !important;
        -webkit-text-fill-color: #4D90FE !important;
      }
    </style>
    <link href="/visitante/css/floating-labels.css" rel="stylesheet">
</head>
<body>
    <form class="form-signin" autocomplete="off">
      <div class="text-center mb-4">
        <img class="mb-4" src="/visitante/img/logo.svg" alt="" width="220" height="74">
        <!--img class="mb-4" src="/visitante/img/logo-arred.svg" alt="" width="122" height="122"-->
        <h1 class="h3 mb-3 font-weight-normal">{{captive_titulo}}</h1>
        <p id="p1"></p>
      </div>

      <div id="div_campos">
        <input type="hidden" id="input_mac" placeholder="MAC" required disabled>
        <div class="form-label-group">
          <input type="text" class="form-control" id="input_cpf" placeholder="CPF" required disabled hidden inputmode="numeric">
          <label id="label_cpf" for="input_cpf" hidden>CPF</label>
        </div>

        <div class="form-label-group">
          <input type="text" class="form-control" id="input_nome" placeholder="Nome" required disabled hidden> 
          <label id="label_nome" for="input_nome" hidden>Entre com o seu nome</label>
        </div>

        <div class="form-label-group">
          <input type="text" class="form-control" id="input_fone" placeholder="Fone" required disabled hidden inputmode="numeric">
          <label  id="label_fone" for="input_fone" hidden>Fone</label>
        </div>

        <button class="btn btn-lg btn-primary btn-block" type="button" id="btn_enviar" disabled hidden>Enviar</button>
        <p class="mt-5 mb-3 text-muted text-center">&copy; dbIT Tecnologia - Todos os direitos reservados</p>
      </div>
    </form>
  </div>
<script src="/visitante/js/jquery-3.4.1.slim.min.js" integrity="sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n" crossorigin="anonymous"></script>
<script src="/visitante/js/jquery.mask.min.js"</script>
<script src="/visitante/js/popper.min.js" integrity="sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo" crossorigin="anonymous"></script>
<script src="/visitante/js/bootstrap.min.js" integrity="sha384-wfSDF2E50Y2D1uUdj0O3uMBJnjuUD4Ih7YwaYd1iqfktj0Uod8GCExl3Og8ifwB6" crossorigin="anonymous"></script>
<script src="/visitante/js/util.js"></script>
<script type="text/javascript">
const p1 = document.getElementById('p1');
const div_campos = document.getElementById('div_campos');
const input_mac = document.getElementById('input_mac');
const input_cpf = document.getElementById('input_cpf');
const label_cpf = document.getElementById('label_cpf');
const input_nome = document.getElementById('input_nome');
const label_nome = document.getElementById('label_nome');
const input_fone = document.getElementById('input_fone');
const label_fone = document.getElementById('label_fone');
const btn_enviar = document.getElementById('btn_enviar');
const url_existe_arq_aguarde = "{{url}}/visitante/existe_arq_aguarde";
const url_get_visitante = "{{url}}/visitante/id/get_visitante/";
const url_set_visitante = "{{url}}/visitante/id/set_visitante";
const url_perm_con = "{{url}}/visitante/id/perm";
const T_ENVIAR = 'Enviar';
const T_ENVIANDO = 'Enviando';
const T_SPINNER = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
var timer_geral = {hnd: null, cb: timer_geral_cb, intervalo: 6000};
const debug = false;
const debug_console = true;
const cor_ini_p = p1.style.color;

var modo_cadastro = false;
function hab_campos() {
    if (input_cpf.disabled == !modo_cadastro && p1.innerText != '') {
        //add_log('Evita executar');
        return;
    }
    
    var texto = ((modo_cadastro) ? 'Pra navegar basta fazer um cadastro rápido' : 'Não está aguardando!!! Inicie o aguarde de conexões.');

    p1.innerText = texto;
    p1.style.color = cor_ini_p;

    input_cpf.disabled = !modo_cadastro;
    input_cpf.hidden = !modo_cadastro;
    label_cpf.hidden = !modo_cadastro;

    input_nome.disabled = !modo_cadastro;
    input_nome.hidden = !modo_cadastro;
    label_nome.hidden = !modo_cadastro;

    input_fone.disabled = !modo_cadastro;
    input_fone.hidden = !modo_cadastro;
    label_fone.hidden = !modo_cadastro;

    btn_enviar.disabled = !modo_cadastro;
    btn_enviar.hidden = !modo_cadastro;

    if (modo_cadastro) input_cpf.focus();
}

function existe_arq_aguarde() {
    ajax(url_existe_arq_aguarde,
         function(resp) {
             var r = JSON.parse(resp);
             if (!r.existe_arq_aguarde) {
                add_log('NAO existe arq. de aguarde!');
                modo_cadastro = false;
             } else {
                add_log('EXISTE arq. de aguarde!');
                modo_cadastro = true;
             }
             hab_campos();
         },
         'GET');
}

//function limpar_campos(cpf=false) {
//    if (cpf) input_cpf.value = '';
//    input_nome.value = '';
//    input_fone.value = '';
//}

function get_visitante(cpf) {
    add_log('Procurando cadastro para o CPF ' + cpf);
    var url = url_get_visitante + cpf;
    ajax(url,
         function(resp) {
            var r = JSON.parse(resp);
            if (Object.keys(r).length === 0) {
                add_log('NÃO encontrou nenhum registro pra esse CPF');
                //limpar_campos();
            } else {
                input_nome.value = r.nome;
                input_fone.value = r.fone;
            }
         },
         'GET');
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

/////////////////////////////////////////////////////////////
//  Util
/////////////////////////////////////////////////////////////

function msg(texto, reset=false) {
    if (!reset) {
        p1.style.color = 'red';
        p1.innerText = texto;
    } else {
        p1.style.color = cor_ini_p;
        if (texto) p1.innerText = texto;
    }
}

function add_log(texto) {
    if (debug) div_log.innerHTML += '<br> ' + texto;
        
    if (debug_console) console.log(texto);
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

function get_cpf_sem_masc(cpf){
    var cpf = input_cpf.value;
    return cpf.replace('.', '').replace('.', '').replace('-', '');
}

function validar_cpf(cpf) {
    add_log('Validando o CPF ' + cpf);

    var cpf = input_cpf.value;
    if (cpf == undefined || cpf === '') return false;
    cpf = get_cpf_sem_masc(cpf);

    add_log(cpf);

    var soma;
    var resto;
    soma = 0;
    if (cpf == "00000000000") return false;
     
    for (i=1; i<=9; i++) soma = soma + parseInt(cpf.substring(i-1, i)) * (11 - i);
    resto = (soma * 10) % 11;
   
    if ((resto == 10) || (resto == 11))  resto = 0;
    if (resto != parseInt(cpf.substring(9, 10)) ) return false;
   
    soma = 0;
    for (i = 1; i <= 10; i++) soma = soma + parseInt(cpf.substring(i-1, i)) * (12 - i);
    resto = (soma * 10) % 11;
   
    if ((resto == 10) || (resto == 11))  resto = 0;
    if (resto != parseInt(cpf.substring(10, 11) ) ) return false;
    return true;
}

function validar_nome(nome) {
    if (nome === undefined || nome === '') {
        msg('Favor preencher nome');
        return false;
    }
    if (nome.search(" ") == -1) {
        msg('Favor digitar sobrenome');
        return false;
    }

    return true;
}

function get_fone_sem_masc(fone) {
    if (fone === undefined) return;
    return fone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
}
function validar_fone(fone) {
    if (fone === undefined) return;
    fone = get_fone_sem_masc(fone);

    if (fone.length < 8) {
        msg('Favor digitar fone completo');
        return false;
    }

    //if (fone == '(11) 1111-1111'

    return true;
}

/////////////////////////////////////////////////////////////
//  Eventos
/////////////////////////////////////////////////////////////
input_cpf.addEventListener('focusout', function(){
    if (input_cpf.disabled) return;
    if (!validar_cpf(input_cpf.value)) {
        msg('CPF Inválido!');
        //limpar_campos();
        return false;
    }

    get_visitante(get_cpf_sem_masc(input_cpf.value));
});

input_nome.addEventListener('focusout', function() {
    if (input_nome.disabled) return;
    validar_nome(input_nome.value);
});

input_fone.addEventListener('focusout', function() {
    if (input_fone.disabled) return;
    validar_fone(input_fone.value);
});

btn_enviar.addEventListener('click', function() { 
    if (!validar_cpf(input_cpf.value)) { input_cpf.focus(); return; }
    if (!validar_nome(input_nome.value)) { input_nome.focus(); return;}
    if (!validar_fone(input_fone.value)) { input_fone.focus(); return; }

    var t_redir_spinner = T_SPINNER + ' ' + 'Redirecionando...';
    btn_enviar.disabled = true;

    if (btn_enviar.innerText == T_ENVIAR) {
        add_log('Enviando..');

        // salvar registro
        var reg = {mac: input_mac.value, 
                   cpf: get_cpf_sem_masc(input_cpf.value), 
                   nome: input_nome.value, 
                   fone: get_fone_sem_masc(input_fone.value)};


        btn_enviar.innerHTML = t_redir_spinner;
        ajax(url_set_visitante, 
             function(resp){
                var r = JSON.parse(resp);
                if (r.ok) {
                    add_log('Registro inserido/atualizado!');
                    add_log('Internet liberada!');
                    location.replace('{{captive_redir}}');
                    
                } else {
                    btn_enviar.disabled = false;
                    btn_enviar.innerHTML = T_ENVIAR;
                    add_log('PROBLEMAS ao inserir/atualizar registro!');
                    msg('PROBLEMAS ao inserir/atualizar registro!');
                }
             }, 
             "POST", "json", reg
        );

    } /*else {
        add_log('Cancelar...');
        btn_enviar.innerHTML = t_enviar_spinner;
        solicitar_cancelamento();
    }*/

    // salvar ou alterar registro cliente, liberar acesso a internet e depois
    // redirecionar pra uma pagina ou pro check in face
}, false);

/////////////////////////////////////////////////////////////
// Mascaras 
/////////////////////////////////////////////////////////////
$(function() {
    $('#input_cpf').mask('000.000.000-00', {reverse: true});


    var fone_masc = function (val) {
      return val.replace(/\D/g, '').length === 11 ? '(00) 00000-0000' : '(00) 0000-00009';
    },
    spOptions = {
      onKeyPress: function(val, e, field, options) {
          field.mask(fone_masc.apply({}, arguments), options);
        }
    };

    $('#input_fone').mask(fone_masc, spOptions);

});

/////////////////////////////////////////////////////////////
// Main
/////////////////////////////////////////////////////////////
function main() {
    msg('Processando...');
    ajax(url_perm_con, 
         function(resp){
            var r = JSON.parse(resp);
            if (r.ok) {
                existe_arq_aguarde();
                iniciar_timer(timer_geral);
                input_mac.value = r.mac;
            } else {
                add_log('PROBLEMAS ao verificar permissão!');
                msg(r.msg);
            }
         }, 
         'GET'
    );
}

main();

</script>
</body>
</html>
