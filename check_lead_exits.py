import requests
import json
from supabase import create_client, Client
import os

def check_lead_exits(useful_variables: str):
    try:
        user_variables = json.loads(useful_variables)
    except json.JSONDecodeError as e:
        print('Erro ao tentar converter para json')
        return None
        
    print(user_variables)
    telefone = user_variables['telefone']
    
    # Configuração do Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    supabase: Client = create_client(url, key)
    
    try:
        # Fazer consulta GET na tabela 'leads'
        response = supabase.table('leads').select("*").eq('telefone', telefone).execute()
        
        if response.data:
            print(f"Lead encontrado: {response.data}")
            return {"exists": True, "data": response.data}
        else:
            print("Lead não encontrado")
            return {"exists": False, "data": None}
            
    except Exception as e:
        print(f"Erro ao consultar Supabase: {e}")
        return {"error": str(e)}
