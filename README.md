# Sistema de Advocacia

Sistema de gerenciamento de processos jurídicos desenvolvido com FastAPI.

## Funcionalidades

- Gerenciamento de processos jurídicos (CRUD completo)
- Sistema de autenticação com JWT
- Autenticação de dois fatores (2FA) com Google Authenticator
- API RESTful documentada automaticamente

## Tecnologias

- **FastAPI** - Framework web moderno e rápido
- **SQLModel** - ORM para interação com banco de dados
- **SQLite** - Banco de dados
- **JWT** - Autenticação baseada em tokens
- **Bcrypt** - Criptografia de senhas
- **PyOTP** - Autenticação de dois fatores

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/sistema_advogado.git
cd sistema_advogado
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Executando o projeto

```bash
uvicorn main:app --reload
```

A API estará disponível em `http://localhost:8000`

Documentação interativa: `http://localhost:8000/docs`

## Estrutura do Projeto

```
sistema_advogado/
├── main.py          # Arquivo principal da aplicação FastAPI
├── models.py        # Modelos de dados (Processo, Usuario)
├── database.py      # Configuração do banco de dados
├── security.py      # Autenticação, JWT e 2FA
├── requirements.txt # Dependências do projeto
└── README.md        # Este arquivo
```

## Endpoints Principais

- `POST /usuarios` - Cadastrar novo usuário
- `POST /login` - Fazer login (retorna token JWT)
- `POST /usuarios/ativar-2fa` - Ativar autenticação de dois fatores
- `GET /processos` - Listar processos (requer autenticação)
- `POST /processos` - Criar novo processo
- `PUT /processos/{id}` - Atualizar processo
- `DELETE /processos/{id}` - Excluir processo

## Configuração

Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e defina sua `SECRET_KEY` (use uma chave segura e aleatória).

## Licença

Este projeto está sob a licença MIT.

