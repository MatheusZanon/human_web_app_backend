from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restful import Api, Resource, reqparse
import mysql.connector
from mysql.connector import errorcode
from components.db_config import db_config
from components.importacao_hash_lib import hash_lib

# Configuração do aplicativo e da Api
app = Flask(__name__)
CORS(app)
api = Api(app)

db_conf = db_config()
# Configurações do banco de dados (substitua pelos seus próprios valores)
try: 
    conn = mysql.connector.connect(**db_conf)
    cursor = conn.cursor()
    print(" * Conexão bem sucedida!")

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Tem algo de erro com seu nome ou senha")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database não existe")
    else:
        print(err) 


class Login(Resource):
    def get(self):
        return "método GET para Login"
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user_email', type=str, required=True, help='Email is required')
        parser.add_argument('user_password', type=str, required=True, help='Password is required')
        args = parser.parse_args()

        hash_password = hash_lib(args['user_password'])

        # Verifica as credenciais no banco de dados
        select_query = "SELECT * FROM funcionarios WHERE email = %s AND senha = %s"
        cursor.execute(select_query, (args['user_email'], hash_password))
        funcionario = cursor.fetchone()

        if funcionario:
            return {"message": f"Login bem-sucedido"}, 200
        else:
            return {"error": "Credenciais inválidas"}, 401

class Solicitacao(Resource):
    def get(self):
        return 200

    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('user_name', type=str, required=True, help='Nome é obrigatório')
            parser.add_argument('user_email', type=str, required=True, help='Email é obrigatório')
            parser.add_argument('user_password', type=str, required=True, help='Senha é obrigatória')
            parser.add_argument('telefone', type=int)
            parser.add_argument('setor', type=str)
            # Adicione mais campos conforme necessário
            
            args = parser.parse_args()
            hash_password = hash_lib(args['user_password'])

            # Aqui você pode realizar a lógica de cadastro no banco de dados
            # Exemplo fictício usando cursor:
            query = """INSERT INTO solicitacoes_cadastro (nome, email, senha, telefone_celular, setor) 
                       VALUES (%s, %s, %s, %s, %s)"""
            values = (args['user_name'], args['user_email'], hash_password, args['telefone'], args['setor'])

            with mysql.connector.connect(**db_conf) as conn, conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()

            return {"message": "Funcionário cadastrado com sucesso!"}, 200

        except Exception as error:
            return {"error": f"Erro durante o cadastro do funcionário: {error}"}, 500

class Funcionario(Resource):
    def get(self):
        try: 
            with mysql.connector.connect(**db_conf) as conn, conn.cursor() as cursor:
                # Executa a consulta SQL para obter todos os clientes
                query_selector = "SELECT * FROM funcionarios"
                cursor.execute(query_selector)

                # Obtém os nomes das colunas
                column_names = [desc[0] for desc in cursor.description]
                
                # Processa os resultados da consulta
                funcionarios = []
                for row in cursor.fetchall():
                    funcionario_data = dict(zip(column_names, row))
                    # Exclui as colunas "created_at" e "updated_at"
                    del funcionario_data['created_at']
                    del funcionario_data['updated_at']
                    funcionarios.append(funcionario_data)

            return {"funcionarios": funcionarios}, 200
        except Exception as error:
            return {"Erro": f"Ocorreu um erro na execução: {error}"}, 500
    
    def post(self):
        try:
            return {"message": "Funcionário cadastrado com sucesso!"}, 200
        except Exception as error:
            return {"error": f"Erro durante o cadastro do funcionário: {error}"}, 500


class Cliente(Resource):
    def get(self):      
        try: 
            with mysql.connector.connect(**db_conf) as conn, conn.cursor() as cursor:
                # Executa a consulta SQL para obter todos os clientes
                query_selector = "SELECT * FROM clientes_financeiro"
                cursor.execute(query_selector)

                # Obtém os nomes das colunas
                column_names = [desc[0] for desc in cursor.description]
                
                # Processa os resultados da consulta
                clientes = []
                for row in cursor.fetchall():
                    cliente_data = dict(zip(column_names, row))
                    # Exclui as colunas "created_at" e "updated_at"
                    del cliente_data['created_at']
                    del cliente_data['updated_at']
                    clientes.append(cliente_data)

            return {"clientes": clientes}, 200
        except Exception as error:
            return {"Erro": f"Ocorreu um erro na execução: {error}"}, 500
        
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('nome_razao_social', type=str, required=True, help='Nome é obrigatório')
            parser.add_argument('cnpj', type=int)
            parser.add_argument('cpf', type=int)
            parser.add_argument('email', type=str, required=True, help='Email é obrigatória')
            parser.add_argument('telefone_celular', type=int)
            parser.add_argument('regiao', type=str, required=True, help='Região é obrigatório')
            # Adicione mais campos conforme necessário

            args = parser.parse_args()

            # Aqui você pode realizar a lógica de cadastro no banco de dados
            # Exemplo fictício usando cursor:
            query = """INSERT INTO clientes_financeiro (nome_razao_social, cnpj, cpf, email, telefone_celular, regiao) 
                       VALUES (%s, %s, %s, %s, %s)"""
            values = (args['nome_razao_social'], args['cnpj'], args['cpf'], args['email'], args['telefone_celular'], args['regiao'])

            with mysql.connector.connect(**db_conf) as conn, conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()

            return {"message": "Cliente cadastrado com sucesso!"}, 200

        except Exception as error:
            return {"error": f"Erro durante o cadastro do cliente: {error}"}, 500

api.add_resource(Login, '/login')
api.add_resource(Solicitacao, '/solicitacao')
api.add_resource(Funcionario, '/funcionarios')
api.add_resource(Cliente, '/clientes')

if __name__ == "__main__":
    app.run(debug=True)