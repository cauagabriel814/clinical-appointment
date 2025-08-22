from .treating import analyze_image, trancribe_audio
import json
import time

def classifying_mensagem(useful_variables: str):
    try:
        user_variables = json.loads(useful_variables)

    except json.JSONDecodeError as e:
        print('Erro ao tentar converter para json')
        with open('erros', 'a')as e:
            e.write(f'Erro ao tentar converter para json time: {time.time()}')

        error_convertion = json.loads(useful_variables)
        return  error_convertion
    
    if 'mensagem_Imagem' in user_variables: 
        image_content = analyze_image(user_variables['mensagem'])
        user_variables['mensagem'] = image_content
        new_user_variable = user_variables
        return json.dumps(new_user_variable)


    if 'mensagem_audio' in user_variables:
        image_content = trancribe_audio(user_variables['mensagem'])
        user_variables['mensagem'] = image_content
        new_user_variable = user_variables
        return json.dumps(new_user_variable)
    else: 
        return json.dumps(user_variables)
            