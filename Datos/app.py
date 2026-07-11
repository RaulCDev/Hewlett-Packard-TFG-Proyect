import asyncio
import os
import time
from urllib.parse import urlencode
import re

import jwt
from flask import Flask, redirect, request, jsonify
from functools import wraps
from py_eureka_client.eureka_client import EurekaClient
from pymongo import MongoClient


#Creamos la aplicacion de Flask
app = Flask(__name__)
#Llave secreta para los JWT
SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = 'HS256'

#Cambiamos en la configuracion de la aplicacion de Flask la la direccion de la base de datos mongo
client = MongoClient(os.environ["MONGO_URI"])

#Nombre de la base de datos que creamos dentro del docker
db = client['projectCDS']
#Nombre del documento en el que vamos a guardar a los usuarios
collection_juegos = db['juegos']
collection_usuarios = db['usuarios']


def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"message": "Missing authorization header"}), 401

        try:
            auth_scheme, token = auth_header.split()
            if auth_scheme.lower() != "bearer":
                return jsonify({"message": "Invalid authorization scheme"}), 401
        except ValueError:
            return jsonify({"message": "Invalid authorization header"}), 401

        try:
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            request.user = decoded_token["identity"]
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return fn(*args, **kwargs)

    return wrapper

#==================================================================================================================================
# Datos
#==================================================================================================================================

def format_game(game):
    # Limpiar y formatear la información del juego
    formatted_game = {
        "appId": (game["appId"]),
        "title": game["title"],
        "url": game["url"],
        "imgUrl": game["imgUrl"],
        "released": game["released"],
        "reviewSummary": None,
        "originalPrice": None,
        "discountedPrice": None
    }

    # Procesar el campo "reviewSummary"
    if "reviewSummary" in game:
        match = re.search(r'(\d+)%', game["reviewSummary"])
        if match:
            formatted_game["reviewSummary"] = match.group(1) + "%"
        else:
            formatted_game["reviewSummary"] = "No review summary available"
            
    # Procesar el campo "price"
    if "price" in game:
        prices = game["price"].strip().split('\u20ac')
        # Quitar espacios vacíos
        prices = [price.strip() for price in prices if price.strip() != '']
        if len(prices) == 1:
            # Si solo hay un precio, es un juego gratuito o no tiene descuento
            formatted_game["originalPrice"] = prices[0] + '\u20ac'
        elif len(prices) == 2:
            # Si hay dos precios, el primero es el original y el segundo es el precio con descuento
            formatted_game["originalPrice"] = prices[0] + '\u20ac'
            formatted_game["discountedPrice"] = prices[1] + '\u20ac'
    return formatted_game

@app.route('/games', methods=['GET'])
@jwt_required
def games():
    # Obtén los 50 juegos con la puntuación más alta sin el campo _id
    top_games = list(collection_juegos.find({"released": {"$nin": ["Coming soon", "To be announced"]}}, {'_id': 0}).sort([('porcentaje_votos', -1)]).limit(50))
    lista_juegos = [format_game(juego) for juego in top_games]
    return jsonify(lista_juegos)  # Usa jsonify para convertir la lista en una respuesta JSON válida

@app.route('/search_games', methods=['GET'])
@jwt_required
def search_games():
    search_term = request.args.get('q', '')
    search_results = collection_juegos.find({"title": {"$regex": search_term, "$options": 'i'}})

    # Convertir Cursor de MongoDB a una lista de diccionarios
    results_list = [format_game(game) for game in search_results]

    return jsonify(results_list)


#Pedir toda la lista de favoritos del usuario
@app.route('/favorite', methods=['GET'])
@jwt_required
def favorite():
    current_user = request.user
    user_data = collection_usuarios.find_one({"correo": current_user})
    return jsonify(user_data.get('wishlist', []))

#Buscar todos los juegos de la lista de deseados del usuario para devolverlos como una lista
@app.route('/favorite/favorite_games', methods=['GET'])
@jwt_required
def favorite_games():
    # Obtén el correo del usuario actual a través del token
    current_user = request.user

    # Busca al usuario en la base de datos
    user_data = collection_usuarios.find_one({"correo": current_user})

    # Obten la lista de deseos del usuario
    wishlist = user_data.get('wishlist', [])

    # Busca en la base de datos de juegos todos los juegos cuyos ID están en la lista de deseos
    wishlist_games = list(collection_juegos.find({"appId": {"$in": wishlist}}))

    # Formatea los juegos para la respuesta
    wishlist_games = [format_game(game) for game in wishlist_games]
    print(wishlist_games)
    return jsonify(wishlist_games)


#Añadir juego a la lista de favoritos
@app.route('/favorite/add/<game_id>', methods=['POST'])
@jwt_required
def add_to_favorite(game_id):
    current_user = request.user
    collection_usuarios.update_one(
        {"correo": current_user},
        {"$addToSet": {"wishlist": game_id}}
    )
    return jsonify({"message": "Game added to wishlist"})

#Borrar juego de la lista de favoritos del usuario
@app.route('/favorite/remove/<game_id>', methods=['DELETE'])
@jwt_required
def remove_from_favorite(game_id):
    current_user = request.user
    collection_usuarios.update_one(
        {"correo": current_user},
        {"$pull": {"wishlist": game_id}}
    )
    return jsonify({"message": "Game removed from wishlist"})

#Pedir datos del usuario
@app.route('/user_data', methods=['GET'])
@jwt_required
def data():
    current_user = request.user
    print(current_user)

    # Consulta para buscar un usuario con un correo electrónico específico
    consulta = {'correo': current_user}

    # Contar el número de resultados que coinciden con la consulta
    num_resultados = collection_usuarios.count_documents(consulta)
    if num_resultados == 1:
        existing_user = collection_usuarios.find(consulta)
        for resultado in existing_user:
            nombre = resultado['nombre']
        return {'message': nombre}
    else:
        print('Hay mas de uno o ningun resultado, cuando solo se quiere uno')
        return {'message': 'Hay mas de uno o ningun resultado, cuando solo se quiere uno'}


#Funcion que nos conecta al servicio de erureka y en la que le decimos en que puerto esta escuchando el microservicio
def configure_eureka(app_name, eureka_server, port, instance_ip):
    async def start_eureka_client():
        eureka_client = EurekaClient(app_name=app_name, eureka_server=eureka_server, instance_port=port, instance_ip=instance_ip)
        await eureka_client.start()

    asyncio.run(start_eureka_client())

#En el inicio de la aplicacion de flask iniciamos tambien la conexion con eureka
if __name__ == '__main__':
    #Id de la conexion con eureka
    app_name = 'Data'
    eureka_server = "http://eureka:8761/eureka"
    port = 4001
    instance_ip = "datos"

    #Hacemos que espere 30 segundos para que eureka pueda iniciar antes de que conecte
    time.sleep(60)
    configure_eureka(app_name, eureka_server, port, instance_ip)
    app.run(debug=True, port=port, host="0.0.0.0")
