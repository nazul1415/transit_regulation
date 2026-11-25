import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { FragmentoLegal } from '../api/types';
import { pesos, rangoUma, resumenSanciones } from '../lib/formato';
import { colores } from '../theme';

const LIMITE_COLAPSADO = 280;

interface Props {
  fragmento: FragmentoLegal;
  etiqueta?: string;
}

export function FragmentoCard({ fragmento, etiqueta }: Props) {
  const [abierto, setAbierto] = useState(false);
  const largo = fragmento.texto.length > LIMITE_COLAPSADO;
  const texto = abierto || !largo ? fragmento.texto : `${fragmento.texto.slice(0, LIMITE_COLAPSADO).trimEnd()}…`;
  const sanciones = resumenSanciones(fragmento.sanciones);
  const rangos = fragmento.sanciones?.multa_uma ?? [];

  return (
    <View style={estilos.tarjeta}>
      <View style={estilos.encabezado}>
        <Text style={estilos.cita} selectable>
          {fragmento.cita}
        </Text>
        {etiqueta ? <Text style={estilos.etiqueta}>{etiqueta}</Text> : null}
      </View>

      <Text style={estilos.texto} selectable>
        {texto}
      </Text>
      {largo ? (
        <Pressable onPress={() => setAbierto((v) => !v)} accessibilityRole="button" hitSlop={8}>
          <Text style={estilos.enlace}>{abierto ? 'Ver menos' : 'Ver texto completo'}</Text>
        </Pressable>
      ) : null}

      {rangos.length > 0 || sanciones.length > 0 || fragmento.multas_en_pesos.length > 0 ? (
        <View style={estilos.sanciones}>
          <Text style={estilos.sancionesTitulo}>Sanciones</Text>
          {rangos.map((r, i) => (
            <Text key={`uma-${i}`} style={estilos.sancion}>
              Multa: {rangoUma(r)}
            </Text>
          ))}
          {fragmento.multas_en_pesos.map((m, i) => (
            <Text key={`mxn-${i}`} style={estilos.sancion}>
              Equivale a {pesos(m.pesos_min)}
              {m.pesos_max !== m.pesos_min ? ` – ${pesos(m.pesos_max)}` : ''}
            </Text>
          ))}
          {sanciones.map((s) => (
            <Text key={s} style={estilos.sancion}>
              {s}
            </Text>
          ))}
        </View>
      ) : null}

      {fragmento.paginas.length > 0 ? (
        <Text style={estilos.pie}>
          {fragmento.paginas.length > 1 ? 'Páginas' : 'Página'} {fragmento.paginas.join(', ')} del Reglamento
        </Text>
      ) : null}
    </View>
  );
}

const estilos = StyleSheet.create({
  tarjeta: { backgroundColor: colores.tarjeta, borderColor: colores.borde, borderWidth: 1, borderRadius: 12, padding: 14, gap: 8 },
  encabezado: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 },
  cita: { flex: 1, fontSize: 15, fontWeight: '700', color: colores.primario },
  etiqueta: { fontSize: 12, fontWeight: '600', color: colores.exacta },
  texto: { fontSize: 15, lineHeight: 22, color: colores.texto },
  enlace: { fontSize: 14, color: colores.primario, fontWeight: '600' },
  sanciones: { backgroundColor: colores.fondo, borderRadius: 8, padding: 10, gap: 2 },
  sancionesTitulo: { fontSize: 13, fontWeight: '700', color: colores.texto },
  sancion: { fontSize: 14, color: colores.texto },
  pie: { fontSize: 12, color: colores.textoSuave },
});
