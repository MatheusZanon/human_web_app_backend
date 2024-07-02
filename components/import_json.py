from configuracao_db import configura_db
import json

def main():
    # Conecte-se ao banco de dados MySQL
    db_conf, conn, cursor = configura_db()

    try:
        # Abra o arquivo JSON com os dados
        with open('caminho\\arquivo.json', 'r') as arquivo_json:
            dados = json.load(arquivo_json)
            for registro in dados:
                # Supondo que `dados` é uma lista de dicionários onde as chaves são os nomes das colunas
                colunas = ', '.join(registro.keys())
                valores_placeholders = ', '.join(['%s'] * len(registro))
                valores = list(registro.values())

                sql = f"INSERT INTO tabela ({colunas}) VALUES ({valores_placeholders})"
                cursor.execute(sql, valores) 
        conn.commit()  
    except Exception as error:
        print(f"Ocorreu um erro: {error}")
    finally:
        if conn.is_connected():
            print("Fechando conexão")
            conn.close()

if __name__ == '__main__':
    main()