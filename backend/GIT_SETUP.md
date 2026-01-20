# Configuração do Git e GitHub

## 1. Configure seu Git (se ainda não fez)

Execute os seguintes comandos substituindo com seus dados:

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@exemplo.com"
```

## 2. Faça o commit inicial

O repositório já foi inicializado e os arquivos foram adicionados. Execute:

```bash
git commit -m "Initial commit: Sistema de Advocacia com FastAPI"
```

## 3. Crie um repositório no GitHub

1. Acesse [GitHub](https://github.com) e faça login
2. Clique no botão "+" no canto superior direito
3. Selecione "New repository"
4. Escolha um nome para o repositório (ex: `sistema_advogado`)
5. **NÃO** inicialize com README, .gitignore ou licença (já temos esses arquivos)
6. Clique em "Create repository"

## 4. Conecte seu repositório local ao GitHub

Após criar o repositório no GitHub, execute os comandos que aparecerão na tela. Geralmente são:

```bash
git remote add origin https://github.com/SEU_USUARIO/sistema_advogado.git
git branch -M main
git push -u origin main
```

**Nota:** Se o GitHub pedir autenticação, você pode usar:
- Personal Access Token (recomendado)
- GitHub CLI (`gh auth login`)
- Credenciais do GitHub

## 5. Pronto!

Seu projeto agora está no GitHub! 🎉

