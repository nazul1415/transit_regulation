import { StyleSheet, Text, View } from 'react-native';

import { colores } from '../theme';

export function Aviso({ tipo, texto }: { tipo: 'error' | 'alerta'; texto: string }) {
  const esError = tipo === 'error';
  return (
    <View style={[estilos.caja, { backgroundColor: esError ? colores.errorFondo : colores.alertaFondo }]} accessibilityRole="alert">
      <Text style={{ color: esError ? colores.error : colores.alerta, fontSize: 14 }}>{texto}</Text>
    </View>
  );
}

const estilos = StyleSheet.create({ caja: { borderRadius: 10, padding: 12 } });
