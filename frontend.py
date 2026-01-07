import streamlit as st
import requests
from datetime import date
import os
import base64

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
    opcao = st.sidebar.radio("Ir para:", ["Dashboard", "Novo Processo", "Meus Processos", "Configurações"])
    
    if st.sidebar.button("Sair"):
        del st.session_state["token"]
        st.rerun()

    # --- TELA 1: DASHBOARD ---
    if opcao == "Dashboard":
        st.header("📊 Visão Geral")
        st.markdown("Visão geral estratégica do seu escritório.")
        
        try:
            res = requests.get(f"{BASE_URL}/dashboard/geral", headers=headers)

            if res.status_code == 200:
                dados = res.json()

                #--- LINHA 1: KPIs (Indicadores Chave) ---
                col1, col2, col3, col4 = st.columns(4)

                col1.metric("Total de Processos", dados["total"])
                col2.metric("Ativos", dados["ativos"])
                col3.metric("Concluídos", dados["concluidos"])

                # Destaque vermelho para vencidos
                col4.metric("⚠️ Prazos Vencidos", dados["vencidos"], delta_color="inverse")

                st.divider()

                # --- LINHA 2: GRÁFICOS E PRAZOS ---
                col_grafico, col_prazos = st.columns([1, 2])

                with col_grafico:
                    st.subheader("Status dos Processos")
                    # Gráfico simples de barras
                    st.bar_chart(dados["grafico_status"])

                with col_prazos:
                    st.subheader("📅 Próximos Prazos (30 dias)")

                    lista_prazos = dados["proximos_prazos"]

                    if lista_prazos:

                        for p in lista_prazos:
                            dias = p["dias_restantes"]

                            # Define a cor do alerta baseada nos dias
                            cor_alerta = "🔴" if dias <= 5 else "🟡" if dias <= 15 else "🟢"
                            msg_dias = "HOJE!" if dias == 0 else f"em {dias} dias"

                            with st.container(border=True):
                                col_a, col_b = st.columns([3, 1])
                                col_a.markdown(f"**{cor_alerta} Processo {p['numero']}**")
                                col_a.caption(f"Cliente: {p['cliente']}")
                                col_b.write(f"**{msg_dias}**")
                                col_b.caption(f"{p['data']}")
                    else:
                        st.success("Tudo tranquilo! Nenhum prazo crítico para os próximos 30 dias.")

            else:
                st.error("Erro ao carregar dados do dashboard.")
        except Exception as e:
            st.error(f"Erro de conexão: {e}")

    # --- TELA 2: NOVO PROCESSO ---
    elif opcao == "Novo Processo":
        st.header("📝 Cadastrar Processo")

        # 1. Inicializa o estado se não existir
        if "form_numero" not in st.session_state: st.session_state["form_numero"] = ""
        if "form_cliente" not in st.session_state: st.session_state["form_cliente"] = ""
        if "form_parte" not in st.session_state: st.session_state["form_parte"] = ""
        if "form_data" not in st.session_state: st.session_state["form_data"] = date.today()

        # --- ÁREA DE UPLOAD ---
        with st.expander("✨ Preenchimento Automático com IA (Opcional)", expanded=True):
            st.caption("Suba o PDF inicial para a IA tentar ler os dados.")
            arquivo_pdf = st.file_uploader("Arraste o PDF aqui", type="pdf", key="upload_inicial")

            if arquivo_pdf is not None:
                if st.button("🪄 Extrair Dados do PDF"):
                    with st.spinner("A IA está lendo o documento..."):
                        files = {"arquivo": arquivo_pdf.getvalue()}
                        try:
                            res = requests.post(f"{BASE_URL}/ia/extrair-dados", files=files, headers=headers)
                            
                            if res.status_code == 200:
                                dados_ia = res.json()
                                
                                # Atualiza Textos
                                st.session_state["form_numero"] = dados_ia.get("numero_processo") or ""
                                st.session_state["form_cliente"] = dados_ia.get("cliente") or ""
                                st.session_state["form_parte"] = dados_ia.get("contra_parte") or ""
                                
                                # --- CORREÇÃO DA DATA AQUI ---
                                raw_date = dados_ia.get("data_prazo")
                                try:
                                    # Tenta converter string ISO (2025-01-01) para objeto Date
                                    if raw_date:
                                        nova_data = date.fromisoformat(raw_date)
                                    else:
                                        nova_data = date.today()
                                except ValueError:
                                    # Se a IA mandou data mal formatada, usa hoje
                                    nova_data = date.today()
                                
                                st.session_state["form_data"] = nova_data
                                st.success("Dados extraídos!")
                                st.rerun() # Força recarregar a página para exibir os dados novos
                            else:
                                st.error("Erro ao ler o PDF.")
                        except Exception as e:
                            st.error(f"Erro de conexão: {e}")

        st.divider()

        # --- O FORMULÁRIO ---
        with st.form("form_processo"):
            
            # Garante que 'value' seja sempre um objeto data, nunca string
            valor_data_seguro = st.session_state["form_data"]
            if not isinstance(valor_data_seguro, date):
                valor_data_seguro = date.today()

            numero = st.text_input("Número do Processo", value=st.session_state["form_numero"])
            cliente = st.text_input("Nome do Cliente", value=st.session_state["form_cliente"])
            parte = st.text_input("Contra-parte", value=st.session_state["form_parte"])
            data_prazo = st.date_input("Data do Prazo Fatal", value=valor_data_seguro)
            
            enviar = st.form_submit_button("Salvar Processo")
            
            if enviar:
                payload = {
                    "numero": numero,
                    "cliente": cliente,
                    "contra_parte": parte,
                    "data_prazo": str(data_prazo)
                }
                res = requests.post(f"{BASE_URL}/processos", json=payload, headers=headers)
                
                if res.status_code == 200:
                    st.success(f"Processo {numero} criado com sucesso!")
                    
                    # --- LIMPEZA DE DADOS APÓS SALVAR ---
                    st.session_state["form_numero"] = ""
                    st.session_state["form_cliente"] = ""
                    st.session_state["form_parte"] = ""
                    st.session_state["form_data"] = date.today() # Reseta a data para hoje
                    
                    # Opcional: sleep breve e rerun para dar sensação de atualização
                    st.rerun()
                else:
                    st.error(f"Erro: {res.text}")

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
                    tab_detalhes, tab_chat = st.tabs(["📄 Detalhes & Arquivos", "💬 Chat Jurídico (IA)"])

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

                        # Edição Rápida
                        with col_edit:
                            with st.popover("✏️ Editar Dados"):
                                with st.form(key=f"edit_{p['id']}"):
                                    n_status = st.selectbox("Status", ["Em Andamento", "Concluído", "Suspenso"])
                                    if st.form_submit_button("Salvar"):
                                        requests.put(f"{BASE_URL}/processos/{p['id']}", json={"status": n_status}, headers=headers)
                                        st.rerun()
                        
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