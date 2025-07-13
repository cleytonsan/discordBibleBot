# interactive_bible_bot.py
import os
import requests
import google.generativeai as genai
import datetime
import pytz
import random
import re
import discord
from discord.ext import commands

# --- Configurações das Chaves/Tokens ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# --- Verificação de Segurança ---
if not GOOGLE_API_KEY:
    print("ERRO: GOOGLE_API_KEY não encontrada nas variáveis de ambiente.")
    exit(1)
if not DISCORD_BOT_TOKEN:
    print("ERRO: DISCORD_BOT_TOKEN não encontrado nas variáveis de ambiente.")
    exit(1)

# --- Configuração da API do Google Gemini ---
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Dicionário de Livros da Bíblia e seus capítulos ---
bible_books_chapters = {
    "Gênesis": 50, "Êxodo": 40, "Levítico": 27, "Números": 36, "Deuteronômio": 34,
    "Josué": 24, "Juízes": 21, "Rute": 4, "1 Samuel": 31, "2 Samuel": 24,
    "1 Reis": 22, "2 Reis": 25, "1 Crônicas": 29, "2 Crônicas": 36, "Esdras": 10,
    "Neemias": 13, "Ester": 10, "Jó": 42, "Salmos": 150, "Provérbios": 31,
    "Eclesiastes": 12, "Cantares de Salomão": 8, "Isaías": 66, "Jeremias": 52, "Lamentações": 5,
    "Ezequiel": 48, "Daniel": 12, "Oséias": 14, "Joel": 3, "Amós": 9,
    "Obadias": 1, "Jonas": 4, "Miquéias": 7, "Naum": 3, "Habacuque": 3,
    "Sofonias": 3, "Ageu": 2, "Zacarias": 14, "Malaquias": 4,
    "Mateus": 28, "Marcos": 16, "Lucas": 24, "João": 21, "Atos": 28,
    "Romanos": 16, "1 Coríntios": 16, "2 Coríntios": 13, "Gálatas": 6, "Efésios": 6,
    "Filipenses": 4, "Colossenses": 4, "1 Tessalonicenses": 5, "2 Tessalonicenses": 3,
    "1 Timóteo": 6, "2 Timóteo": 4, "Tito": 3, "Filemom": 1, "Hebreus": 13,
    "Tiago": 5, "1 Pedro": 5, "2 Pedro": 3, "1 João": 5, "2 João": 1,
    "3 João": 1, "Judas": 1, "Apocalipse": 22
}

def generate_prayer() -> str:
    prompt = """Gere uma breve oração (máximo 4 frases) em português para ser feita antes da leitura da Bíblia. A oração deve pedir entendimento, sabedoria e iluminação espiritual para compreender a Palavra de Deus. Use um tom reverente e devocional. Comece com '🙏🏽' e termine com '🙏🏽'."""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if not text.startswith('🙏🏽'):
            text = '🙏🏽 ' + text
        if not text.endswith('🙏🏽'):
            text = text + ' 🙏🏽'
        return text
    except Exception as e:
        print(f"Erro ao gerar oração: {e}")
        return "Erro ao gerar oração. 🙏🏽"

def get_verse_and_explanation_from_gemini(book_chapter_verse: str) -> tuple[str, str, str]:
    prompt = f"""
    Para a passagem bíblica "{book_chapter_verse}" da Bíblia Sagrada, faça o seguinte:

    1.  Apresente o versículo completo, incluindo a referência (Ex: João 3:16).
    2.  Depois, explique o significado **desse versículo e do seu contexto no capítulo**, em termos do que Deus quer nos dizer hoje.
    3.  A explicação deve ter entre 80 e 150 palavras, em um tom inspirador, reflexivo e teologicamente correto.
    4.  Formate sua resposta exatamente assim, com os rótulos em MAIÚSCULAS e seguidos de dois pontos, e as seções separadas por uma linha vazia. Não inclua texto adicional.
        VERSICULO_REFERENCIA: [O versículo com a referência, ex: Gênesis 1:1]

        VERSICULO_TEXTO: [O texto completo do versículo]

        EXPLICACAO: [A explicação do versículo e capítulo]
    """
    try:
        response = model.generate_content(prompt)
        text_response = response.text.strip()

        ref_match = re.search(r"VERSICULO_REFERENCIA:\s*(.*?)(?=\n\n|$)", text_response, re.DOTALL)
        text_match = re.search(r"VERSICULO_TEXTO:\s*(.*?)(?=\n\n|$)", text_response, re.DOTALL)
        expl_match = re.search(r"EXPLICACAO:\s*(.*?)$", text_response, re.DOTALL)

        versiculo_referencia = ref_match.group(1).strip() if ref_match else "Referência não encontrada."
        versiculo_texto = text_match.group(1).strip() if text_match else "Texto do versículo não encontrado."
        explicacao = expl_match.group(1).strip() if expl_match else "Explicação não gerada."

        return versiculo_referencia, versiculo_texto, explicacao

    except Exception as e:
        print(f"Erro ao obter versículo e explicação do Gemini: {e}")
        return "Erro", "Erro", f"Erro ao gerar conteúdo bíblico: {e}. Verifique as logs."

# --- Configuração do Bot Discord ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} conectado ao Discord!')
    print(f'ID: {bot.user.id}')
    print('Aguardando comandos...')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Desculpe, esse comando não existe. Use `!biblia <livro> <capítulo>:<versículo>` (ex: `!biblia Gênesis 1:1`)")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Por favor, forneça a referência bíblica. Ex: `!biblia João 3:16`")
    else:
        print(f'Erro no comando: {error}')
        await ctx.send(f'Ocorreu um erro inesperado ao processar seu comando.')

@bot.command(name='biblia', help='Envia uma oração, um versículo bíblico e sua explicação. Uso: !biblia <Livro> <Capítulo>:<Versículo> (ex: !biblia João 3:16)')
async def biblia(ctx, *, reference: str):
    await ctx.send(f"Buscando a passagem **{reference}** para você... Por favor, aguarde alguns segundos.")

    oracao = generate_prayer()
    versiculo_ref, versiculo_texto, explicacao = get_verse_and_explanation_from_gemini(reference)

    agora = datetime.datetime.now(tz=pytz.timezone('America/Sao_Paulo'))

    mensagem_discord = f"""
    **Mensagem Bíblica Solicitada ({agora.strftime('%d/%m/%Y %H:%M:%S')} Horário de SP):**

    1. {oracao}

    2. 📚**{versiculo_ref}**📚
    {versiculo_texto}

    3. 📝**Explicação:**📝
    {explicacao}
    """

    await ctx.send(mensagem_discord)

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
    
