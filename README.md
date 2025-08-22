# Human Web App Backend

Este repositório contém o backend de um projeto web desenvolvido em **Python**, com foco em fornecer uma API RESTful segura e escalável para integração com diferentes serviços e aplicações.

## 📌 Objetivo
- O projeto foi criado como um backend centralizado para:
- Gerenciar dados de usuários e autenticação;
- Disponibilizar API RESTful para consumo pelo frontend;
- Integrar com banco de dados relacional em nuvem (RDS);
- Suportar execução de automações via funções serverless (AWS Lambda).

## 🛠️ Tecnologias Utilizadas
- **Python** (Framework Django)
- **Mysql Workbench**
- **JWT** (JSON Web Tokens) para autenticação
- **AWS Lambda** (execução de robôs automatizados)
- **AWS RDS** (banco de dados gerenciado)

## 🚀 Funcionalidades Principais
- API RESTful para gerenciamento de usuários e dados de aplicação
- Autenticação e autorização baseada em JWT personalizada para lidar com cookies (http only)
- Integração com banco de dados Mysql
- Deploy e execução de automações na AWS
- Estrutura modular, permitindo expansão de funcionalidades

## ⚙️ Estrutura do Projeto
```
📂 human_app
 ┣ 📂 migrations         # Histórico das migrações feitas no banco
 ┣ 📂 serializers        # Formatação dos dados das models
 ┣ 📂 services           # Serviços e regras de negócio
 ┣ 📂 sql                # Comandos para retirar tokens temporários do banco
 ┣ 📂 views              # Parte lógica das páginas da aplicação frontend
 ┣ 📜 authentication.py  # Configuração do sistema de Autenticação de Usuário
 ┣ 📜 models.py          # Configuração das entidades no banco
📂 human_project
 ┣ 📜 middleware.py      # Receptor de requisições, permite somente requisições vindas da plataforma
 ┣ 📜 settings.py        # Configurações gerais do projeto Django + AWS
```

## Participantes
Matheus Zanon - perfil no github (MatheusZanon) / Bruno Apolinário - perfil no github (obrunoapolinario)

## 📖 Observação
Este projeto foi desenvolvido como parte de um sistema de automação e backend web. Atualmente está **encerrado**, sendo mantido aqui apenas para fins de estudo, portfólio e referência técnica.
Este repositório tem caráter educacional e demonstração de boas práticas de backend.
