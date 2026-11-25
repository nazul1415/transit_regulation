# App móvil (Android / iOS)

Cliente en React Native (Expo SDK 58, Expo Router, TypeScript) del API del Reglamento de Tránsito de la CDMX. Dos pantallas:

- **Preguntar** → `POST /v1/consultas`: resumen del LLM + citas verificadas con texto literal, sanciones en UMA y pesos.
- **Buscar** → `GET /v1/busqueda`: búsqueda híbrida sin LLM (sirve aunque el LLM falle).

## Requisitos
Node 20+ y la app **Expo Go** en tu teléfono (o un emulador de Android / simulador de iOS). El API debe estar corriendo en el puerto 8080 de tu PC.

## Correr
```bash
cd mobile
npm install
npx expo start        # escanea el QR con Expo Go
npm run typecheck
```

## A qué URL se conecta (`src/api/config.ts`)
1. `EXPO_PUBLIC_API_URL`, si está definida (p. ej. el dominio HTTPS de producción).
2. En desarrollo, la misma IP de tu PC que sirve Expo, puerto 8080 (funciona con teléfono real).
3. Emulador de Android: `http://10.0.2.2:8080`. Simulador de iOS: `http://localhost:8080`.

El teléfono y la PC deben estar en la misma red, y el firewall de Windows debe permitir conexiones entrantes al puerto 8080.

## Contratos del API
`src/api/types.ts` replica a mano los esquemas de `app/api/schemas.py` y `app/domain/models.py`. Si cambias un esquema del API, actualiza ese archivo (el OpenAPI está en `/openapi.json`).

## Antes de publicar en tiendas
- El API necesita HTTPS (iOS y Android bloquean HTTP en builds de producción).
- Autenticación y límites de uso: sin ellos cualquiera puede gastar la cuota del LLM.
- Builds con EAS (`eas build`), iconos y nombre definitivos en `app.json`.
