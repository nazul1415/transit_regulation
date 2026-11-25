import Constants from 'expo-constants';
import { Platform } from 'react-native';

const PUERTO_API = 8080;

/**
 * URL base del API.
 * 1. EXPO_PUBLIC_API_URL (producción o dispositivo con otra red).
 * 2. Desarrollo: el mismo host de la PC que sirve Expo (funciona en teléfono real y simulador).
 * 3. Emulador de Android: 10.0.2.2 es la PC; iOS: localhost.
 */
export function apiBaseUrl(): string {
  const env = process.env.EXPO_PUBLIC_API_URL;
  if (env) return env.replace(/\/$/, '');

  const hostUri = Constants.expoConfig?.hostUri;
  if (hostUri) return `http://${hostUri.split(':')[0]}:${PUERTO_API}`;

  return Platform.OS === 'android' ? `http://10.0.2.2:${PUERTO_API}` : `http://localhost:${PUERTO_API}`;
}

/** /v1/consultas puede tardar si el LLM es lento. */
export const TIMEOUT_CONSULTA_MS = 90_000;
export const TIMEOUT_BUSQUEDA_MS = 20_000;
