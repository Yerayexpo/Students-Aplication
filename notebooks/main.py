from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://goner10:tetete@cluster1.jsr8w0n.mongodb.net/?retryWrites=true&w=majority"

# Crear un nuevo cliente y conectar al servidor
client = MongoClient(uri, server_api=ServerApi('1'))

# Enviar un ping para confirmar una conexión exitosa
try:
    client.admin.command('ping')
    print("¡Ping a tu implementación exitoso! Te has conectado correctamente a MongoDB.")
except Exception as e:
    print(e)

db = client.get_database("test")
collection = db["users"]

# Obtener todos los documentos de la colección
print("Todos los documentos de la colección:")
for doc in collection.find():
    print(doc)

# Cerrar la conexión
client.close()