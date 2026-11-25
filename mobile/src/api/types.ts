// Contratos del API (app/api/schemas.py y app/domain/models.py). Mantener sincronizados.

export interface RangoUma {
  min: number;
  media: number | null;
  max: number;
}

export interface Sanciones {
  multa_uma: RangoUma[];
  puntos: number[];
  deposito_vehicular: boolean;
  arresto: boolean;
  amonestacion: boolean;
}

export interface MultaEnPesos {
  uma_min: number;
  uma_max: number;
  pesos_min: number;
  pesos_max: number;
}

/** Campos comunes de una cita (/v1/consultas) y de un fragmento (/v1/busqueda). */
export interface FragmentoLegal {
  chunk_id: string;
  cita: string;
  texto: string;
  articulo_num: number | null;
  fraccion: string | null;
  inciso: string | null;
  paginas: number[];
  sanciones: Sanciones | null;
  multas_en_pesos: MultaEnPesos[];
}

export type Cita = FragmentoLegal & { ultima_reforma: string | null };

export type Fragmento = FragmentoLegal & {
  tipo: string;
  score: number | null;
  coincidencia_exacta: boolean;
};

export interface Respuesta {
  pregunta: string;
  encontrado: boolean;
  respuesta: string;
  citas: Cita[];
  advertencias: string[];
  uma_valor_diario: number | null;
  modelo: string | null;
}

export interface BusquedaResponse {
  pregunta: string;
  resultados: Fragmento[];
}
