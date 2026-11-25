import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text } from 'react-native';

import { buscar } from '../api/client';
import type { Fragmento } from '../api/types';
import { Aviso } from '../components/Aviso';
import { BuscadorInput } from '../components/BuscadorInput';
import { FragmentoCard } from '../components/FragmentoCard';
import { colores } from '../theme';

export default function Busqueda() {
  const [q, setQ] = useState('');
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultados, setResultados] = useState<Fragmento[] | null>(null);

  async function enviar() {
    setCargando(true);
    setError(null);
    try {
      setResultados((await buscar(q.trim())).resultados);
    } catch (e) {
      setResultados(null);
      setError(e instanceof Error ? e.message : 'Ocurrió un error inesperado.');
    } finally {
      setCargando(false);
    }
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={estilos.pantalla} contentContainerStyle={estilos.contenido} keyboardShouldPersistTaps="handled">
        <BuscadorInput
          valor={q}
          onCambio={setQ}
          onEnviar={enviar}
          cargando={cargando}
          placeholder='Palabras clave o "artículo 14, fracción I"'
          etiquetaBoton="Buscar"
          minLength={2}
          maxLength={500}
        />

        {error ? <Aviso tipo="error" texto={error} /> : null}

        {resultados && resultados.length === 0 ? <Text style={estilos.vacio}>Sin resultados para “{q.trim()}”.</Text> : null}

        {resultados?.map((r) => (
          <FragmentoCard key={r.chunk_id} fragmento={r} etiqueta={r.coincidencia_exacta ? 'Coincidencia exacta' : undefined} />
        ))}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const estilos = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: colores.fondo },
  contenido: { padding: 16, gap: 12 },
  vacio: { fontSize: 15, color: colores.textoSuave, textAlign: 'center', marginTop: 12 },
});
