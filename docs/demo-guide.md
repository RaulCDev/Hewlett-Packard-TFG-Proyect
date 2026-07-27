# Guion de demostración

## Preparación

```powershell
docker compose up --build --detach --force-recreate
docker compose ps --all
```

Espera a que todos los servicios persistentes indiquen `healthy`. `injector` debe
mostrar `Exited (0)`. Comprueba el sembrado con:

```powershell
docker compose logs injector consumidor
```

En la salida se verán la fuente, `published=571` y los lotes persistidos, nunca la
clave de RapidAPI.

## Recorrido sugerido para el vídeo

1. Abre http://localhost:3000 y entra en Registro.
2. Crea un usuario local y accede con correo y contraseña.
3. En Home enseña el catálogo, la ordenación, una búsqueda y la lista de deseados.
4. Si el estado indica `fixture`, explica el modal: la aplicación sigue operativa
   con datos locales aunque falte la clave o falle Steam2.
5. En Login pulsa Google. Con las credenciales actuales debe abrirse el consentimiento
   de Google; sin ellas aparece el modal que enumera `GOOGLE_CLIENT_ID` y/o
   `GOOGLE_CLIENT_SECRET`.
6. Muestra Eureka en http://localhost:8761 para visualizar `Log-In`, `Data` y el
   gateway registrados.

## Demostración explícita sin credenciales

`.env.example` deja vacías las integraciones externas:

```powershell
docker compose --env-file .env.example up --build --detach --force-recreate
```

Registra/inicia sesión localmente, abre Home para ver el modal RapidAPI y vuelve a
Login para ver el modal Google. Los juegos continúan disponibles.

Para recuperar el `.env` normal:

```powershell
docker compose up --build --detach --force-recreate
```

No grabes la pantalla mientras editas `.env`, ni muestres la URL OAuth completa o
los logs con datos de usuario.
