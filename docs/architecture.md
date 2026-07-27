# Arquitectura de GameShop

## Tráfico de la aplicación

El navegador carga Next.js desde `localhost:3000` y consume una única puerta de
entrada, Zuul en `localhost:8081/api`. Zuul localiza los servicios Flask mediante
Eureka:

```text
Navegador :3000
      |
      v
Zuul :8081 ---- Eureka :8761
   |                    ^
   +-- /api/login/* --> Login :4000
   +-- /api/data/*  --> Datos :4001
                             |
                             v
                         MongoDB
```

`Login` gestiona registro, login local, emisión de JWT y OAuth de Google. `Datos`
valida el JWT para juegos, búsquedas, perfil y favoritos. El estado de la fuente
RapidAPI es público en `/api/data/integration-status` para que Home pueda decidir
si muestra el modal.

## Ingesta de juegos

```text
Steam2/RapidAPI --si responde--+
                              |
JSON local --fallback---------+--> Injector --> Kafka (games)
                                               |
                                               v
                                          Consumidor
                                               |
                                               v
                                        Consumidor Base
                                               |
                                               v
                                            MongoDB
```

`Injector` intenta la API únicamente si `RAPIDAPI_KEY` está configurada. Cualquier
respuesta HTTP errónea, contenido no válido o lista vacía activa el fixture local.
Los juegos se deduplican por `appId`, se publican en lotes de 50 y el inyector
finaliza con código 0. `Consumidor` confirma el offset solo después de que
`Consumidor Base` haya persistido el lote. La persistencia es idempotente por
`appId` y registra si la ejecución utilizó `rapidapi` o `fixture`.

## Redes y datos

Compose mantiene dos redes internas: `gateway` para el tráfico web y `kafka` para
la ingesta. MongoDB participa en ambas. Los datos se guardan en el volumen nombrado
`mongo-data`; el código fuente ya no se monta como bind mount dentro de las
imágenes, por lo que el mismo build funciona desde cualquier directorio.

Las credenciales de Mongo/JWT incluidas por defecto son exclusivamente para
desarrollo local. `.env` no se versiona.
