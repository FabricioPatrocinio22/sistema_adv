# Sistema de Advocacia ⚖️

Sistema completo de gerenciamento de processos jurídicos desenvolvido com FastAPI e Streamlit, incluindo IA para análise inteligente de documentos.

## ✨ Funcionalidades

### 🔐 Autenticação e Segurança
- Sistema de autenticação com JWT
- Autenticação de dois fatores (2FA) com Google Authenticator
- Criptografia de senhas com bcrypt
- Tokens de acesso com expiração

### 📋 Gerenciamento de Processos
- CRUD completo de processos jurídicos
- Upload de documentos PDF anexados aos processos
- Download de documentos via links pré-assinados
- Sistema de prazos e processos urgentes
- Associação de processos aos usuários
- Auto preenchimento de dados do processo via IA a partir de PDF

### 🤖 IA Jurídica
- Análise automática de documentos PDF usando Google Gemini AI
- Resumo inteligente de documentos jurídicos
- Identificação de informações importantes (datas, partes, tipo de documento)
- Triagem processual automatizada
- Auto preenchimento de formulários a partir de PDFs
- Extração inteligente de dados (número do processo, partes envolvidas, datas)

### 📊 Dashboard
- Visualização de estatísticas gerais
- Processos urgentes destacados
- Interface moderna e intuitiva com Streamlit

### 🌐 API RESTful
- Documentação automática com Swagger/OpenAPI
- CORS configurado para integração com frontend
- Endpoints bem estruturados e documentados

## 🛠️ Tecnologias

### Backend
- **FastAPI** - Framework web moderno e rápido
- **SQLModel** - ORM para interação com banco de dados
- **SQLite** - Banco de dados
- **JWT (python-jose)** - Autenticação baseada em tokens
- **Bcrypt** - Criptografia de senhas
- **PyOTP** - Autenticação de dois fatores
- **Google Gemini AI** - Análise inteligente de documentos
- **PyPDF** - Extração de texto de PDFs
- **AWS S3 (boto3)** - Armazenamento de arquivos na nuvem
- **Python-dotenv** - Gerenciamento de variáveis de ambiente

### Frontend
- **Streamlit** - Interface web interativa
- **Requests** - Comunicação com API

## 📦 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/FabricioPatrocinio22/sistema_adv.git
cd sistema_adv
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:

**Windows (PowerShell):**
```powershell
.\venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 🚀 Executando o Projeto

### Backend (FastAPI)

Em um terminal, execute:
```bash
uvicorn main:app --reload
```

A API estará disponível em `http://localhost:8000`

- Documentação interativa: `http://localhost:8000/docs`
- Documentação alternativa: `http://localhost:8000/redoc`

### Frontend (Streamlit)

Em outro terminal, execute:
```bash
streamlit run frontend.py
```

O frontend estará disponível em `http://localhost:8501`

## 📁 Estrutura do Projeto

```
sistema_advogado/
├── main.py          # Backend FastAPI - Endpoints e lógica da API
├── frontend.py      # Frontend Streamlit - Interface do usuário
├── models.py        # Modelos de dados (Processo, Usuario)
├── database.py      # Configuração do banco de dados
├── security.py      # Autenticação, JWT e 2FA
├── ia.py            # IA Jurídica - Análise de documentos
├── requirements.txt # Dependências do projeto
├── uploads/         # Pasta para arquivos PDF anexados
├── .gitignore       # Arquivos ignorados pelo Git
└── README.md        # Este arquivo
```

## 🔌 Endpoints da API

### Autenticação
- `POST /usuarios` - Cadastrar novo usuário
- `POST /login` - Fazer login (retorna token JWT)
- `POST /usuarios/ativar-2fa` - Ativar autenticação de dois fatores
- `POST /usuarios/confirmar-2fa` - Confirmar ativação do 2FA

### Processos
- `GET /processos` - Listar processos (requer autenticação)
- `POST /processos` - Criar novo processo
- `PUT /processos/{id}` - Atualizar processo
- `DELETE /processos/{id}` - Excluir processo
- `GET /processos/urgents` - Listar processos urgentes
- `POST /processos/{id}/anexo` - Anexar arquivo PDF ao processo (armazena no AWS S3)
- `GET /processos/{id}/download` - Obter link pré-assinado para download do arquivo
- `POST /processos/{id}/analise-ia` - Analisar documento com IA
- `POST /processos/extrair-dados-pdf` - Extrair e preencher dados do processo via IA a partir de PDF

### Dashboard
- `GET /dashboard/geral` - Estatísticas gerais do sistema

## ⚙️ Configuração

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```bash
# Segurança
SECRET_KEY=sua_chave_secreta_super_segura_aqui

# Backend
BACKEND_URL=${import.meta.env.VITE_API_URL}

# AWS S3 (para armazenamento de arquivos na nuvem)
AWS_ACCESS_KEY_ID=sua_access_key_aws
AWS_SECRET_ACCESS_KEY=sua_secret_key_aws
AWS_REGION=us-east-1
AWS_BUCKET_NAME=nome-do-seu-bucket

# Google Gemini AI
GEMINI_API_KEY=sua_api_key_do_google_gemini
```

### 2. Configuração do Google Gemini AI

Configure a API Key do Google Gemini no arquivo `ia.py` ou use a variável de ambiente `GEMINI_API_KEY`:

Para obter uma API Key:
- Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
- Crie uma nova API Key
- Adicione no arquivo `.env` como `GEMINI_API_KEY`

### 3. Configuração do AWS S3

1. **Criar conta AWS**: Acesse [AWS Console](https://console.aws.amazon.com/)
2. **Criar S3 Bucket**: 
   - Acesse o serviço S3
   - Crie um novo bucket
   - Configure as permissões necessárias
3. **Criar IAM User**:
   - Acesse IAM no AWS Console
   - Crie um usuário com permissões para S3 (AmazonS3FullAccess ou permissões personalizadas)
   - Gere Access Key e Secret Key
   - Adicione as credenciais no arquivo `.env`

**Nota**: Em produção, nunca commite o arquivo `.env` com credenciais reais!

## 🔒 Segurança

- Senhas são criptografadas usando bcrypt
- Tokens JWT com expiração de 30 minutos
- Autenticação de dois fatores opcional
- Validação de arquivos no upload
- CORS configurado (ajustar para produção)

## 📝 Uso da IA Jurídica

A IA Jurídica utiliza o Google Gemini para analisar documentos PDF:

### Análise de Documentos

1. Faça upload de um arquivo PDF através do endpoint `/processos/{id}/anexo`
2. O arquivo será automaticamente salvo no AWS S3
3. Chame o endpoint `/processos/{id}/analise-ia` para analisar o documento
4. A IA retornará um resumo estruturado com:
   - Tipo de documento
   - Informações das partes envolvidas
   - Datas importantes
   - Resumo do conteúdo
   - Observações relevantes

### Auto Preenchimento de Formulários

1. Use o endpoint `/processos/extrair-dados-pdf` enviando um PDF
2. A IA extrairá automaticamente:
   - Número do processo
   - Nome do cliente
   - Nome da contra-parte
   - Status do processo
   - Data de prazo (se disponível)
3. Os dados serão retornados prontos para preencher o formulário de cadastro

## ☁️ Armazenamento na Nuvem (AWS S3)

Todos os arquivos PDF são armazenados no AWS S3 para:
- ✅ Escalabilidade e performance
- ✅ Backup automático
- ✅ Segurança e redundância
- ✅ Acesso rápido via links pré-assinados
- ✅ Economia de espaço no servidor

Os links de download são gerados dinamicamente e têm expiração automática para segurança.

## 🌟 Recursos em Destaque

- ✅ Interface moderna e responsiva com Streamlit
- ✅ Análise inteligente de documentos jurídicos
- ✅ Sistema de prazos e alertas de urgência
- ✅ Upload e gerenciamento de documentos na nuvem (AWS S3)
- ✅ Download seguro via links pré-assinados
- ✅ Auto preenchimento inteligente de formulários via IA
- ✅ Dashboard com estatísticas em tempo real
- ✅ Autenticação robusta com 2FA
- ✅ API RESTful bem documentada
- ✅ Armazenamento escalável e seguro na nuvem

## 📄 Licença

Este projeto está sob a licença MIT.

## 👤 Autor

**FabricioPatrocinio22**

GitHub: [@FabricioPatrocinio22](https://github.com/FabricioPatrocinio22)

---

⭐ Se este projeto foi útil para você, considere dar uma estrela no repositório!
