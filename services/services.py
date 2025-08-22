import uuid

def generator_uuid()-> str:
    uuid_aleatorio = uuid.uuid4()
    return str(uuid_aleatorio)

print(generator_uuid())