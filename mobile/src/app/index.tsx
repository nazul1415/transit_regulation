import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';

import { consultar } from '../api/client';
import type { Respuesta } from '../api/types';
import { Aviso } from '../components/Aviso';
import { BuscadorInput } from '../components/BuscadorInput';
import { FragmentoCard } from '../components/FragmentoCard';
import { colores } from '../theme';

export default function Preguntar() {
  const [pregunta, setPregunta] = useState('');
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [respuesta, setRespuesta] = useState<Respuesta | null>(null);

  async function enviar() {
    const texto = pregunta.trim();
    setCargando(true);
    setError(null);
    setRespuesta(null);
    try {
      setRespuesta(await consultar(texto));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ocurrió un error inesperado.');
    } finally {
      setCargando(false);
    }
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={estilos.pantalla} contentContainerStyle={estilos.contenido} keyboardShouldPersistTaps="handled">
        <BuscadorInput
          valor={pregunta}
          onCambio={setPregunta}
          onEnviar={enviar}
          cargando={cargando}
          placeholder="Ej. ¿Cuál es la sanción por conducir en estado de ebriedad?"
          etiquetaBoton="Preguntar"
          minLength={3}
          maxLength={1000}
        />

        {error ? <Aviso tipo="error" texto={error} /> : null}

        {respuesta ? (
          <View style={estilos.resultado}>
            <View style={estilos.resumen}>
              <Text style={estilos.resumenTitulo}>{respuesta.encontrado ? 'Respuesta' : 'Sin resultados'}</Text>
              <Text style={estilos.resumenTexto} selectable>
                {respuesta.respuesta}
              </Text>
            </View>

            {respuesta.advertencias.map((a) => (
              <Aviso key={a} tipo="alerta" texto={a} />
            ))}

            {respuesta.citas.length > 0 ? <Text style={estilos.seccion}>Fundamento en el Reglamento</Text> : null}
            {respuesta.citas.map((c) => (
              <FragmentoCard key={c.chunk_id} fragmento={c} />
            ))}

            {respuesta.uma_valor_diario ? (
              <Text style={estilos.nota}>Montos en pesos calculados con UMA diaria de ${respuesta.uma_valor_diario}.</Text>
            ) : null}
          </View>
        ) : null}

        <Text style={estilos.nota}>
          Información orientativa basada en el texto del Reglamento. No sustituye asesoría legal ni a la autoridad.
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const estilos = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: colores.fondo },
  contenido: { padding: 16, gap: 14 },
  resultado: { gap: 12 },
  resumen: { backgroundColor: colores.tarjeta, borderRadius: 12, borderColor: colores.primario, borderWidth: 1.5, padding: 14, gap: 6 },
  resumenTitulo: { fontSize: 13, fontWeight: '700', color: colores.primario, textTransform: 'uppercase' },
  resumenTexto: { fontSize: 16, lineHeight: 24, color: colores.texto },
  seccion: { fontSize: 15, fontWeight: '700', color: colores.texto, marginTop: 4 },
  nota: { fontSize: 12, color: colores.textoSuave },
});
