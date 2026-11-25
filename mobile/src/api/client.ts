import { apiBaseUrl, TIMEOUT_BUSQUEDA_MS, TIMEOUT_CONSULTA_MS } from './config';
import type { BusquedaResponse, Respuesta } from './types';

export class ApiError extends Error {
  constructor(
    message: string,
    readonly estado?: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function pedir<T>(ruta: string, init: RequestInit, timeoutMs: number): Promise<T> {
  const control = new AbortController();
  const temporizador = setTimeout(() => control.abort(), timeoutMs);
  try {
    const res = await fetch(`${apiBaseUrl()}${ruta}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...init.headers },
      signal: control.signal,
    });
    if (!res.ok) {
      throw new ApiError(
        res.status === 422 ? 'La pregunta no es válida (muy corta o muy larga).' : `El servidor respondió ${res.status}.`,
        res.status,
      );
    }
    return (await res.json()) as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e instanceof Error && e.name === 'AbortError') {
      throw new ApiError('La consulta tardó demasiado. Intenta de nuevo.');
    }
    throw new ApiError(`No se pudo conectar con el servidor (${apiBaseUrl()}).`);
  } finally {
    clearTimeout(temporizador);
  }
}

export function consultar(pregunta: string): Promise<Respuesta> {
  return pedir<Respuesta>('/v1/consultas', { method: 'POST', body: JSON.stringify({ pregunta }) }, TIMEOUT_CONSULTA_MS);
}

export function buscar(q: string, topK = 8): Promise<BusquedaResponse> {
  const params = new URLSearchParams({ q, top_k: String(topK) });
  return pedir<BusquedaResponse>(`/v1/busqueda?${params}`, { method: 'GET' }, TIMEOUT_BUSQUEDA_MS);
}
