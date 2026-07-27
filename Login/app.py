import asyncio
import datetime
import logging
import os
import secrets
from urllib.parse import urlencode

import cachecontrol
import jwt
import google.auth.transport.requests
import requests
from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, request, jsonify, session
from functools import wraps
from google.auth import exceptions as google_auth_exceptions
from google.oauth2 import id_token
from py_eureka_client.eureka_client import EurekaClient
from pymongo import MongoClient

try:
    from .integrations import (
        build_google_authorization_url,
        google_identity_from_claims,
        google_integration_status,
        redact_oauth_callback_log,
    )
except ImportError:
    from integrations import (
        build_google_authorization_url,
        google_identity_from_claims,
        google_integration_status,
        redact_oauth_callback_log,
    )


LOGGER = logging.getLogger("login")


class OAuthCallbackLogFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = redact_oauth_callback_log(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                redact_oauth_callback_log(value)
                if isinstance(value, str)
                else value
                for value in record.args
            )
        return True


logging.getLogger("werkzeug").addFilter(OAuthCallbackLogFilter())



#Creamos la aplicacion de Flask
app = Flask(__name__)
#Llave secreta para los JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "gameshop-development-jwt-secret-change-me")
JWT_ALGORITHM = 'HS256'
app.secret_key = SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


#Le damos "CORS" para poder tratar con el error que suge al hacer peticiones
#CORS(app)


#Cambiamos en la configuracion de la aplicacion de Flask la la direccion de la base de datos mongo
client = MongoClient(os.getenv("MONGO_URI", "mongodb://gameshop:gameshop-development-password@mongo:27017/"))

#Nombre de la base de datos que creamos dentro del docker
db = client['projectCDS']
#Nombre del documento en el que vamos a guardar a los usuarios
collection = db['usuarios']


oauth = OAuth(app)
#Variables de Google
GOOGLE_CALLBACK_URI = os.getenv(
    "GOOGLE_CALLBACK_URI", "http://localhost:8081/api/login/callback"
)
FRONTEND_GOOGLE_SUCCESS_URI = os.getenv(
    "FRONTEND_GOOGLE_SUCCESS_URI", "http://localhost:3000/inicio_exitoso_google"
)

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

#OPERACIONES
#==================================================================================================================================
# REGISTRO Y LOGIN PLATAFORMA
#==================================================================================================================================
#Funcion que llamamos desde el front despues del incio de sesion(Tiene que verificar el token(Otra funcion) y devolver la informacion que deba)


@app.route('/user/datapls', methods=['GET'])
@jwt_required
def requestuser():
    print(request.headers.get('Authorization'))
    current_user = request.user
    print(current_user)

    # Consulta para buscar un usuario con un correo electrónico específico
    consulta = {'correo': current_user}

    # Contar el número de resultados que coinciden con la consulta
    num_resultados = collection.count_documents(consulta)
    if num_resultados == 1:
        existing_user = collection.find(consulta)
        for resultado in existing_user:
            nombre = resultado['nombre']
        return {'message': nombre}
    else:
        print('Hay mas de uno o ningun resultado, cuando solo se quiere uno')
        return {'message': 'Hay mas de uno o ningun resultado, cuando solo se quiere uno'}


#REGISTOR USUARIOS
@app.route('/user/register', methods=['POST'])
def registerUser():
    data = request.json
    #Buscamos si existe ese usuario en la base de datos
    existing_user = collection.find_one({'correo': data['correo']})
    #Condicion que comprueba si lo que hemos buscado en la base de datos esta vacio
    if existing_user:
        return {'message': 'El usuario ya existe en la base de datos'}
    else:
        collection.insert_one(data)
        return {'message': 'Deberia estar guardado'}

#INICIO DE SESION USUARIOS
@app.route('/user/login', methods=['POST'])
def loginUser():
    data = request.json
    correo = data['correo']
    contrasenia = data['contrasenia']
    #Comprobamos que ay algun dato en el correo y contraseña que nos a enviado
    if not data or not correo or not contrasenia:
        return ({'massage': 'No se puede verificar faltan datos'})

    #Buscamos el usuario en la base de datos y si existe devolvemos el JWT para que inicie la sesion
    user = collection.find_one({'correo': correo, 'contrasenia': contrasenia})

    if user:
        return {'token': create_token(user["correo"])}

    return {'message': "NO EXISTE"}

def create_token(identity):
    expires_delta = None
    if expires_delta:
        expires = datetime.datetime.utcnow() + expires_delta
    else:
        expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)

    payload = {
        "identity": identity,
        "exp": expires,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

#==================================================================================================================================
#GOOGLE
#==================================================================================================================================


#Funcion inicial para iniciar sesion con google
@app.route('/user/login/google', methods=['GET'])
def loginUser_Google():
    # Enviar la solicitud de autorizaciÃ³n de Google
    status = google_integration_status(os.environ)
    if not status["configured"]:
        return jsonify(status), 503

    state = secrets.token_urlsafe(32)
    session["google_oauth_state"] = state
    return jsonify({
        "link": build_google_authorization_url(
            os.environ,
            redirect_uri=GOOGLE_CALLBACK_URI,
            state=state,
        )
    })

#Funcion que llama google despues del intento de inicio de sesion
@app.route('/callback')
def oauth2callback():
    # Recuperar el cÃ³digo de autorizaciÃ³n de la solicitud de autorizaciÃ³n de Google
    status = google_integration_status(os.environ)
    if not status["configured"]:
        return jsonify(status), 503

    code = request.args.get('code')
    state = request.args.get('state')
    expected_state = session.pop("google_oauth_state", None)
    if not code:
        return jsonify({"message": "Google did not return an authorization code"}), 400
    if not state or not expected_state or not secrets.compare_digest(state, expected_state):
        return jsonify({"message": "Invalid Google OAuth state"}), 400

    credentials = {
        "code": code,
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "redirect_uri": GOOGLE_CALLBACK_URI,
        "grant_type": "authorization_code",
    }

    # Intercambiar el cÃ³digo de autorizaciÃ³n por un token de acceso y un ID de cliente
    try:
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data=credentials,
            timeout=20,
        )
        response.raise_for_status()
        token_payload = response.json()
        if "id_token" not in token_payload:
            return jsonify({"message": "Google token response did not include an ID token"}), 502
        token = google_get_user_info(token_payload)
    except (requests.RequestException, ValueError, KeyError):
        return jsonify({"message": "Google authentication could not be completed"}), 502

    if not token:
        return jsonify({"message": "Google identity could not be verified"}), 401

    token_str = str(token)
    direccion = f"{FRONTEND_GOOGLE_SUCCESS_URI}?{urlencode({'access_token': token_str})}"
    return redirect(direccion)

# Esta función verifica la identidad del usuario y devuelve la información del usuario del token de Google en concreto
def google_get_user_info(token):
    try:
        # Verificar la identidad del usuario con el token de Google
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        id_info = id_token.verify_oauth2_token(
            id_token=token['id_token'],
            request=token_request,
            audience=os.environ["GOOGLE_CLIENT_ID"]
        )

        # Obtener el correo electrónico y la información del usuario
        identity = google_identity_from_claims(id_info)
        email = identity["email"]
        nombre = identity["name"]

        #Comprobar si existe un usuario con ese correo y sino registrarlo en la base de datos
        user = collection.find_one({"correo": email})
        #Si existe un usuario creamos el token, y sino lo añadimos a la base de datos y despues creamos el token
        if user:
            print('El usuario YA estaba registrado')
            token_google = create_token(email)
            return token_google
        else:
            collection.insert_one({"correo": email, "nombre": nombre})
            token_google = create_token(email)
            print('El usuario NO estaba registrado')
            return token_google

    except (ValueError, KeyError, google_auth_exceptions.GoogleAuthError) as error:
        LOGGER.warning(
            "Google identity verification failed (%s)",
            type(error).__name__,
        )
        return None


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


def get_jwt_identity(encoded_token):
    try:
        decoded_token = jwt.decode(encoded_token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return decoded_token["identity"]
    except jwt.ExpiredSignatureError:
        return None

#Funcion que nos conecta al servicio de erureka y en la que le decimos en que puerto esta escuchando el microservicio
def configure_eureka(app_name, eureka_server, port, instance_ip):
    async def start_eureka_client():
        eureka_client = EurekaClient(app_name=app_name, eureka_server=eureka_server, instance_port=port, instance_ip=instance_ip)
        await eureka_client.start()

    asyncio.run(start_eureka_client())

#En el inicio de la aplicacion de flask iniciamos tambien la conexion con eureka
if __name__ == '__main__':
    #Id de la conexion con eureka
    app_name = 'Log-In'
    eureka_server = "http://eureka:8761/eureka"
    port = 4000
    instance_ip = "login"

    configure_eureka(app_name, eureka_server, port, instance_ip)
    app.run(debug=False, port=port, host="0.0.0.0")
