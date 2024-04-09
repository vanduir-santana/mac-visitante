#!/usr/bin/env python

# tempo (em segundos) pra ficar aguardando conexoes
tempo_aguardar = (3 * 60) + 8

# tempo (em segundos) que o acesso sera permitido
tempo_permitido = 8 * 60

# tempo (em segundos) para aguardar entre interacoes
tempo_aguardar_interacoes = 1

# diretorio principal projeto rede
DIRET_REDE = '/root/dev/rede/'
# diretorio principal projeto
DIRET_VISITANTE = '/home/vanduir/dev/mac-visitante'

# arquivo de configuracao dhcp
arq_dhcpd_conf = '{diret_rede}/etc/heads/dhcpd.conf.head'.format(diret_rede=DIRET_REDE)

# comando pra reiniciar servidor dhcp
cmd_reiniciar_dhcp = '{diret_rede}/main.sh dhcp'.format(diret_rede=DIRET_REDE)

# comando pra exectuar scripts de rede (iptables, bind, dhcp, etc)
cmd_rede_script = '{diret_rede}/main.sh'.format(diret_rede=DIRET_REDE)

cmd_visitante = '{diret_visitante}/visitante.py'.format(diret_visitante=DIRET_VISITANTE)
cmd_aguardar = '{cmd} aguardar'.format(cmd=cmd_visitante)
cmd_cancelar = '{cmd} cancelar'.format(cmd=cmd_visitante)

# arquivo de rede
arq_rede = '{diret_rede}/etc/rede.csv'.format(diret_rede=DIRET_REDE)

# arquivo de log
#arq_log = '{diret_visitante}/dbit-mac-visitante.log'.format(diret_visitante=DIRET_VISITANTE)
arq_log = '/tmp/mac-visitante-error.log'

# arquivo onde ficam registrados os visitantes
arq_visitantes = '{diret_visitante}/visitantes'.format(diret_visitante=DIRET_VISITANTE)

# arquivo de aguarde de conexoes de visitantes
# esse diretorio salva diretamente na memoria tornando mais rapida a maninpulacao do arquivo
arq_aguarde = '/run/shm/visitantes-aguarde'

# a presenca desse arquivo autoriza cancelamento de aguarde
arq_cancelar = '/run/shm/visitantes-cancelar'

# cancelar aguarde quando detectar primeiro visitante conectado?
#cancelar_aguarde = True
cancelar_aguarde = False

# lista do Wunderlist, quando adicionar ou bloquear visitante add item
# se nao quiser q adicione ao Wunderlist basta deixar wl_path = ''
#wl_path = '/home/vanduir/dev/wl'
wl_path = ''
wl_lista = 'MTU'

# configuracoes da interface web
ip = '172.16.4.20'

# url
url = 'http://uaitube.com:8081/'

# formato pra ser salvor no rede.csv
fmt_csv = '{mac}|{ip}|{nome}|{descricao}|{status}|\n'

# formtado de data hora
fmt_dth = '%d/%m/%Y %H:%M:%S'

# passar pelo captive portal
captive = True
# url captive portal
#captive_url = "http://uniao.id"
captive_url = "http://uaitube.com:8081/visitante/id"
# redirecionar para endereco abaixo dps q liberar a internet
captive_redir = "http://uaitube.com"
# comandos pra marcar pacotes e liberar internet
cmd_captive_marcar = cmd_rede_script + '  marcar {mac} {ip}'
cmd_ipt = '{diret_rede}/main.sh ipt'.format(diret_rede=DIRET_REDE)
captive_titulo = 'Acessar Internet'
arq_db = '{diret_visitante}/db/visitante.db'.format(diret_visitante=DIRET_VISITANTE)
# ips dos administratores do CP
ips_admin = ('172.16.0.22', '172.16.0.89')
