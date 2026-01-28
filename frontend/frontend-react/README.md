# Frontend – Sistema de Advocacia ⚖️

Aplicação **React + Vite** que serve como interface web moderna para o sistema de gestão de processos jurídicos.  
Ela consome a API FastAPI do backend para autenticação, cadastro de usuários, processos, clientes e módulo financeiro.

## ✨ Principais Funcionalidades

- **Tela de login e cadastro** com feedback visual (toasts)
- **Integração com API** via `axios` usando `VITE_API_URL`
- **Dashboard**, **Processos**, **Clientes** e **Financeiro**
- **UI moderna** construída com **Chakra UI**
- **Navegação** entre páginas com **React Router**

## 🛠️ Tecnologias

- **React**
- **Vite**
- **Chakra UI**
- **React Router DOM**
- **Axios**

## 📦 Instalação

Na raiz do repositório principal você terá a pasta `frontend/frontend-react`.  
Entre nela e instale as dependências:

```bash
cd frontend/frontend-react
npm install
```

## ⚙️ Configuração – Variáveis de Ambiente

Crie um arquivo `.env` dentro de `frontend-react` com:

```bash
VITE_API_URL=http://localhost:8000
```

Ajuste a URL conforme o endereço/porta onde seu backend FastAPI estiver rodando.

## 🚀 Executando o Frontend

Ainda dentro da pasta `frontend-react`, execute:

```bash
npm run dev
```

Por padrão, a aplicação ficará disponível em `http://localhost:5173`.

Certifique-se de que o **backend FastAPI** também esteja em execução para que as funcionalidades de login, cadastro e consulta de dados funcionem corretamente.
