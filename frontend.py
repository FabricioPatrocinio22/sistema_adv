import streamlit as st
import requests
from datetime import date
import os

# Endereço do seu Backend (FastAPI)
BASE_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

# Configuração da Página
st.set_page_config(page_title="Sistema Jurídico", page_icon="⚖️")

# --- FUNÇÕES AUXILIARES ---
def fazer_login(email, senha, codigo_2fa=None):
    # O FastAPI espera um formulário (data), não JSON
    payload = {"username": email, "password": senha}
    params = {}
    if codigo_2fa:
        params = {"otp": codigo_2fa}
    
    try:
        response = requests.post(f"{BASE_URL}/login", data=payload, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        st.error("Erro ao conectar com o servidor. O Backend está ligado?")
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
    opcao = st.sidebar.radio("Ir para:", ["Dashboard", "Novo Processo", "Meus Processos"])
    
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
        
        with st.form("form_processo"):
            numero = st.text_input("Número do Processo")
            cliente = st.text_input("Nome do Cliente")
            parte = st.text_input("Contra-parte")
            data_prazo = st.date_input("Data do Prazo Fatal")
            
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
                else:
                    st.error(f"Erro: {res.text}")

    # --- TELA 3: MEUS PROCESSOS E UPLOAD ---
    elif opcao == "Meus Processos":
        st.header("📂 Gestão de Processos")
        
        # Lista todos os processos
        res = requests.get(f"{BASE_URL}/processos", headers=headers)
        if res.status_code == 200:
            processos = res.json()
            
            for p in processos:
                with st.expander(f"Processo: {p['numero']} - {p['cliente']}"):
                    st.write(f"**Contra-parte:** {p['contra_parte']}")
                    st.write(f"**Prazo:** {p['data_prazo']}")
                    st.write(f"**Status:** {p['status']}")
                    
                    # Se já tiver arquivo
                    if p.get("arquivo_pdf"):
                        st.info("✅ Este processo já tem anexo.")
                        # Aqui poderíamos botar o botão de download
                        link_download = f"{BASE_URL}/processos/{p['id']}/download"
                        st.markdown(f"[📥 Baixar Arquivo Atual]({link_download})")
                    
                    # Área de Upload
                    st.divider()
                    st.write("📤 **Anexar Documento**")
                    arquivo = st.file_uploader("Escolha um PDF", key=f"uploader_{p['id']}")
                    
                    if arquivo and st.button("Enviar Arquivo", key=f"btn_{p['id']}"):
                        files = {"arquivo": arquivo}
                        res_upload = requests.post(
                            f"{BASE_URL}/processos/{p['id']}/anexo", 
                            headers=headers, 
                            files=files
                        )
                        if res_upload.status_code == 200:
                            st.success("Arquivo enviado!")
                            st.rerun()
                        else:
                            st.error("Erro no envio.")

                    #delete button
                    st.divider()
                    col_del1, col_del2 = st.columns([3, 1])
                    with col_del2:
                        
                        if st.button("🗑️ Excluir Processo", key=f"del_{p['id']}", type="primary"):
                            res_del = requests.delete(f"{BASE_URL}/processos/{p['id']}", headers=headers)
                            if res_del.status_code == 200:
                                st.success("Processo apagado!")
                                st.rerun() # Recarrega a tela para sumir da lista
                            else:
                                st.error("Erro ao excluir.")

                    st.divider()
                    st.write("✏️ **Editar Dados**")

                    if st.checkbox("Alterar dados deste processo", key=f"check_edit_{p['id']}"):
                        with st.form(key=f"form_edit_{p['id']}"):

                            novo_numero = st.text_input("Número", value=p['numero'])
                            novo_cliente = st.text_input("Cliente", value=p['cliente'])
                            nova_parte = st.text_input("Contra-parte", value=p['contra_parte'])
                            novo_status = st.selectbox("Status", ["Em Andamento", "Concluido", "Suspenso"], index=0)

                            btn_salvar = st.form_submit_button("Salvar Alterações")

                            if btn_salvar:
                                payload_edit = {
                                    "numero": novo_numero,
                                    "cliente": novo_cliente,
                                    "contra_parte": nova_parte,
                                    "status": novo_status
                                }

                                res_edit = requests.put(
                                    f"{BASE_URL}/processos/{p['id']}",
                                    json=payload_edit,
                                    headers=headers
                                )

                                if res_edit.status_code == 200:
                                    st.success("Dados atualizados!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar.")

                    st.divider()
                    st.write("🧠 **Inteligência Artificial**")

                    # 1. Se o banco já tem um resumo salvo, mostra ele na tela
                    if p.get("resumo_ia"):
                        st.info(f"**Análise da IA:**\n\n{p['resumo_ia']}")

                    # 2. Botão para pedir uma nova análise
                    # O key=f"..." é obrigatório para não confundir os botões de processos diferentes
                    if st.button("🤖 Analisar Documento com IA", key=f"btn_ia_{p['id']}"):

                        # Mostra um "carregando" enquanto a IA pensa
                        with st.spinner("Lendo o PDF e consultando o Gemini..."):
                            try:

                                res_ia = requests.post(
                                    f"{BASE_URL}/processos/{p['id']}/analise-ia", 
                                    headers=headers
                                )
                                
                                if res_ia.status_code == 200:
                                    st.success("Análise Concluída!")
                                    st.rerun() # Recarrega a página para o resumo aparecer
                                elif res_ia.status_code == 400:
                                    st.warning("⚠️ Este processo precisa de um PDF anexado antes.")
                                else:
                                    st.error(f"Erro ao analisar: {res_ia.text}")
                            except Exception as e:
                                st.error("Erro de conexão com o backend.")