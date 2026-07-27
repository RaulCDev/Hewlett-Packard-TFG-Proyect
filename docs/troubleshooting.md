# Resolución de problemas

## Diagnóstico inicial

```powershell
docker compose config --quiet
docker compose ps --all
docker compose logs --tail 150 NOMBRE_DEL_SERVICIO
```

`injector` con `Exited (0)` no es un error. Códigos distintos de cero requieren
revisar `docker compose logs injector`.

## Puerto ocupado

Si aparece `port is already allocated`, identifica contenedores anteriores:

```powershell
docker ps --all --format "{{.Names}} {{.Status}} {{.Ports}}"
```

Detén el Compose antiguo que sea propietario de esos contenedores y repite el
arranque. No borres volúmenes si necesitas conservar usuarios/favoritos.

## El frontend no refleja una variable nueva

`NEXT_PUBLIC_API_BASE_URL` se compila en el bundle de Next. Usa:

```powershell
docker compose up --build --detach --force-recreate front-next
```

Para Google/RapidAPI también conviene recrear los backends:

```powershell
docker compose up --build --detach --force-recreate login datos injector
```

## Google

- Confirma ambas variables sin imprimir sus valores.
- En Google Cloud, el redirect debe coincidir carácter por carácter con
  `http://localhost:8081/api/login/callback`.
- El origen JavaScript es `http://localhost:3000`.
- Si la aplicación OAuth está en modo de prueba, añade la cuenta como usuario de
  prueba en Google Cloud.
- Un error `Invalid Google OAuth state` suele indicar cookies bloqueadas o que se
  inició el callback en otra sesión; permite cookies para localhost y reintenta
  desde el botón.

Prueba de inicio del flujo sin mostrar la URL generada:

```powershell
curl.exe --silent --output NUL --write-out "%{http_code}" http://localhost:8081/api/login/user/login/google
```

Debe devolver 200 con credenciales completas o 503 si faltan.

## RapidAPI y catálogo vacío

Consulta el estado:

```powershell
curl.exe --silent http://localhost:8081/api/data/integration-status
docker compose logs injector consumidor consumidor-base
```

`source: fixture` es válido. Si `configured` es `true` y el motivo es
`live_api_unavailable`, la clave existe pero el proveedor no respondió. En julio
de 2026 el endpoint publicado `steam2.p.rapidapi.com/search/{term}/page/{page}`
devolvía 404, por lo que la aplicación usaba automáticamente los 571 registros
locales.

Si Mongo está vacío, vuelve a ejecutar el sembrado y mantén el consumidor activo:

```powershell
docker compose up --detach consumidor consumidor-base kafka
docker compose run --rm injector
```

## Reinicio total de datos

Solo cuando quieras borrar usuarios, favoritos y juegos locales:

```powershell
docker compose down --volumes --remove-orphans
docker compose up --build --detach
```
