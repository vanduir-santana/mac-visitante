#!/usr/bin/env python

__version__ = '0.1'
__author__ = 'Vanduir Santana'

import sqlite3, sys, config
from datetime import datetime

SQL_VISITANTE = '''CREATE TABLE visitante (
id      INTEGER PRIMARY KEY,
mac     VARCHAR(17) NOT NULL,
cpf     VARCHAR(14) NOT NULL,
nome    VARCHAR(100) NOT NULL,
fone    VARCHAR(11),
data    TIMESTAMP);'''

class Visitante():
    def __init__(self):
        self.con = None
        self.conectado = False

    def conectar(self):
        if self.conectado: return True
        try:
            self.con = sqlite3.connect(config.arq_db)
        except sqlite3.Error as erro:
            print('Erro ao conectar ao db:', erro)
            self.conectado = False
            return False

        self.conectado = True
        return True

    def fechar(self):
        try:
            if not self.con:
                print('Nao eh possivel fechar a conexao pois nao foi setada!')
                return False

            self.con.close()
        except sqlite3.Error as erro:
            print('Erro ao fechar conexao:', erro)
            return False

        self.conectado = False
        return True

    def selecionar_por_cpf(self, valor):
        if not self.conectar():
            return False

        print('Selecionar registro para {} = {}'.format('CPF', valor))
        sql = 'SELECT mac, cpf, nome, fone, data FROM visitante WHERE cpf = ?'

        cursor = self.con.cursor()
        dados = (valor, )
        cursor.execute(sql, dados)
        regs = cursor.fetchone()
        cursor.close()
        self.fechar()

        if regs:
            d = {'mac': regs[0],
                 'cpf': regs[1],
                 'nome': regs[2],
                 'fone': regs[3],
                 'data': regs[4]
                 }
        else:
            d = dict()
        return d

    def existe_cpf(self, valor):
        if not self.conectar():
            return False

        print('Selecionar registro para {} = {}'.format('CPF', valor))
        sql = 'SELECT id FROM visitante WHERE cpf = ?'

        cursor = self.con.cursor()
        dados = (valor, )
        cursor.execute(sql, dados)
        reg = cursor.fetchone()
        cursor.close()
        self.fechar()

        if reg:
            if reg[0]:
                print('>>> reg[0]: {}'.format(reg[0]))
                return True

        return False


    def inserir(self, mac, cpf, nome, fone):
        if self.existe_cpf(cpf):
            print('Ja existe um registro com esse CPF, atualizando')
            return self.atualizar(cpf, mac, nome, fone)

        if not self.conectar():
            return False

        print('Inserindo {}, {}...'.format(mac, nome))
        dth = datetime.now()
        sql = 'INSERT INTO visitante (mac, cpf, nome, fone, data) VALUES (?, ?, ?, ?, ?);'
        dados = (mac, cpf, nome, fone, dth)

        try:
            cursor = self.con.cursor()
            cursor.execute(sql, dados)
            self.con.commit()
        except sqlite3.Error as erro:
            print('Erro ao inserir registro:', erro)
            self.fechar()
            return False

        cursor.close()

        self.fechar()
        return True

    def atualizar(self, cpf, mac, nome, fone):
        if not self.conectar():
            return False

        print('Atualizando registro para o cpf = {}'.format(cpf))
        sql = 'UPDATE visitante SET mac = ?, nome = ?, fone = ? WHERE cpf = ?'
        dados = (mac, nome, fone, cpf)

        try:
            cursor = self.con.cursor()
            cursor.execute(sql, dados)
            self.con.commit()
        except sqlite3.Error as erro:
            print('Erro ao atualizar registro:', erro)
            cursor.close
            self.fechar()
            return False

        cursor.close()

        self.fechar()
        return True

    def remover(self, mac='', cpf=''):
        if not self.conectar():
            return False

        if not mac and not cpf:
            print('Setar MAC ou CPF pra poder excluir')
            return False

        texto = 'para o MAC {}'.format(mac) if mac else 'para o CPF {}'.format(cpf)
        print('Removendo registro {}'.format(texto))
        sql = 'DELETE FROM visitante WHERE {} = ?'.format('mac' if mac else 'cpf')
        dados = (mac if mac else cpf,)

        cursor = self.con.cursor()
        cursor.execute(sql, dados)
        self.con.commit()
        cursor.close()

        self.fechar()

    def _esquema(self, sql):
        if not self.conectar():
            return False

        cursor = self.con.cursor()
        try:
            cursor.execute(sql)
            self.con.commit()
            cursor.close()
            self.fechar()
            return True
        except sqlite3.Error as erro:
            print('Erro ao criar esquema:', erro)
            self.fechar()
            return False


def main():
    quant_args = len(sys.argv)
    if quant_args == 2 :
        if sys.argv[1] == 'esquema':
            Visitante()._esquema(SQL_VISITANTE)
        else:
            print('Argumento invalido!')

if __name__ == '__main__':
    main()
