import requests
import json
from supabase import create_client, Client
from services.services import generator_uuid 
import os
import time

#Verificando a existencia do lead
def get_lead(useful_variables: str) -> str:
    try:
        user_variables = json.loads(useful_variables)

    except json.JSONDecodeError as e:
        print('Erro ao tentar converter para json')
        with open('erros', 'a')as e:
            e.write(f'Erro ao tentar converter para json {time.time()}')

        error_convertion = json.loads(useful_variables)
        error_convertion['lead_found'] = False
        return  error_convertion
        
    print(user_variables)
    telefone = user_variables['telefone']
    
    # Configuração do Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    supabase: Client = create_client(url, key) #type: ignore
    
    try:
        # Fazer consulta GET na tabela 'leads'

        response = supabase.table('clientes_cadastro').select("*").eq('numero', f'{telefone}').execute()
        if response.data:
            user_variables['lead_found'] = True
            
            user_variables['session_id'] = response.data[0]['session_id']
            return json.dumps(user_variables)

        else:
            user_variables['lead_found'] = False
            return json.dumps(user_variables)


            
    except Exception as e:
        
        print(f"Erro ao consultar Supabase: {e}")
        user_variables['lead_found'] = False

        with open('erros', 'a')as e:
            e.write(f'Erro ao tentar buscar lead no supabase{time.time()}')
        return json.dumps(user_variables)
    

# Criar novo lead no Supabase
def create_lead_db(useful_variables: str) -> str:
    try:
        user_variables = json.loads(useful_variables)
    except json.JSONDecodeError as e:
        print('Erro ao tentar converter para json')
        with open('erros', 'a') as f:
            f.write(f'Erro ao tentar converter para json {time.time()}\n')
        return json.dumps({"error": "JSON decode error", "lead_created": False})
        
    print(f"Criando lead com dados: {user_variables}")
    telefone = user_variables.get('telefone')
    
    # Configuração do Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    supabase: Client = create_client(url, key) #type: ignore
    
    # Gerar session_id único para o novo lead
    session_id = generator_uuid()
    
    try:
        # Dados para inserir na tabela clientes_cadastro
        lead_data = {
            "numero": telefone,
            "session_id": session_id
        }
        
        # Inserir lead na tabela clientes_cadastro
        response = supabase.table('clientes_cadastro').insert(lead_data).execute()
        
        if response.data:
            print(f"Lead criado com sucesso: {response.data}")
            user_variables['lead_created'] = True
            user_variables['session_id'] = session_id
            return json.dumps(user_variables)
        else:
            print("Erro ao criar lead - resposta vazia")
            user_variables['lead_created'] = False
            return json.dumps(user_variables)
            
    except Exception as e:
        print(f"Erro ao criar lead no Supabase: {e}")
        user_variables['lead_created'] = False
        with open('erros', 'a') as f:
            f.write(f'Erro ao tentar criar lead no supabase {time.time()}: {str(e)}\n')
        return json.dumps(user_variables)
