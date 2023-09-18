# Importar la biblioteca pymongo
import pymongo

client = pymongo.MongoClient('mongodb+srv://paubellonch99:YSsMTs3NLtkDCkC5@cluster0.xdne2xq.mongodb.net/?retryWrites=true&w=majority')
db = client['autos']  # Nombre de la base de datos
data_preprocessing_autocasion = db['autos']  # Nombre de la colección
data_todownload= db['autos_todownload']
FIELD_NAME = "_id"

variable=False
if variable ==True:
    # 1. Obtener todos los `_id` de `data_preprocessing_autocasion`
    ids_in_autocasion = [doc['_id'] for doc in data_preprocessing_autocasion.find({}, {"_id": 1})]

    # 2. Eliminar los documentos de `data_todownload` que tengan un `_id` que coincida con los de `data_preprocessing_autocasion`
    result = data_todownload.delete_many({"_id": {"$in": ids_in_autocasion}})
    print(f"{result.deleted_count} documentos eliminados de data_todownload.")

    # 3. Añadir los documentos restantes (únicos) de `data_todownload` a `data_preprocessing_autocasion`
    unique_documents_to_add = list(data_todownload.find({}))
    if unique_documents_to_add:
        data_preprocessing_autocasion.insert_many(unique_documents_to_add)
        print(f"{len(unique_documents_to_add)} documentos añadidos a data_preprocessing_autocasion.")
else:
    count_original = data_preprocessing_autocasion.count_documents({})
    count_new = data_todownload.count_documents({})

    print(f"Total de documentos en original: {count_original}")
    print(f"Total de documentos en nuevo: {count_new}")
    # Ahora puedes eliminar documentos usando collection.delete_many({}) y document_count seguirá siendo un entero.
    #data_todownload.delete_many({})

    """
    print("\nDatos en 'autos_todownload':")
    for doc in data_todownload.find():
        print(doc)
    """