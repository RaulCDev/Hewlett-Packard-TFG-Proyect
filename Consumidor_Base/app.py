import os

from flask import Flask, redirect, request, jsonify, url_for
from pymongo import MongoClient
from flask_cors import CORS, cross_origin
import re
import json

#Creamos la aplicacion de Flask
app = Flask(__name__)

#Cambiamos en la configuracion de la aplicacion de Flask la la direccion de la base de datos mongo
client = MongoClient(os.environ["MONGO_URI"])

#Nombre de la base de datos que creamos dentro del docker
db = client['projectCDS']
#Nombre del documento en el que vamos a guardar a los usuarios
collection = db['juegos']

@cross_origin()
@app.route('/save_games', methods=['POST'])
def guardar_juegos():
    # Obtener el JSON de la solicitud HTTP POST
    games = request.get_json()

    if games:
        # Lista para almacenar los juegos que serán insertados
        new_games = []
        for game in games:
            # Extraer el porcentaje de la cadena de texto en "reviewSummary"
            if 'reviewSummary' in game:
                match = re.search(r'(\d+)%', game['reviewSummary'])
                if match:
                    percentage = int(match.group(1))  # convertir la cadena de texto extraída a un número entero
                    game['reviewPercentage'] = percentage  # añadir el porcentaje como un nuevo parámetro
            else:
                game['reviewPercentage'] = None  # O el valor que prefieras en caso de que 'reviewSummary' no esté presente

            # Comprobar si el juego ya está en la colección
            print(game)
            if game.get("appId") is None:
                existing_game = "No tiene appId"#Añadiendo algun valor no introduce el juego en la lista
            else:
                appid = game["appId"]
                existing_game = collection.find_one({"appId": appid})

            # Si el juego no está en la colección, añadirlo a la lista de nuevos juegos
            if existing_game is None:
                new_games.append(game)

        # Insertar todos los juegos nuevos en la colección de MongoDB
        if new_games:
            collection.insert_many(new_games)
            return {"success": True, "message": "Juegos guardados correctamente."}
        else:
            return {"success": False, "message": "Todos los juegos ya están registrados en la base de datos."}
    else:
        return {"success": False, "message": "No se recibió JSON en la solicitud."}

if __name__ == '__main__':
    app.run(debug=True, port=4002, host="0.0.0.0")
