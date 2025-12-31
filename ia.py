from google import genai
from pypdf import PdfReader
import os

API_KEY = "AIzaSyC7WQczLzlFCX7bOS9kat0t8A9YwLqlEUo"


def analisar_documento(caminho_pdf):
    """
    1. Abre o PDF.
    2. Extrai o texto.
    3. Manda pro Gemini resumir.
    """
    try:
        #Extrai o pdf
        leitor = PdfReader(caminho_pdf)
        texto_completo = ""
        for pagina in leitor.pages:
            texto_completo += pagina.extract_text() or ""

        #limite de segurança
        texto_completo = texto_completo[:15000]

        if not texto_completo.strip():
            return "Erro: O PDF parece estar vazio ou é imagem."

        prompt = f"""
        Atue como um Advogado Sênior especialista em Triagem Processual.
        Abaixo, você receberá o texto extraído de um arquivo PDF jurídico. Este arquivo pode conter múltiplos documentos (Petição, Procuração, Comprovantes, Sentença, etc.).
        
        Sua missão é filtrar o ruído e focar no andamento processual.
        
        DIRETRIZES:
        1. IDENTIFICAÇÃO: Primeiro, identifique qual é a peça PRINCIPAL deste PDF (Ex: Petição Inicial, Contestação, Sentença, Despacho ou apenas Documento Administrativo).
        2. FILTRAGEM: Ignore documentos acessórios como Procurações, Substabelecimentos e Guias de Pagamento, a menos que haja um vício neles.
        3. SITUAÇÃO ATUAL: Com base APENAS neste documento, em que fase o processo parece estar?
        
        SAÍDA ESPERADA (Formate em Markdown):
        
        **Tipo de Documento Identificado:** [Nome da Peça Principal]
        
        **Resumo dos Fatos Relevantes:**
        [Resumo focado apenas na argumentação jurídica ou decisão judicial]
        
        **Status/Situação Processual:**
        [Explique em 1 frase a fase atual. Ex: "Processo aguardando citação", "Aguardando Sentença", "Recurso Interposto"]
        
        **Pontos de Atenção/Riscos:**
        [Se houver riscos, cite. Se for apenas um documento simples, diga "Sem riscos aparentes"]

        ---
        TEXTO DO ARQUIVO:
        {texto_completo}
        """

        # 3. Chamar a IA (SINTAXE NOVA CORRIGIDA)
        client = genai.Client(api_key=API_KEY)

        # Na biblioteca nova, chamamos client.models.generate_content
        response = client.models.generate_content(
            model="models/gemini-3-flash-preview", 
            contents=prompt
        )
        
        return response.text

    except Exception as e:
        print(f"ERRO IA: {e}")
        return f"Erro ao analisar IA: {str(e)}"