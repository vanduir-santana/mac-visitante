#!/usr/bin/python3
###!/usr/bin/env python
'''
Aguarda executar evento no commit do dhcpd.conf
passa parametros atraves do sys.argv
Remove visitante.
'''

__version__ = '0.55'
__author__ = 'Vanduir Santana'

import sys, os
import logging
from time import sleep
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import config
if config.wl_path:
    sys.path.insert(0, config.wl_path)
    from wunderlist import Wunderlist

PARAM_NEGAR_DESC = 'deny unknown-clients;\n'

class LoggerWriter:
    def __init__(self, logger, level):
        # self.level is really like using log.debug(message)
        # at least in my case
        self.logger = logger
        self.level = level

    def write(self, message):
        # if statement reduces the amount of newlines that are
        # printed to the logger
        if message != '\n':
            self.logger.log(self.level, message)
            #print(message)

    def flush(self):
        # create a flush method so things can be flushed when
        # the system wants to. Not sure if simply 'printing'
        # sys.stderr is the correct way to do it, but it seemed
        # to work properly for me.
        #self.level(sys.stderr)
        pass

stderr_logger = logging.getLogger('STDERR')
sys.stderr = LoggerWriter(stderr_logger, logging.ERROR)

logging.basicConfig(filename=config.arq_log, format='%(asctime)s:%(levelname)s:%(name)s:%(message)s', level=logging.INFO)

def p(t):
    logging.info(t)
    print(t)

class TipoBloqueio(Enum):
    mac = 1
    vencidos = 2
    timeout = 3     # bloqueia os que estiverem com status = login_cp. Terminou o tempo, mas nao mudou o status, entao bloqueia

class StatusConexao(Enum):
    bloqueado = 0   # bloqueado o acesso a internet
    proxy = 1       # liberado pra navegar usando o proxy
    liberado = 2    # totalmente liberado
    login_cp = 3    # login no CP, faz nat na porta 80 pra web app mac-visitante e trata login autom.
    liberado_cp = 4 # liberado pelo CP, separado do status = liberado pra dividir na implem. controle de banda

class LiberarVisitante():
    def __init__(self, mac='', ip=''):
        self.mac = mac
        self.ip = ip

        self.dhcp = Dhcp(self.ip, self.mac)
        self.wl = Wunderlist(config.wl_lista) if config.wl_path else None
        if self.wl and self.wl.msg: p(self.wl.msg)
        self.nome = ''
        self.tempo_aguardar_arq = 0
        self.status_conexao = StatusConexao.login_cp if config.captive else StatusConexao.liberado
        self.fmt_linha_vis = '{mac}|{ip}|{datahora}\n'   # formato da linha do arquivo de visitantes

    def aguardar_conexoes(self):
        '''
        Aceita conexoes de MACs desconhecidos (comenta deny unknown-clients), reinicia servidor dhcp
        Retorna uma tupla onde o primeiro valor eh boleano indicando que um cliente conectou,
        o segundo valor eh a mensagem.
        '''

        estava_aguardando = self.esta_aguardando()
        if estava_aguardando:
            p('Ja esta aguardando, ler tempo do arquivo')
            tempo_aguardar = self.tempo_aguardar_arq
        else:
            p('NAO esta aguardando, aguardar e escrever tempo no arquivo de aguarde')
            tempo_aguardar = config.tempo_aguardar
            # permite atribuir IP pra MACs nao cadastrados
            # comentar deny unknown-clients
            p('-' * 30)
            p('Permitir conexoes de MACs desconhecidos')
            self.dhcp.comentar_linha_conf(param=PARAM_NEGAR_DESC, comentar=True)

            # reiniciar servidor dhcp
            self.dhcp.reiniciar()

        # aguarda tempo pra novas conexoes
        p('Aguardando conexoes...')
        t = datetime(
            datetime.now().year,
            datetime.now().month,
            datetime.now().day) + timedelta(seconds=tempo_aguardar
        )

        delay = config.tempo_aguardar_interacoes
        print('-' * 80)
        for i in range(tempo_aguardar, 0, -1):
            t = t - timedelta(seconds=delay)
            # imprime mesma linha
            print('Aguardando por conexoes de visitantes <<%s>>' % t.strftime('%H:%M:%S'), end='\r', flush=True)

            if estava_aguardando:
                if not self._existe_arq_aguarde():
                    p('CANCELADO aguarde!')
                    break
            else:
                if self._verificar_cancelamento():
                    p('CANCELANDO aguarde...')
                    break
                else:
                    self._escrever_arq_aguarde(i)

            sleep(delay)
        else:
            print()
            if not estava_aguardando: self.cancelar_aguarde()
            p('Tempo de aguarde esgotado!')
            p('TERMINOU aguarde!')
            return True

        print()
        if not estava_aguardando: self.cancelar_aguarde()
        p('aguarde CANCELADO!')
        p('FIM AGUARDE!')
        return False

    def solicitar_cancelamento_aguarde(self):
        '''
        Solicita o cancelamento de aguarde de conexoes.
        '''
        p('solicitar CANCELAMENTO aguarde de conexoes...')
        Path(config.arq_cancelar).touch()

    def cancelar_aguarde(self, reiniciar_dhcp=True):
        # descomentar deny unknown-clients
        p('Bloquear conexoes de MACs desconhecidos')
        self.dhcp.comentar_linha_conf(param=PARAM_NEGAR_DESC, comentar=False)
        # reiniciar servidor dhcp
        if reiniciar_dhcp:
            self.bloquear_timeout()
            self.dhcp.reiniciar()
            self._ipt_aplicar()
        self._limpar_arqs()
        p('NAO aguardar mais por conexoes!')


    def _verificar_cancelamento(self):
        '''
        Verificar cancelamento de aguarde.
        '''
        return os.path.exists(config.arq_cancelar)

    def _limpar_arqs(self):
        '''
        Excluir arquivos
        '''
        try:
            if os.path.exists(config.arq_cancelar):
                os.remove(config.arq_cancelar)

            if os.path.exists(config.arq_aguarde):
                os.remove(config.arq_aguarde)

        except Exception as e:
            p('Erro ao limpar!')
            p(e)
            return False

        return True

    def liberar(self, captive_liberar=False):
        '''
        Liberar acesso total sem passar pelo proxy
        captive_liberar: libera internet quando status_conexao = StatusConexao.liberado_cp e tiver configurado pra captive portal
        '''

        p('-' * 30)
        #p('Chamado por dhcp server')
        p('Liberar...')
        mac_aux = validar_mac(self.mac)
        p('IP: %s' % self.ip)
        if not mac_aux:
            p('MAC invalido!')
            return False
        p('MAC: %s' % mac_aux)
        self.mac = mac_aux
        if not self.eh_ip_visitante():
            p('NAO eh visitante')
            return False
        p("Eh IP de visitante")

        if not self.esta_aguardando():
            p("NAO esta aguardando")
            return False

        # Liberar internet pelo Captive Portal
        # redireciona pra captive pra depois fazer cadastro rápido e liberar internet
        if config.captive:
            if not self._existe_visitante():
                self.status_conexao = StatusConexao.login_cp
                self._inserir_visitante()
                self._inserir_alterar_rede_csv()
                self._ipt_redir_captive()
            elif self.status_conexao == StatusConexao.login_cp:
                if not captive_liberar:
                    p('Pra liberar internet eh preciso setar captive_liberar = True')
                    return False
                self.status_conexao = StatusConexao.liberado_cp
                self._inserir_alterar_rede_csv()
                self._ipt_aplicar()
            elif self.status_conexao == StatusConexao.liberado or self.status_conexao == StatusConexao.liberado_cp:
                p('Internet ja liberada pro IP {ip}'.format(ip=self.ip))
                return False
        else:
            # nao tem captive portal
            # ja existe visitante?
            if self._existe_visitante():
                return False

            self.status_conexao = StatusConexao.liberado
            self._inserir_visitante()
            self._inserir_alterar_rede_csv()
            self._ipt_aplicar()

        ## cancelar aguarde quando detectada conexao de cliente (quando for liberar)?
        #if config.cancelar_aguarde:
        #    self.cancelar_aguarde(reiniciar_dhcp=False)

        if self.wl:
            self.wl.set_tarefa('VISITANTE "%s" LIBERADO: %s, %s. Status = %s' % (self.nome, self.mac, self.ip, self.status_conexao), lembrete=True)
            if self.wl.msg: p(self.wl.msg)

        return True

    def _ipt_redir_captive(self):
        '''
        Redireciona porta 80 pra Captive Portal pra fazer login
        '''
        p('Executar script de rede, marcar pacotes...')
        cmd = config.cmd_captive_marcar.format(mac=self.mac, ip=self.ip)

        return _exec_cmd(cmd)

    def _ipt_aplicar(self):
        '''
        Executa comando rede ipt. Aplica firewall de acordo com o rede.csv
        '''

        p('Exectuar script de firewall')
        cmd = config.cmd_ipt

        return _exec_cmd(cmd)

    def _venceu(self, dh):
        '''
        Verifica se venceu o tempo permitido
        '''
        if not type(dh) == datetime:
            dh = dh.rstrip()
            dh = datetime.strptime(dh, config.fmt_dth)

        td = timedelta(seconds=config.tempo_permitido)
        return datetime.now() >= (dh + td)


    def bloquear(self, tipo_bloqueio=TipoBloqueio.mac):
        '''
        Bloqueia acesso de visitante. Exclui do arquivo de visitantes e
        do arquivo de rede. Em seguida executa o script de rede.
        Ou exclui visitantes vencidos, depende de como é setada o parametro
        tipo_bloqueio
        '''
        #p('-' * 30)
        if tipo_bloqueio == TipoBloqueio.mac:
            if not self.mac:
                p('MAC nao setado!')
                return False

        #p('Bloqueando visitantes com o status == %s' % tipo_bloqueio.name)

        # muda ordem se forem registros q estao marcados
        arqs = (config.arq_visitantes, config.arq_rede) if tipo_bloqueio != TipoBloqueio.timeout else (config.arq_rede, config.arq_visitantes)
        encontrou = False
        macs_excluir = []
        for arq in arqs:
            if not os.path.exists(arq):
                p('Arquivo %s NAO existe!' % arq)
                return False

            with open(arq, 'r+', encoding='utf-8') as f:
                linhas = f.readlines()
                f.seek(0)
                for linha in linhas:
                    if tipo_bloqueio == TipoBloqueio.mac:
                        # exclui linha (nao escreve linha correspondente ao MAC)
                        if not linha.startswith(self.mac):
                            f.write(linha)
                        elif arq == config.arq_rede:
                            encontrou = True
                    elif tipo_bloqueio == TipoBloqueio.vencidos:
                        # pega a data do arquivo de visitantes e exclui vencidos
                        if arq == config.arq_visitantes:
                            mac, ip, dt = linha.split('|')
                            if not self._venceu(dt):
                                f.write(linha)
                            else:
                                encontrou = True
                                macs_excluir.append(mac)
                        else: # arquivo rede.csv
                            if len(linha) > 17 and not linha.startswith('#'):
                                mac = linha[:17]
                                # so escreve linha no arquivo de rede se NAO fizer parte dos visitantes vencidos
                                if not mac in macs_excluir:
                                    f.write(linha)
                                else:
                                    p('Bloqueando visitante com tempo vencido: ' + mac)
                            else:
                                f.write(linha)
                    elif tipo_bloqueio == TipoBloqueio.timeout:
                        if arq == config.arq_rede:
                            if  not linha.startswith('#'):
                                mac, ip, nome, descricao, status, sep = linha.split('|')
                                status = StatusConexao(int(status))
                                if status != StatusConexao.login_cp:
                                    f.write(linha)
                                else:
                                    encontrou = True
                                    macs_excluir.append(mac)
                            else:
                                f.write(linha)
                        else: # arq_visitantes
                            if len(linha) > 17 and not linha.startswith('#'):
                                mac = linha[:17]
                                if not mac in macs_excluir:
                                    f.write(linha)
                                else:
                                    p('Bloqueando visitantes MARCADOS q NAO foram liberados pelo Captive Portal: %s'  % mac)

                    f.truncate()

        if encontrou:
            self.dhcp.reiniciar()
            self._ipt_aplicar()
            if tipo_bloqueio != TipoBloqueio.vencidos:
                p('Encontrou MAC %s no arq de rede, excluido' % self.mac)
            else:
                p('Encontrou MACs %s com tempo vencido, excluidos' % macs_excluir)

            if self.wl:
                self.wl.set_tarefa('VISITANTE BLOQUEADO: %s' % self.mac, lembrete=True)
                if self.wl.msg: p(self.wl.msg)
            return True
        else:
            if tipo_bloqueio == TipoBloqueio.mac: p('MAC nao encontrado!')
            return False


    def bloquear_vencidos(self):
        '''
        Bloqueia todos os que estiverem vencidos no arquivo de visitantes.
        '''
        return self.bloquear(tipo_bloqueio=TipoBloqueio.vencidos)

    def bloquear_timeout(self):
        '''
        Bloqueia todos que estiverem como marcados e nao foram liberados pelo
        Captive Portal
        '''
        return self.bloquear(tipo_bloqueio=TipoBloqueio.timeout)

    def _gerar_nome_host(self):
        # cuidado pra nao dar problema no bind (nao usar underline)
        self.nome = 'tmp-%s' % datetime.now().strftime('%d-%m-%Y-%H-%M-%S')
        return self.nome

    def _existe_arq_aguarde(self):
        return os.path.exists(config.arq_aguarde)

    def esta_aguardando(self):
        #return self._existe_arq_aguarde()
        self.tempo_aguardar_arq = 0
        if not self._existe_arq_aguarde():
            return False
        else:
            # verifica se arquivo esta sendo atualizado
           linha = self._ler_arq_aguarde()
           if linha:
               #delay = config.tempo_aguardar_interacoes + 1
               delay = 1
               sleep(delay)
               linha_nova = self._ler_arq_aguarde()
               if linha != linha_nova:
                   if linha_nova == '':
                       p('ARQUIVO DE AGUARDE RETORNOU VAZIO')
                       return True
                   else:
                       self.tempo_aguardar_arq = int(linha_nova)
                   return True
               else:
                   # tvz tenha travado durante o aguarde
                   p('Provavelmente travou durante aguarde, limpando...')
                   self._limpar_arqs()
                   return False
           else:
               return False


    def _ler_arq_aguarde(self):
        if not os.path.exists(config.arq_aguarde):
            p('Nao encontrou arq. {arq} em _ler_arq_aguarde()'.format(arq=config.arq_aguarde))
            return False

        with open(config.arq_aguarde, 'r') as f:
            try:
                linha1 = f.readline()
                if linha1: linha1 = linha1.strip()
            except Excption as e:
                p('Erro ao ler arquivo!')
                p(e)
                return False
            return linha1

    def _escrever_arq_aguarde(self, valor):
        # sem o with pois nao se sabe quando o arquivo eh fechado
        f = open(config.arq_aguarde, 'w')
        f.write(str(valor))
        f.close()


    def eh_ip_visitante(self):
        '''
        Verifica se o ip que conectou esta dentro do intervalo (range) de visitantes.
        Pra funcionar o range de ips tem que ta fora do intervalo de ips fixos;
        '''
        ip_inicial, ip_final = self.dhcp.get_intervalo_subrede()
        return self.dhcp._ipv4_in(self.ip, ip_inicial, ip_final)

    def _inserir_visitante(self):
        '''
        Salva registro de acesso de visitante no arquivo texto.
        '''
        #self.fmt_linha_vis = '{mac}|{ip}|{datahora}\n'
        # status: StatusConexao.login_cp ou StatusConexao.liberado

        p('Salvando visitante!')
        with open(config.arq_visitantes, 'a', encoding='utf-8') as f:
            dth = datetime.now().strftime(config.fmt_dth)
            f.write(self.fmt_linha_vis.format(mac=self.mac, ip=self.ip, datahora=dth))


    #def _atualizar_visitante(self):
    #    '''
    #    Altera registro de acesso de visitante
    #    '''
    #    p('Editando visitante')
    #    if not self.mac:
    #        p('MAC NAO definido!')
    #        return False
    #
    #    encontrou = False
    #    with open(config.arq_visitantes, 'r+', enconding='utf-8') as f:
    #        p('Procurando por  "%s, %s, %s, %s"' % (self.mac, self.ip, self.status_conexao))
    #        linhas = f.readlines()
    #        f.seek(0)
    #        for linha in linhas:
    #            if not linha.startswith(self.mac):
    #                f.write(linha)
    #            else:
    #                dth = datetime.now().strftime(config.fmt_dth)
    #                f.write(fmt_linha_vis.format(mac=self.mac, ip=self.ip, datahora=dth))
    #                encontrou = True
    #        f.truncate()

    def _inserir_alterar_rede_csv(self):
        '''
        Edita ou salva registro no arquivo de configuracoes (rede.csv)
        '''
        # Padrao do arquivo
        #mac|ip|nome|descricao|status|
        #02:05:03:82:66:00|172.16.4.22|bpi-r1|Banana PI R1|1|

        #fmt = '{mac}|{ip}|{nome}|{descricao}|{status}|\n'
        fmt = config.fmt_csv
        r = False

        with open(config.arq_rede, 'r+', encoding='utf-8') as f:
            linha_n = lambda : f.write(fmt.format(mac=self.mac, ip=self.ip, nome=self._gerar_nome_host(), descricao='host tmp por dbit-mac-visitante', status=self.status_conexao.value))
            linhas = f.readlines()
            f.seek(0)
            encontrou = False
            for linha in linhas:
                if linha.startswith(self.mac):
                    p('Editando registro IP %s para o MAC %s, status %s' % (self.ip, self.mac, self.status_conexao.name))
                    linha_n()
                    encontrou = True
                else:
                    f.write(linha)

            if not encontrou:
                p('Fixando IP %s para o MAC %s' % (self.ip, self.mac))
                linha_n()
                r = True
            f.truncate()

        return r

    def _existe_visitante(self, campo='mac'):
        '''
        Verifica se existe acesso do visitante.
        Procurar registro de acordo o argumento campo: mac|ip
        Se return_reg = False o metodo retorna True quando visitante existir.
        Se return_Reg = True retorna o registro
        '''

        if campo == 'mac' and not self.mac:
            p('MAC NAO definido!')
            return False

        if campo == 'ip' and not self.ip:
            p('IP NAO definido!')
            return False

        if not os.path.exists(config.arq_visitantes):
            print('NAO existe arquivo de visitantes <<%s>> (def _existe_visitante)' % config.arq_visitantes)
            return False

        with open(config.arq_visitantes, 'r', encoding='utf-8') as f:
            for linha in f:
                if campo == 'mac':
                    if linha.startswith(self.mac):
                        p('Visitante <<%s, %s>> ja ta cadastrado' % (self.mac, self.ip))
                        mac, ip, dh = linha.split('|')
                        return {'mac': mac, 'ip':  ip, 'dh': dh}
                elif campo == 'ip':
                    if not linha or linha.startswith('#'): continue

                    mac, ip, dh = linha.split('|')
                    if ip == self.ip:
                        return {'mac': mac, 'ip':  ip, 'dh': dh}
                else:
                    p('CAMPO INVALIDO em _existe__visitante')
                    return False

        return False


class Dhcp():
    def __init__(self, ip, mac):
        self.encontrou_conexao = False
        self.ip = ip
        self.mac = mac

    def reiniciar(self):
        '''
        Reinicia servico do dhcp server.
        '''
        p('Reiniciar servidor dhcp...')
        cmd = config.cmd_reiniciar_dhcp

        return _exec_cmd(cmd)

    def comentar_linha_conf(self, param=PARAM_NEGAR_DESC, comentar=False):
        '''
        Comenta linha no arquivo de configuracao do dhcp server
        '''
        comentario = '#%s'
        encontrar = param if comentar else comentario % param
        param_linha = comentario % param if comentar else param
        encontrou = False

        p('Alterar linha em "%s"' % config.arq_dhcpd_conf)

        with open(config.arq_dhcpd_conf, 'r+', encoding='utf-8') as f:
            p('Tentando encontrar "%s"' % encontrar.strip())
            linhas = f.readlines()
            f.seek(0)
            for linha in linhas:
                if not linha.startswith(encontrar):
                    f.write(linha)
                else:
                    f.write(param_linha)
                    encontrou = True
            f.truncate()

        if encontrou:
            p('Linha alterada para "%s"' % param_linha.strip())
        else:
            p('NAO encontrou!')

        return encontrou

    def get_intervalo_subrede(self):
        flag_subnet = False
        with open(config.arq_dhcpd_conf, 'r', encoding='utf-8') as f:
            for linha in f:
                if not flag_subnet:
                    if linha.lstrip().startswith('subnet'):
                        flag_subnet = True
                else:
                    if linha.lstrip().startswith('range'):
                        return self._extrair_intervalo(linha)
                    elif linha.startswith('}'):
                        return (None, None)
            else:
                return (None, None)


    def _extrair_intervalo(self, linha):
        linha = linha.lstrip()
        ponto_virgula = linha.find(';')
        linha = linha[:ponto_virgula]
        intervalo = linha.split()
        ip_inicial = intervalo[1]
        ip_final = intervalo[2].replace(';', '')
        return (ip_inicial, ip_final)

    def _converter_ipv4(self, ip):
        return tuple(int(n) for n in ip.split('.'))

    def _ipv4_in(self, ip,  inicial, final):
        return self._converter_ipv4(inicial) <= self._converter_ipv4(ip) <= self._converter_ipv4(final)

#---------------------------------------------------------------
#           F U N C O E S    G E R A I S
#---------------------------------------------------------------
def validar_mac(mac):
    '''
    Alem de validar, corrige quando uma parte do MAC (entre dois pontos) comeca com 0 ele eh cortado.
    Bug do isc-dhcp-server
    '''
    if len(mac) == 17:
        return mac

    mac = mac.split(':')
    if len(mac) != 6:
        p('MAC possui quantidade octetos errada!')
        return ''

    mac_novo = []
    for octeto in mac:
        tam_octeto = len(octeto)
        if tam_octeto == 0 or tam_octeto > 2:
            p('MAC informado possui octeto invalido: "%s"' % octeto)
            return ''
        elif tam_octeto == 1:
            mac_novo.append(octeto.zfill(2))
        elif tam_octeto == 2:
            mac_novo.append(octeto)

    return ':'.join(mac_novo)


def _exec_cmd(cmd):
    '''
    Executa comando
    '''
    try:
        r = os.popen(cmd).read()
        p(r)
    except Exception as msg:
        p('Erro ao executar comando %s' % cmd)
        p(msg)
        return False
    return True

def liberar(mac, ip):
    lv = LiberarVisitante(mac, ip)
    #if not lv.liberar():
    #    exit(2)
    lv.liberar()

def liberar_captive(mac,ip, nome):
    lv = LiberarVisitante(mac, ip)
    lv.nome = nome
    if not lv.liberar(captive_liberar=True):
        exit(2)

def bloquear(mac):
    mac = validar_mac(mac)
    if not mac:
        sys.exit(2)
    lv = LiberarVisitante(mac=mac, ip='')
    if not lv.bloquear():
        pass

def aguardar():
    lv = LiberarVisitante(mac='', ip='')
    return lv.aguardar_conexoes()

def cancelar():
    lv = LiberarVisitante(mac='', ip='')
    #return lv.cancelar_aguarde()
    return lv.solicitar_cancelamento_aguarde()

def bloquear_vencidos():
    lv = LiberarVisitante(mac='', ip='')
    return lv.bloquear_vencidos()


def uso():
    print()
    print('Uso do comando:')
    print('visitante aguardar|cancelar|bloquear|MAC|MAC IP|')
    print('Parametros:')
    print('    aguardar')
    print('        aguarda por conexoes de clientes ou visitantes de acordo com o tempo configurado')
    print('     cancelar')
    print('        cancela o aguarde de novas conexoes')
    print('     bloquear')
    print('        varre lista de visitantes e bloqueia os q estao com o tempo vencido')
    print('     MAC')
    print('        quando vc digita o endereco do MAC entende-se q vc quer excluir')
    print('     MAC IP')
    print('        quando vc digita o MAC e o IP separados por espaco, entende-se q vc quer liberar a conexao pra esse visitante')
    print('     MAC IP captive')
    print('        quando vc digita o MAC, IP e captive, entende-se q vc quer liberar a conexao atraves do Captive Portal')

#---------------------------------------------------------------
#           M A I N
#---------------------------------------------------------------
if __name__ == '__main__':
    quant_args = len(sys.argv)
    # so um parametro
    if quant_args == 2:
        # aguardar conexao
        if sys.argv[1] == 'aguardar':
            if not aguardar():
                exit(1)
        # cancelar aguarde
        elif sys.argv[1] == 'cancelar':
            if not cancelar():
                exit(1)
        # bloquear visitantes vencidos
        elif sys.argv[1] == 'bloquear':
            if not bloquear_vencidos():
                exit(1)
        # quando enviar somente o MAC eh interpretado q a intencao eh bloquear
        elif len(sys.argv[1]) == 17:
            mac = sys.argv[1]
            bloquear(mac)
            sys.exit(0)
        else:
            p('Parametro invalido!')
            sys.exit(2)
    # quando enviar MAC e IP eh interpretado q se quer liberar
    elif quant_args == 3:
        mac, ip = sys.argv[1], sys.argv[2]
        liberar(mac, ip)
        sys.exit(0)
    # quando enviar MAC, IP e captive a liberacao ta sendo feita pelo captive portal
    elif quant_args == 5:
        mac, ip, nome, captive = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
        if captive != 'captive':
            p('Parametro invalido!')
            sys.exit(1)
        else:
            liberar_captive(mac, ip, nome)
    else:
        p('Parametros invalidos!')
        uso()
        sys.exit(2)

    sys.exit(0)
