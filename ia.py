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
        texto_completo = texto_completo[:10000]

        prompt = f"""
        Você é um assistente jurídico sênior. Analise o texto jurídico abaixo extraído de um PDF.
        Crie um resumo estruturado com:
        1. Do que se trata o processo (Assunto).
        2. Principais pontos alegados.
        3. Risco provável (Baixo/Médio/Alto).
        4. Sugestão de próximo passo.

        Texto do documento:
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