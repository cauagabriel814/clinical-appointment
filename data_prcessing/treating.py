
from langchain_openai import ChatOpenAI
import openai
import base64
from io import BytesIO
from PIL import Image
import requests
from langchain.schema import HumanMessage, AIMessage
import os
import tempfile
from dotenv import load_dotenv
import time
from datetime import datetime

# Inicializar modelo com vis�o
load_dotenv()
llm = ChatOpenAI(
    model="gpt-4o",  # ou gpt-4-vision-preview
    openai_api_key=os.getenv("OPENAI_API_KEY") #type: ignore
)

# Configurar cliente OpenAI para transcrição
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Usar com LangChain
def analyze_image(image_path, prompt="Resumo curto da imagem. Responda sem acento, sem hifens"):
    image_base64 = image_path
    try: 
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        )
        response = llm.invoke([message])
    except: 
        with open('erros', 'a') as a:
            a.write(f'Erro ao tentar converterimagem: {str(a)} - {time.time()}\n')

    
    return response.content

def trancribe_audio(audio_base64, file_extension='mp3'):
    """Função para transcrever audios com a LLM"""


    #Decodificar Base64 e transformando em binario novamente
    audio_data = base64.b64decode(audio_base64)
    
    # Criando arquivo temporario

    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
        #Salvando arquivo
        temp_file.write(audio_data)
        temp_file_path = temp_file.name

    try:
        #transcrevendo audio
        with open(temp_file_path, "rb") as audio_file:
            trancribe_audio = client.audio.transcriptions.create(
            #Modelo que transcreve audio da openIA
            model= 'whisper-1',
            file= audio_file,
            language='pt'
        )
        return trancribe_audio.text
    except Exception as e:
        with open('erros', 'a') as a:
            a.write(f'Erro ao tentar converter audio: {str(e)} - {time.time()}\n')
        return None

    finally:
        #Excluindo arquivo temporario sempre
        os.unlink(temp_file_path)
