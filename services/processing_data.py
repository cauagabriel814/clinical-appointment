from services.monitore_queues import monitor_rabbitmq_queue
import json
import traceback


class ProcessingFile():

    def __init__(self, body :str) :
        self.body = body 



    def get_variable(self):
        useful_variables = {}
        try:
            object_webhook = json.loads(self.body)
        except json.JSONDecodeError as e:
            print(f'Erro ao converter arquivo json: {e}')
            return None
        
        try: 
            conversation = object_webhook['body']['data']["message"].get("conversation")
            audio_message = object_webhook['body']['data']["message"].get("audioMessage")
            if conversation is not None:
                useful_variables = {
                    'mensagem_text': True,
                    'telefone': object_webhook['body']['data']['key']['remoteJid'],
                    'chatwoot_id':object_webhook['body']['data']['chatwootConversationId'],
                    'mensagem' : object_webhook['body']['data']["message"]["conversation"],
                    'fromMe' :  object_webhook['body']['data']['key']['fromMe']
                }
            elif audio_message is not None: 
                useful_variables = {
                    'mensagem_audio': True,
                    'telefone': object_webhook['body']['data']['key']['remoteJid'],
                    'chatwoot_id':object_webhook['body']['data']['chatwootConversationId'],
                    'mensagem' : object_webhook['body']['data']["message"]["base64"],
                    'fromMe' :  object_webhook['body']['data']['key']['fromMe']
                    }
            else :
                useful_variables = {
                    'mensagem_Imagem': True,
                    'telefone': object_webhook['body']['data']['key']['remoteJid'],
                    'chatwoot_id':object_webhook['body']['data']['chatwootConversationId'],
                    'mensagem' : object_webhook['body']['data']["message"]["base64"],
                    'fromMe' :  object_webhook['body']['data']['key']['fromMe']
                    }


        except Exception as e:
            print('Deu erro ',e)
            traceback.print_exc()

        return json.dumps(useful_variables)
