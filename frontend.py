import streamlit as st
import requests
from datetime import date
import os
import base64
import time
import re

# Endereço do seu Backend (FastAPI)
BASE_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

# Configuração da Página
st.set_page_config(page_title="Sistema Jurídico", page_icon="⚖️")

# --- FUNÇÕES AUXILIARES ---
def fazer_login(email, senha, codigo_2fa=None):
    try:
        # O FastAPI (OAuth2) exige que os campos se chamem 'username' e 'password'
        dados = {"username": email, "password": senha}
        
        headers_login = {}
        # Se o usuário digitou algo no campo 2FA, enviamos no cabeçalho
        if codigo_2fa:
            headers_login["codigo_2fa"] = codigo_2fa

        # ATENÇÃO: A rota mudou de /login para /token
        response = requests.post(f"{BASE_URL}/token", data=dados, headers=headers_login)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

def limpar_numero(valor):
    """Remove tudo que não for dígito (pontos, traços, parênteses)"""
    if not valor:
        return ""
    return re.sub(r'\D', '', str(valor))

def formatar_documento(valor):
    """Formata CPF ou CNPJ dependendo do tamanho"""
    v = limpar_numero(valor)
    
    if len(v) == 11: # CPF
        return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
    elif len(v) == 14: # CNPJ
        return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"
    
    return valor # Se não for nem um nem outro, retorna normal

def formatar_telefone(valor):
    """Transforma 11999998888 em (11) 99999-8888"""
    v = limpar_numero(valor)
    if len(v) < 10 or len(v) > 11:
        return valor
    
    if len(v) == 11: # Celular (com 9 dígitos)
        return f"({v[:2]}) {v[2:7]}-{v[7:]}"
    else: # Fixo (com 8 dígitos)
        return f"({v[:2]}) {v[2:6]}-{v[6:]}"
# --- TELA DE LOGIN ---
if "token" not in st.session_state:
    st.title("⚖️ Acesso Restrito")

    tab_login, tab_cadastro = st.tabs(["🔐 Entrar", "📝 Criar Conta"])

    with tab_login:
        st.subheader("Acesse sua conta")
    
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        codigo_2fa = st.text_input("Código 2FA (Opcional se desativado)")
    
        if st.button("Entrar"):
            dados_token = fazer_login(email, senha, codigo_2fa)
            if dados_token:
                st.session_state["token"] = dados_token["access_token"]
                st.success("Login realizado! Recarregando...")
                st.rerun()
            else:
                st.error("E-mail, senha ou código inválidos.")
                
    with tab_cadastro:
        st.subheader("Crie seu acesso")
        with st.form("form_cadastro"):
            novo_email = st.text_input("E-mail para cadastro")
            nova_senha = st.text_input("Crie sua senha", type="password")
            confirmar_senha = st.text_input("Confirme a senha", type="password")

            btn_criar = st.form_submit_button("Criar Conta")

            if btn_criar:
                if nova_senha != confirmar_senha:
                    st.warning("As senhas não coincidem!")
                elif len(nova_senha) < 4:
                    st.warning("A senha é muito curta.")
                else:
                    # Tenta criar
                    payload = {
                        "email": novo_email,
                        "senha": nova_senha
                    }
                    try:
                        res = requests.post(f"{BASE_URL}/usuarios", json=payload)
                        if res.status_code == 200 or res.status_code == 201:
                            st.success("Conta criada com sucesso! Vá para a aba 'Entrar' e faça login.")
                            st.balloons() # Efeito de festa 🎉
                        elif res.status_code == 400:
                            st.error("Erro: Este e-mail já está cadastrado.")
                        else:
                            st.error(f"Erro no servidor: {res.text}")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")

# --- SISTEMA PRINCIPAL (SÓ APARECE SE LOGADO) ---
else:
    token = st.session_state["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Barra Lateral (Menu)
    st.sidebar.title("Menu Advogado")
    opcao = st.sidebar.radio("Ir para:", ["Dashboard", "Novo Processo", "Meus Processos", 'Meus Clientes', "Configurações"])
    
    if st.sidebar.button("Sair"):
        del st.session_state["token"]
        st.rerun()

    # --- TELA 1: DASHBOARD (VISUAL NOVO) ---
    if opcao == "Dashboard":
        st.header("📊 Visão Geral")
        st.markdown("Visão estratégica do escritório em tempo real.")
        
        try:
            res = requests.get(f"{BASE_URL}/dashboard/geral", headers=headers)

            if res.status_code == 200:
                dados = res.json()

                # --- BLOCO 1: OPERACIONAL (PROCESSOS) ---
                with st.container(border=True):
                    st.subheader("📂 Métricas Operacionais")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    col1.metric("Total Processos", dados["total"])
                    col2.metric("Ativos", dados["ativos"])
                    col3.metric("Concluídos", dados["concluidos"])
                    col4.metric("⚠️ Vencidos", dados["vencidos"], delta_color="inverse")

                # --- BLOCO 2: FINANCEIRO (COM MAIS ESPAÇO) ---
                # Usamos um container para agrupar e dar destaque visual
                with st.container(border=True):
                    st.subheader("💰 Controle Financeiro")
                    
                    # Dividimos em 2 colunas grandes em vez de 4 pequenas
                    fin_col1, fin_col2 = st.columns(2)

                    with fin_col1:
                        st.markdown("##### 📈 Receitas")
                        # Faturamento Total
                        st.metric(
                            "Faturamento Previsto (Honorários)", 
                            f"R$ {dados.get('total_pendente', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        )
                        st.divider()
                        # O que já entrou
                        st.metric(
                            "✅ Em Caixa (Recebido)", 
                            f"R$ {dados.get('total_recebido', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                            delta="Entrada Realizada"
                        )

                    with fin_col2:
                        st.markdown("##### 📉 Pendências & Custas")
                        # O que falta receber
                        st.metric(
                            "⏳ A Receber", 
                            f"R$ {dados.get('total_honorarios', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                            delta_color="normal"
                        )
                        st.divider()
                        # Custas
                        valor_custas = dados.get('financeiro_custas', 0)
                        st.metric(
                            "💸 Custas/Despesas", 
                            f"R$ {valor_custas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), 
                            delta="-Saída" if valor_custas > 0 else None,
                            delta_color="inverse"
                        )

                # --- BLOCO 3: GRÁFICOS E PRAZOS ---
                # Mantemos a estrutura de baixo, mas com um espaçamento melhor
                st.write("") # Espaço em branco
                
                col_grafico, col_prazos = st.columns([1, 1.5]) # Ajustei a proporção para o gráfico não ficar espremido

                with col_grafico:
                    with st.container(border=True):
                        st.subheader("Status")
                        if dados["grafico_status"]:
                            st.bar_chart(dados["grafico_status"])
                        else:
                            st.info("Sem dados.")

                with col_prazos:
                    with st.container(border=True):
                        st.subheader("📅 Próximos Prazos (30 dias)")
                        lista_prazos = dados.get("proximos_prazos", [])

                        if lista_prazos:
                            for p in lista_prazos:
                                dias = p["dias_restantes"]
                                cor = "🔴" if dias <= 5 else "🟡" if dias <= 15 else "🟢"
                                msg_dias = "HOJE!" if dias == 0 else f"em {dias} dias"
                                
                                # Cardzinho para cada prazo
                                with st.container():
                                    c_a, c_b = st.columns([3, 1])
                                    c_a.markdown(f"**{cor} {p['numero']}**")
                                    c_a.caption(f"{p['cliente']}")
                                    c_b.write(f"**{msg_dias}**")
                                    c_b.caption(f"{p['data']}")
                                st.divider()
                        else:
                            st.success("Tudo tranquilo! Nenhum prazo crítico.")

            else:
                st.error("Erro ao carregar dados do dashboard.")
        except Exception as e:
            st.error(f"Erro de conexão: {e}")

   # --- TELA: NOVO PROCESSO (COM CRM + IA INTEGRADA) ---
    if opcao == "Novo Processo":
        st.header("⚖️ Cadastrar Novo Processo")

        # 1. INICIALIZA A MEMÓRIA DO FORMULÁRIO (Para os dados não sumirem)
        if "form_dados" not in st.session_state:
            st.session_state["form_dados"] = {
                "numero": "", 
                "contra_parte": "", 
                "data_prazo": date.today() # Padrão hoje
            }
        
        if "cliente_selecionado" not in st.session_state:
            st.session_state["cliente_selecionado"] = None

        # --- 2. SELEÇÃO DE CLIENTE (MODAL DO CRM) ---
        @st.dialog("🔍 Pesquisar Cliente")
        def abrir_modal_clientes(dados_clientes):
            st.write("Selecione o cliente para vincular ao processo:")
            mapa_clientes = {c["nome"]: c for c in dados_clientes}
            nomes = list(mapa_clientes.keys())
            nome_escolhido = st.selectbox("Cliente:", nomes, index=None, placeholder="Digite para buscar...")
            
            if nome_escolhido:
                c_dados = mapa_clientes[nome_escolhido]
                st.info(f"📄 Documento: {c_dados.get('cpf_cnpj', 'N/A')}")
                if st.button("✅ Confirmar Vínculo"):
                    st.session_state["cliente_selecionado"] = nome_escolhido
                    st.rerun()

        # Botão para abrir o Modal
        if st.session_state["cliente_selecionado"]:
            c1, c2 = st.columns([3, 1])
            c1.success(f"👤 Cliente Vinculado: **{st.session_state['cliente_selecionado']}**")
            if c2.button("🔄 Trocar"):
                st.session_state["cliente_selecionado"] = None
                st.rerun()
        else:
            if st.button("🔍 Selecionar Cliente (Obrigatório)"):
                try:
                    res = requests.get(f"{BASE_URL}/clientes", headers=headers)
                    if res.status_code == 200:
                        abrir_modal_clientes(res.json())
                    else:
                        st.error("Erro ao buscar clientes.")
                except:
                    st.error("Erro de conexão.")

        st.divider()

        # --- 3. ÁREA DE UPLOAD (IA) - SÓ APARECE SE TIVER CLIENTE ---
        if st.session_state["cliente_selecionado"]:
            
            st.markdown("#### 🤖 Preenchimento Automático (Gemini 3.0)")
            uploaded_file = st.file_uploader("Arraste a Petição Inicial (PDF) para preencher os campos", type="pdf")
            
            if uploaded_file is not None:
                if st.button("✨ Ler PDF com IA"):
                    with st.spinner("Lendo documento..."):
                        try:
                            # Chama a SUA rota existente: /ia/extrair-dados
                            files = {"arquivo": uploaded_file.getvalue()} # Note que o backend espera 'arquivo'
                            res = requests.post(f"{BASE_URL}/ia/extrair-dados", files=files)
                            
                            if res.status_code == 200:
                                dados_ia = res.json()
                                
                                # --- MAPEAMENTO (O Pulo do Gato) ---
                                # O backend devolve "numero_processo", o form usa "numero"
                                st.session_state["form_dados"]["numero"] = dados_ia.get("numero_processo", "")
                                st.session_state["form_dados"]["contra_parte"] = dados_ia.get("contra_parte", "")
                                
                                # Tenta converter a data que vem da IA (YYYY-MM-DD) para objeto data
                                data_str = dados_ia.get("data_prazo")
                                if data_str:
                                    try:
                                        st.session_state["form_dados"]["data_prazo"] = datetime.strptime(data_str, "%Y-%m-%d").date()
                                    except:
                                        pass # Se falhar, mantém a data de hoje
                                
                                st.toast("Dados extraídos com sucesso!", icon="✅")
                            else:
                                st.error(f"Erro na IA: {res.text}")
                        except Exception as e:
                            st.error(f"Erro de conexão: {e}")

            st.markdown("---")

            # --- 4. FORMULÁRIO FINAL ---
            with st.form("form_processo"):
                c1, c2 = st.columns(2)
                
                # Campos puxando do session_state (Preenchidos pela IA ou Vazios)
                contra_parte = c1.text_input("Contra-parte", value=st.session_state["form_dados"]["contra_parte"])
                numero = c2.text_input("Número do Processo", value=st.session_state["form_dados"]["numero"])
                
                c3, c4 = st.columns(2)
                # Como sua IA atual não extrai o "Tipo de Ação", deixamos manual por enquanto
                tipo_acao = c3.selectbox("Tipo de Ação", ["Cível", "Trabalhista", "Família", "Criminal", "Tributário"])
                data_prazo = c4.date_input("Próximo Prazo", value=st.session_state["form_dados"]["data_prazo"])
                
                submit = st.form_submit_button("💾 Salvar Processo")

                if submit:
                    payload = {
                        "numero": numero,
                        "cliente": st.session_state["cliente_selecionado"], # Usa o cliente do Modal
                        "contra_parte": contra_parte,
                        "tipo_acao": tipo_acao,
                        "status": "Em Andamento",
                        "data_prazo": str(data_prazo)
                    }
                    
                    try:
                        res = requests.post(f"{BASE_URL}/processos", json=payload, headers=headers)
                        if res.status_code == 200:
                            st.balloons()
                            st.success("Processo Criado com Sucesso!")
                            
                            # Reseta o formulário
                            st.session_state["cliente_selecionado"] = None
                            st.session_state["form_dados"] = {"numero": "", "contra_parte": "", "data_prazo": date.today()}
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"Erro: {res.text}")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")
    
    # --- TELA 3: MEUS PROCESSOS E UPLOAD ---
    elif opcao == "Meus Processos":
            st.header("📂 Gestão e Análise")

            # Inicializa histórico de Chat
            if "chat_history" not in st.session_state:
                st.session_state["chat_history"] = {}

            try:
                res = requests.get(f"{BASE_URL}/processos", headers=headers)
                processos = res.json() if res.status_code == 200 else []
            except:
                processos = []
                st.error("Erro ao conectar.")

            for p in processos:
                # Container visual para o processo
                with st.container(border=True):
                    # Cabeçalho do Card
                    c_top1, c_top2 = st.columns([3, 1])
                    c_top1.subheader(f"{p['numero']} - {p['cliente']}")
                    status_color = "red" if p['status'] == "Suspenso" else "green"
                    c_top2.markdown(f"Status: :{status_color}[{p['status']}]")

                    # --- SISTEMA DE ABAS ---
                    tab_detalhes, tab_chat, tab_fin = st.tabs(["📄 Detalhes & Arquivos", "💬 Chat Jurídico (IA)", "💰 Financeiro"])

                    # ABA 1: DETALHES (O que já existia + Upload + Edição)
                    with tab_detalhes:
                        c1, c2 = st.columns(2)
                        c1.write(f"**Contra-parte:** {p['contra_parte']}")
                        c2.write(f"**Prazo:** {p['data_prazo']}")
                        
                        st.divider()
                        
                        # Colunas de Ação
                        col_up, col_edit, col_del = st.columns([2, 2, 1])
                        
                        # Upload
                        with col_up:
                            if not p.get("arquivo_pdf"):
                                arq = st.file_uploader("Anexar PDF", key=f"up_{p['id']}", label_visibility="collapsed")
                                if arq and st.button("Enviar PDF", key=f"btn_up_{p['id']}"):
                                    files = {"arquivo": arq}
                                    requests.post(f"{BASE_URL}/processos/{p['id']}/anexo", headers=headers, files=files)
                                    st.success("Enviado!")
                                    st.rerun()
                            else:
                                st.success(f"✅ Arquivo na Nuvem: {p.get('arquivo_pdf')}")

                                if st.button("📥 Gerar Link de Download", key=f"btn_down_{p['id']}"):
                                    res_link = requests.get(f"{BASE_URL}/processos/{p['id']}/download", headers=headers)
                                    if res_link.status_code == 200:
                                        link = res_link.json()["url_download"]
                                        st.markdown(f"[📥 Baixar Documento]({link})")
                                    else:
                                        st.error("Erro ao gerar link de download.")

                        # Edição Rápida (AGORA COM BUSCA DE CLIENTE INTELIGENTE)
                        with col_edit:
                            with st.popover("✏️ Editar Dados"):
                                st.write(f"Editando: **{p['numero']}**")
                                
                                # Lógica para carregar lista de clientes para o Selectbox
                                try:
                                    res_cli = requests.get(f"{BASE_URL}/clientes", headers=headers)
                                    lista_clientes = res_cli.json() if res_cli.status_code == 200 else []
                                    nomes_clientes = [c["nome"] for c in lista_clientes]
                                except:
                                    nomes_clientes = []

                                with st.form(key=f"edit_{p['id']}"):
                                    # 1. Cliente (Dropdown em vez de texto solto)
                                    # Tenta achar o índice atual do cliente para já vir selecionado
                                    try:
                                        idx_atual = nomes_clientes.index(p['cliente'])
                                    except:
                                        idx_atual = 0
                                    
                                    n_cliente = st.selectbox("Cliente Vinculado", nomes_clientes, index=idx_atual)
                                    
                                    # 2. Status
                                    # Mapear índice do status atual
                                    lista_status = ["Em Andamento", "Concluído", "Suspenso"]
                                    try:
                                        idx_status = lista_status.index(p['status'])
                                    except:
                                        idx_status = 0
                                    n_status = st.selectbox("Status", lista_status, index=idx_status)

                                    # 3. Tipo de Ação (Para corrigir os antigos "Não Informado")
                                    lista_acoes = ["Cível", "Trabalhista", "Família", "Criminal", "Tributário"]
                                    # Tenta achar o índice atual ou usa Cível como padrão
                                    try:
                                        idx_acao = lista_acoes.index(p.get('tipo_acao'))
                                    except:
                                        idx_acao = 0
                                        
                                    n_tipo_acao = st.selectbox("Tipo de Ação", lista_acoes, index=idx_acao)

                                    if st.form_submit_button("💾 Salvar Alterações"):
                                        payload_edit = {
                                            "cliente": n_cliente,
                                            "status": n_status,
                                            "tipo_acao": n_tipo_acao
                                        }
                                        # Envia o PUT para o backend
                                        res_edit = requests.put(f"{BASE_URL}/processos/{p['id']}", json=payload_edit, headers=headers)
                                        
                                        if res_edit.status_code == 200:
                                            st.success("Atualizado!")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(f"Erro: {res_edit.text}")
                        
                        # Excluir
                        with col_del:
                            if st.button("🗑️", key=f"del_{p['id']}", help="Excluir Processo"):
                                requests.delete(f"{BASE_URL}/processos/{p['id']}", headers=headers)
                                st.rerun()

                        #Botao Resumo IA
                        st.divider()
                        st.markdown("#### 🧠 Resumo do Caso (IA)")

                        if p.get("resumo_ia"):
                            st.info(f"**Análise Automática:**\n\n{p['resumo_ia']}")

                        if p.get("arquivo_pdf"):
                            if st.button("🔍 Analisar com IA", key=f"btn_ia_{p['id']}"):
                                with st.spinner("Analisando com IA..."):
                                    try:
                                        res_ia = requests.post(f"{BASE_URL}/processos/{p['id']}/analise-ia", headers=headers)
                                        if res_ia.status_code == 200:
                                            st.success("Análise concluída!")
                                            st.rerun()
                                        else:
                                            st.error("Erro na IA.")
                                    except Exception as e:
                                        st.error(f"Erro de conexão: {e}")
                        else:
                            st.caption("Nenhum PDF anexado. Não é possível usar a IA.")

                    # ABA 2: CHAT COM IA
                    with tab_chat:
                        if not p.get("arquivo_pdf"):
                            st.warning("⚠️ Você precisa anexar um PDF na aba 'Detalhes' para usar o chat.")
                        else:
                            # --- NOVIDADE AQUI: Cabeçalho com Botão de Limpar ---
                            col_titulo_chat, col_btn_limpar = st.columns([4, 1])

                            with col_titulo_chat:
                                st.markdown("##### 🤖 Pergunte sobre este processo")
                            
                            # ID único para o histórico deste processo
                            chat_id = p['id']
                            if chat_id not in st.session_state["chat_history"]:
                                st.session_state["chat_history"][chat_id] = []

                            with col_btn_limpar:
                                if st.button("🧹 Limpar", key=f"clean_chat_{chat_id}", help="Apagar histórico desta conversa"):
                                    st.session_state["chat_history"][chat_id] = []
                                    st.rerun() # Recarrega a tela para sumir as mensagens

                            # 1. Mostra histórico
                            for msg in st.session_state["chat_history"][chat_id]:
                                with st.chat_message(msg["role"]):
                                    st.markdown(msg["content"])

                            # 2. Input do Usuário
                            prompt = st.chat_input("Ex: Qual o valor da causa?", key=f"input_{chat_id}")
                            
                            if prompt:
                                # Mostra msg usuário
                                with st.chat_message("user"):
                                    st.markdown(prompt)
                                st.session_state["chat_history"][chat_id].append({"role": "user", "content": prompt})

                                # Chama Backend
                                with st.spinner("Analisando autos..."):
                                    try:
                                        res_chat = requests.post(
                                            f"{BASE_URL}/processos/{p['id']}/chat", 
                                            json={"pergunta": prompt}, 
                                            headers=headers
                                        )
                                        if res_chat.status_code == 200:
                                            resposta = res_chat.json()["resposta"]
                                        else:
                                            resposta = f"Erro na IA: {res_chat.text}"
                                    except:
                                        resposta = "Erro de conexão com o servidor."

                                # Mostra msg IA
                                with st.chat_message("assistant"):
                                    st.markdown(resposta)
                                st.session_state["chat_history"][chat_id].append({"role": "assistant", "content": resposta})

                    with tab_fin:
                        st.write("#### 💸 Controle de Honorários e Custas")

                        with st.expander("➕ Novo Lançamento", expanded=False):
                            with st.form(key=f"form_fin_{p['id']}"):
                                c_desc, c_valor = st.columns(2)
                                f_desc = c_desc.text_input("Descrição (Ex: Entrada)")
                                f_valor = c_valor.number_input("Valor (R$)", min_value=0.0, step=100.0)

                                c_tipo, c_status, c_data = st.columns(3)
                                f_tipo = c_tipo.selectbox("Tipo", ["Honorários", "Recebido", "Reembolso"])
                                f_status = c_status.selectbox("Status", ["Pendente", "Recebido"])
                                f_data = c_data.date_input("Data Vencimento")

                                if st.form_submit_button("Salvar Lançamento"):
                                    payload_fin = {
                                        "processo_id": p['id'],
                                        "descricao": f_desc,
                                        "valor": f_valor,
                                        "tipo": f_tipo,
                                        "status": f_status,
                                        "data_pagamento": str(f_data)
                                    }
                                    try:
                                        res = requests.post(f"{BASE_URL}/financeiro", json=payload_fin, headers=headers)

                                        if res.status_code == 200:
                                            st.success("✅ Lançamento Salvo!")

                                            time.sleep(1.5)
                                            st.rerun()
                                        else:
                                            st.error(f"Erro ao salvar: {res.text}")

                                    except Exception as e:
                                        st.error(f"Erro de conexão: {e}")
                        
                        try:
                            res_fin = requests.get(f"{BASE_URL}/processos/{p['id']}/financeiro", headers=headers)
                            if res_fin.status_code == 200:
                                lista_fin = res_fin.json()
                                if lista_fin:
                                        # Monta uma tabela simples visual
                                    dados_tabela = []
                                    for item in lista_fin:
                                        dados_tabela.append({
                                            "Data": item["data_pagamento"],
                                            "Descrição": item["descricao"],
                                            "Tipo": item["tipo"],
                                            "Valor": f"R$ {item['valor']:.2f}",
                                            "Status": item["status"]
                                        })
                                    st.table(dados_tabela)
                            else:
                                st.info("Nenhum lançamento financeiro para este processo.")
                        except:
                            st.error("Erro ao carregar financeiro.")

    elif opcao == 'Meus Clientes':
        st.header('👥 Carteira de Clientes')

        tab_add, tab_list = st.tabs(['➕ Novo Cliente', '📋 Lista de Clientes'])

        with tab_add:
            st.markdown("ℹ️ *Digite apenas os números nos campos de documento e telefone.*")
            
            # 1. O RADIO BUTTON FICA FORA DO FORMULÁRIO (Para atualizar na hora)
            tipo_pessoa = st.radio(
                "Tipo de Cliente", 
                ["Pessoa Física (CPF)", "Pessoa Jurídica (CNPJ)"], 
                horizontal=True
            )

            # 2. CALCULA AS VARIÁVEIS ANTES DE CRIAR O FORMULÁRIO
            if tipo_pessoa == "Pessoa Física (CPF)":
                doc_label = "CPF (11 dígitos)"
                doc_max = 11
                doc_placeholder = "12345678900"
                doc_key = "input_cpf"
            else:
                doc_label = "CNPJ (14 dígitos)"
                doc_max = 14
                doc_placeholder = "12345678000199"
                doc_key = "input_cnpj"
            
            with st.form("form_cliente"):
                
                c1, c2 = st.columns(2)
                nome = c1.text_input("Nome / Razão Social *")

                documento = c2.text_input(doc_label, max_chars=doc_max, placeholder=doc_placeholder, key=doc_key)
                # --------------------------------
                
                c3, c4 = st.columns(2)
                email = c3.text_input("E-mail")
                tel = c4.text_input("Celular/Telefone (DDD + Números)", max_chars=11, placeholder='35988887777')
                
                obs = st.text_area("Observações")
                
                if st.form_submit_button("Cadastrar Cliente"):
                    # Validações
                    erro = False
                    
                    if not nome:
                        st.warning("O Nome/Razão Social é obrigatório.")
                        erro = True
                    
                    # Valida se o documento é numérico e se tem o tamanho certo
                    if documento:
                        if not documento.isnumeric():
                            st.error("Erro: O documento deve conter APENAS números.")
                            erro = True
                        elif len(documento) != doc_max:
                            st.error(f"Erro: O {doc_label} deve ter exatamente {doc_max} números.")
                            erro = True

                    if tel and not tel.isnumeric():
                        st.error("Erro: O telefone deve conter APENAS números.")
                        erro = True

                    if not erro:
                        payload = {
                            "nome": nome,
                            "cpf_cnpj": documento,
                            "email": email,
                            "telefone": tel,
                            "observacoes": obs
                        }
                        
                        try:
                            res = requests.post(f"{BASE_URL}/clientes", json=payload, headers=headers)
                            if res.status_code == 200:
                                st.success(f"Cliente cadastrado com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Erro no servidor: {res.text}")
                        except Exception as e:
                            st.error(f"Erro de conexão: {e}")

        with tab_list:
            # 1. Carrega a lista simples para o seletor
            res = requests.get(f"{BASE_URL}/clientes", headers=headers)
            if res.status_code == 200:
                clientes = res.json()
                
                if not clientes:
                    st.info("Nenhum cliente cadastrado.")
                else:
                    # Seletor para escolher quem investigar
                    opcoes = {c["nome"]: c["id"] for c in clientes}
                    escolhido_nome = st.selectbox("📂 Selecione um cliente para ver o Dossiê:", [""] + list(opcoes.keys()))
                    
                    st.divider()

                    if escolhido_nome:
                        id_cliente = opcoes[escolhido_nome]
                        
                        # Chama a rota inteligente que criamos (Dossiê)
                        try:
                            res_dossie = requests.get(f"{BASE_URL}/clientes/{id_cliente}/dossie", headers=headers)
                            if res_dossie.status_code == 200:
                                dados = res_dossie.json()
                                cli = dados["cliente"]
                                fin = dados["financeiro"]
                                procs = dados["processos_lista"]
                                
                                # --- CABEÇALHO DO CLIENTE ---
                                col_perfil, col_kpi = st.columns([1, 2])
                                
                                with col_perfil:
                                    st.subheader(cli["nome"])
                                    st.caption(f"Desde: {cli['data_cadastro']}")
                                    st.write(f"📞 **Tel:** {formatar_telefone(cli.get('telefone', ''))}")
                                    st.write(f"📧 **Email:** {cli.get('email', '-')}")
                                    st.write(f"🆔 **Doc:** {formatar_documento(cli.get('cpf_cnpj', ''))}")
                                    if cli.get("observacoes"):
                                        st.info(cli["observacoes"])
                                
                                with col_kpi:
                                    # Cards Financeiros do Cliente
                                    k1, k2, k3 = st.columns(3)
                                    k1.metric("Processos", dados["qtd_processos"])
                                    k2.metric("Honorários Totais", f"R$ {fin['total']:,.2f}")
                                    k3.metric("Em Aberto (Deve)", f"R$ {fin['devendo']:,.2f}", delta_color="inverse")
                                
                                st.divider()
                                
                                # --- LISTA DE PROCESSOS DELE ---
                                st.subheader(f"Processos de {escolhido_nome}")
                                if procs:
                                    # Tabela simplificada dos processos dele
                                    lista_proc_visual = []
                                    for p in procs:
                                        lista_proc_visual.append({
                                            "Número": p.get("numero", "-"), # Usa .get para garantir
                                            
                                            # AQUI ERA O ERRO: Trocamos ["tipo_acao"] por .get(...)
                                            "Ação": p.get("tipo_acao", "Não Informado"), 
                                            
                                            "Status": p.get("status", "-"),
                                            "Próx. Prazo": p.get("data_prazo", "-")
                                        })
                                    st.dataframe(lista_proc_visual, width='stretch')
                                else:
                                    st.warning("Este cliente ainda não tem processos cadastrados.")
                                    
                            else:
                                st.error("Erro ao carregar dossiê.")
                        except Exception as e:
                            st.error(f"Erro: {e}")
                    else:
                        # Se não selecionou ninguém, mostra a tabela geral resumida
                        st.caption("Visão Geral da Carteira:")
                        df_clientes = [{"Nome": c["nome"], "Telefone": formatar_telefone(c["telefone"])} for c in clientes]
                        st.dataframe(df_clientes, width='stretch')
            else:
                st.error("Erro ao conectar.")

    elif opcao == "Configurações":
        st.header("⚙️ Configurações da Conta")

        st.subheader("🔐 Autenticação de Dois Fatores (2FA)")
        st.write("Aumente a segurança da sua conta exigindo um código do celular.")

        if st.button("Ativar/Ver meu QR Code 2FA"):
            res = requests.post(f"{BASE_URL}/2fa/setup", headers=headers)

            if res.status_code == 200:
                dados_2fa = res.json()
                b64_img = dados_2fa["qr_code_b64"]
                segredo = dados_2fa["segredo"]
                
                # Exibe o QR Code decodificando o Base64
                st.image(base64.b64decode(b64_img), caption="Escaneie com Google Authenticator")
                st.info(f"Se não conseguir ler, digite este código no app: {segredo}")
                st.success("2FA Configurado! No próximo login, o código será exigido.")
            else:
                st.error("Erro ao gerar QR Code.")