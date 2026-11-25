import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { colores } from '../theme';

interface Props {
  valor: string;
  onCambio: (v: string) => void;
  onEnviar: () => void;
  cargando: boolean;
  placeholder: string;
  etiquetaBoton: string;
  maxLength: number;
  minLength: number;
}

export function BuscadorInput({ valor, onCambio, onEnviar, cargando, placeholder, etiquetaBoton, maxLength, minLength }: Props) {
  const habilitado = valor.trim().length >= minLength && !cargando;
  return (
    <View style={estilos.caja}>
      <TextInput
        style={estilos.input}
        value={valor}
        onChangeText={onCambio}
        placeholder={placeholder}
        placeholderTextColor={colores.textoSuave}
        multiline
        maxLength={maxLength}
        returnKeyType="search"
        submitBehavior="blurAndSubmit"
        onSubmitEditing={() => habilitado && onEnviar()}
        accessibilityLabel={placeholder}
      />
      <Pressable
        style={[estilos.boton, !habilitado && estilos.botonInactivo]}
        onPress={onEnviar}
        disabled={!habilitado}
        accessibilityRole="button"
      >
        {cargando ? <ActivityIndicator color={colores.primarioTexto} /> : <Text style={estilos.botonTexto}>{etiquetaBoton}</Text>}
      </Pressable>
    </View>
  );
}

const estilos = StyleSheet.create({
  caja: { gap: 10 },
  input: {
    minHeight: 56,
    maxHeight: 140,
    backgroundColor: colores.tarjeta,
    borderColor: colores.borde,
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    color: colores.texto,
    textAlignVertical: 'top',
  },
  boton: { backgroundColor: colores.primario, borderRadius: 12, paddingVertical: 14, alignItems: 'center' },
  botonInactivo: { opacity: 0.45 },
  botonTexto: { color: colores.primarioTexto, fontSize: 16, fontWeight: '600' },
});
