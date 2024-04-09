#!/usr/bin/env python
'''
Interface web pra operar controle de visitantes
'''

__version__ = '1.2'
__author__ = 'Vanduir Santana'

from flask import Flask, request, render_template, jsonify, send_from_directory, Response, redirect
import sys
sys.path.insert(0, '..')
from visitante import LiberarVisitante, StatusConexao
import persistencia
import config
import os
import subprocess, shlex
from getmac import get_mac_address

if config.wl_path:
    sys.path.insert(0, config.wl_path)
    from wunderlist import Wunderlist
wl = Wunderlist(config.wl_lista) if config.wl_path else None


app = Flask(__name__, template_folder='.', static_folder='.')

###############################################################
# arquivos estaticos
@app.route('/visitante/js/<path:path>')
def js(path):
    return send_from_directory('s/js', path)

@app.route('/visitante/css/<path:path>')
def css(path):
    return send_from_directory('s/css', path)

@app.route('/visitante/img/<path:path>')
def img(path):
    return send_from_directory('s/img', path)

###############################################################
# pags
###############################################################
@app.route('/')
def ini():
    #return 'Teste Captive'
    return redirect(config.captive_url, code=302)

@app.route('/visitante')
@app.route('/visitante/')
def raiz():
    if not eh_ip_admin():
        return 'Acesso Negado!'

    return render_template('visitante.tpl', url=config.url)

@app.route('/visitante/id')
def id():
    return render_template('id.tpl', captive_titulo=config.captive_titulo, url=config.url, captive_redir=config.captive_redir)

###############################################################
# tela de login Captive Portal
###############################################################

def cp():
    #return render_template('id.tpl', url=config.url)
    return render_template('redir.tpl', url=config.captive_url)

##############
# Android
@app.route('/generate_204', methods=['GET', 'POST'])
def generate_204():
    print('CP Android - 1!')
    return redirect(config.captive_url, code=302)
    #return cp()

@app.route('/gen_204', methods=["GET", "POST"])
def handle_fallback_android():
    print('CP Android - 2!')
    return redirect(config.captive_url, code=302)

##############
# Windows
@app.route('/ncsi.txt', methods=['GET', 'POST'])
def ncsi():
    return cp()

@app.route('/connecttest.txt', methods=['GET', 'POST'])
def connecttest():
    return cp()

@app.route('/redirect', methods=['GET', 'POST'])
def redirect_win():
    return redirect(config.captive_url, code=302)


##############
# Apple
@app.route('/hotspot-detect.html', methods=['GET', 'POST'])
def redirect_apple():
    print('CP Apple!')
    return redirect(config.captive_url, code=302)


##############################################################
# metodos servidor
###############################################################
@app.route('/visitante/tempo', methods=['GET'])
def tempo():
    lv = LiberarVisitante()
    r = lv.esta_aguardando()
    d = {'tempo': lv.tempo_aguardar_arq }
    return jsonify(d)

@app.route('/visitante/existe_arq_aguarde', methods=['GET'])
def existe_arq_aguarde():
    existe_arq_aguarde = LiberarVisitante()._existe_arq_aguarde()
    d = {'existe_arq_aguarde': existe_arq_aguarde}
    return jsonify(d)

@app.route('/visitante/solicitar_aguarde', methods=['GET'])
def sol_aguarde():
    return _exec_cmd(config.cmd_aguardar)

@app.route('/visitante/solicitar_cancelamento', methods=['GET'])
def sol_cancelamento():
    return _exec_cmd(config.cmd_cancelar, esperar=True)

@app.route('/visitante/ip', methods=['GET'])
def ip():
    return jsonify(ip=get_ip())

@app.route('/visitante/id/get_visitante/<cpf>', methods=['GET'])
def get_visitante(cpf):
    pv = persistencia.Visitante()
    reg = pv.selecionar_por_cpf(cpf)
    return jsonify(reg)

@app.route('/visitante/id/set_visitante', methods=['POST'])
def set_visitante():
    reg = request.json
    ret = {}

    pv = persistencia.Visitante()
    if pv.existe_cpf(reg['cpf']):
        r = pv.atualizar(**reg)
    else:
        r = pv.inserir(**reg)

    #ret['ok'] = r

    # Liberar internet caso tenha inserido corretamente
    nome, mac, ip = reg['nome'], reg['mac'], get_ip()
    print('Liberando internet pro cliente: {}, {}, {}'.format(nome, mac, ip))
    lv = LiberarVisitante(mac=mac, ip=ip)
    # setar status atual da conexao
    lv.status_conexao = StatusConexao.login_cp
    r = lv.liberar(captive_liberar=True)

    ret['ok'] = r

    return jsonify(ret)

@app.route('/visitante/id/perm', methods=['GET'])
def perm():
    print()
    print('#' * 30)
    print('/visitante/id/perm')
    ip = get_ip()
    print('ip {}'.format(ip))
    lv = LiberarVisitante(ip=ip)

    ok = False
    msg = ''
    mac = ''

    if not lv.eh_ip_visitante():
        msg = 'IP fora do intervalo permitido!'
        return jsonify(ok=ok, msg=msg, mac=mac)

    mac = get_mac_address(ip=ip, network_request=True)
    if mac == '00:00:00:00:00:00': mac = ''
    print('mac {}'.format(mac))
    r = lv._existe_visitante(campo='ip')
    print('lv._existe_visitante {}'.format(r))
    if not r:
        msg = 'MAC INexistente no registro de acessos!'
        mac = ''
    elif (not mac) or (mac == r['mac']):
        ok = True
        mac = r['mac']
    else:
        msg = 'MAC guardado nos acessos difere do MAC remoto!'
        mac = ''

    return jsonify(ok=ok, msg=msg, mac=mac)

###############################################################
# outros
###############################################################
def get_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

def eh_ip_admin():
    return get_ip() in config.ips_admin

def _exec_cmd(cmd, esperar=False):
    try:
        cmd = shlex.split(cmd)
        if not esperar:
            subprocess.Popen(cmd)
            print('Comando <<%s>> solicitado!' % cmd)
            d = {'ok': True}
        else:
            r = subprocess.call(cmd)
            print('Comando <<%s>> executado! Cod. retorno %d' % (' '.join(cmd), r))
            d = {'ok': True}
    except Exception as e:
        print('Erro ao executar comando <<%s>>!' % cmd)
        print(e)
        d = {'ok': False,
             'erro': str(e)}

    return jsonify(d)


if __name__ == '__main__':
    print('dbIT MAC Visitante versao: %s' % __version__)
    HOST = config.ip
    app.run(host=HOST, port=8081, debug=False)
