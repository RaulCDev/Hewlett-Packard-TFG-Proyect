# Docker Compose portable y credenciales opcionales

## Objetivo

El proyecto debe poder iniciarse en una máquina con Docker mediante `docker compose up --build` aunque no exista un archivo `.env`. Las integraciones de Google OAuth y RapidAPI se conservarán: cuando sus credenciales estén configuradas se utilizarán con normalidad y, cuando falten, la aplicación seguirá siendo demostrable con mensajes explícitos para el usuario.

## Alcance

- Reparar las imágenes, puertos, rutas, montajes y dependencias de arranque que actualmente impiden ejecutar la composición de forma reproducible.
- Proporcionar valores locales de desarrollo para MongoDB y JWT, sin convertirlos en recomendaciones para producción.
- Hacer opcionales únicamente las credenciales externas de Google y RapidAPI.
- Mantener el registro y el inicio de sesión local, Google OAuth, la carga de juegos, la búsqueda y los favoritos.
- Añadir un dataset local amplio procedente de respuestas reales de `steam2.p.rapidapi.com`, obtenido usando la clave local del propietario y sin guardar la clave ni cabeceras sensibles.
- Documentar la arquitectura, los modos de ejecución, la obtención de credenciales y el recorrido de demostración.

No se migrarán los microservicios a otro framework ni se sustituirán Kafka, Eureka, Zuul o MongoDB. Tampoco se abordarán en este cambio mejoras no necesarias para la demostración, como el hash de contraseñas antiguas o una modernización completa de Spring.

## Enfoque elegido

Se aplicará una reparación conservadora de la arquitectura existente. Docker Compose seguirá levantando todos los servicios originales, pero utilizará imágenes fijadas y disponibles, comprobaciones de salud o reintentos en vez de esperas rígidas, rutas con el uso correcto de mayúsculas y puertos coherentes.

Se descartaron dos alternativas:

1. Obligar a usar `.env` y proporcionar solamente mensajes de error. Es más sencillo, pero no cumple el requisito de arrancar en cualquier máquina sin credenciales externas.
2. Eliminar Kafka, Eureka y los microservicios para crear una aplicación monolítica de demostración. Reduciría el tiempo de arranque, pero cambiaría sustancialmente el proyecto que se quiere presentar.

## Configuración y secretos

Docker Compose aceptará estas variables opcionales:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `RAPIDAPI_KEY`
- `RAPIDAPI_HOST`, con `steam2.p.rapidapi.com` como valor predeterminado

Los valores vacíos y los marcadores de ejemplo se considerarán “no configurados”. El archivo `.env.example` explicará cuáles pueden quedar vacíos. MongoDB y JWT tendrán valores predeterminados explícitamente marcados como exclusivos para desarrollo, de modo que un clon nuevo pueda arrancar sin crear `.env`. Un `.env` local podrá reemplazar todos esos valores.

Ninguna credencial se enviará al navegador, se escribirá en logs, se incluirá en el dataset ni se añadirá a Git.

## Google OAuth

El servicio Login leerá las variables de Google con valores opcionales. El endpoint que inicia OAuth tendrá dos respuestas:

- Con `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`: devuelve la URL de autorización y mantiene el flujo actual de código de autorización y callback.
- Sin una o ambas variables: devuelve HTTP 503 y un JSON estable que indica `service: "google"`, `configured: false` y los nombres de las credenciales ausentes.

El botón “Iniciar sesión con Google” interpretará esa respuesta. Si faltan credenciales, abrirá un modal centrado en la propia página y no intentará abrir la ventana de Google. El modal indicará que se necesitan `GOOGLE_CLIENT_ID` y/o `GOOGLE_CLIENT_SECRET`, cómo incorporarlas al `.env` y que se debe recrear el servicio.

El callback seguirá siendo exactamente `http://localhost:8081/api/login/callback` en desarrollo. El frontend aceptará mensajes del popup únicamente desde `http://localhost:3000` y eliminará el listener después de recibir la respuesta o cerrar el popup.

## RapidAPI y dataset local

El Injector separará la selección de fuente, la lectura del JSON, la petición HTTP y la publicación en Kafka en funciones comprobables.

- Si `RAPIDAPI_KEY` está configurada, consultará la API `Steam` de RapidAPI en el host configurado y enviará sus lotes válidos a Kafka.
- Si no está configurada, leerá `Injector/data/rapidapi-steam-games.json` y publicará esos mismos lotes en Kafka.
- Una respuesta HTTP inválida no se publicará como si fuera una lista de juegos. En desarrollo se recurrirá al dataset local para mantener la aplicación utilizable y se registrará el motivo sin mostrar secretos.

El JSON tendrá un objeto de metadatos con el proveedor, host, endpoints consultados, fecha de captura y la declaración de que la clave no está incluida. Los juegos conservarán los campos consumidos por el proyecto: `appId`, `title`, `url`, `imgUrl`, `released`, `reviewSummary` y `price` cuando estén presentes.

El servicio Datos expondrá un endpoint público de estado de integración a través del gateway. Informará si RapidAPI está configurada y qué fuente se espera utilizar. Al entrar en la página principal, el frontend consultará ese estado. Si la fuente es el JSON local, mostrará una vez por carga un modal centrado que explique que falta `RAPIDAPI_KEY`, que se están mostrando datos de respaldo y dónde configurarla.

El almacenamiento calculará `reviewPercentage` y la consulta de juegos utilizará ese mismo nombre al ordenar, corrigiendo la discrepancia actual con `porcentaje_votos`.

## Modal reutilizable

El frontend incorporará un único componente accesible para ambos avisos. Tendrá fondo superpuesto, panel centrado, título, descripción, lista de variables ausentes y botón “Entendido”. Permitirá cerrarse con el botón, la tecla Escape o pulsando fuera del panel, devolverá el foco al elemento que lo abrió y declarará los atributos ARIA de diálogo.

Los textos serán específicos:

- Google: la funcionalidad no está disponible hasta configurar las credenciales.
- RapidAPI: la aplicación sigue funcionando con el dataset local, pero la carga en vivo necesita la clave.

## Arranque reproducible

La composición se ajustará para:

- utilizar imágenes con versiones explícitas y disponibles;
- compilar los servicios Java con una imagen Temurin 11 compatible;
- evitar depender de finales de línea ejecutables del wrapper Maven;
- corregir el puerto de Datos a `4001` y el puerto expuesto de Login a `4000`;
- eliminar montajes de desarrollo incorrectos o hacerlos coincidir con los directorios de trabajo;
- esperar a MongoDB, Kafka y Eureka mediante healthchecks, reintentos o condiciones de salud apropiadas;
- hacer que Next escuche en `0.0.0.0` dentro del contenedor;
- evitar nombres de contenedor globales que colisionen con otras composiciones;
- mantener los puertos de acceso del usuario: frontend `3000`, gateway `8081` y Eureka `8761`.

La primera carga puede tardar mientras se construyen Maven y npm y se inserta el dataset. La documentación distinguirá ese estado de un fallo.

## Flujo de datos

1. Compose arranca infraestructura y servicios respetando sus dependencias reales.
2. Injector decide entre RapidAPI y el JSON local.
3. Injector publica lotes de juegos en `games`.
4. Consumidor entrega cada lote a Consumidor Base.
5. Consumidor Base normaliza y guarda en MongoDB sin duplicar `appId`.
6. Datos consulta MongoDB y sirve juegos, búsquedas y favoritos a través de Zuul.
7. El frontend consulta el estado de integración y presenta el modal correspondiente sin bloquear el uso del fallback.

## Tratamiento de errores

- La ausencia de credenciales externas nunca impedirá crear los contenedores.
- Los endpoints de configuración devolverán JSON estable y códigos HTTP explícitos.
- Las respuestas de RapidAPI se validarán como listas antes de enviarlas a Kafka.
- Los procesos que dependen de Kafka, Eureka o MongoDB reintentarán la conexión con límites y mensajes claros.
- El frontend gestionará respuestas no JSON, errores de red y popups bloqueados con mensajes comprensibles.
- El dataset local se validará durante las pruebas para impedir que un JSON corrupto llegue a Kafka.

## Pruebas y aceptación

La implementación se considerará aceptada cuando se hayan comprobado estos escenarios:

1. `docker compose config` funciona sin `.env`.
2. `docker compose up --build` inicia toda la composición sin credenciales de Google o RapidAPI.
3. El dataset local termina almacenado y el endpoint de juegos devuelve elementos después de registrar e iniciar sesión con un usuario local.
4. La página principal muestra el modal de RapidAPI y continúa mostrando juegos del JSON.
5. El botón de Google muestra el modal de Google cuando faltan sus credenciales y no abre un popup inválido.
6. Con credenciales configuradas, el endpoint de Google devuelve una URL de autorización válida y RapidAPI es la fuente seleccionada.
7. Las pruebas automatizadas de Python y frontend, el build de Next y las pruebas Java finalizan correctamente.
8. La documentación permite repetir ambos modos sin conocer previamente el proyecto.

La verificación con credenciales reales no imprimirá sus valores. Si una integración externa no puede completar un consentimiento o una llamada por restricciones de la cuenta, se documentará el punto exacto alcanzado y la respuesta externa sanitizada.

