import { Tabs } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { colores } from '../theme';

export default function Layout() {
  return (
    <>
      <StatusBar style="dark" />
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: colores.primario,
          headerStyle: { backgroundColor: colores.tarjeta },
          headerTitleStyle: { color: colores.texto },
        }}
      >
        <Tabs.Screen name="index" options={{ title: 'Preguntar', tabBarLabel: 'Preguntar' }} />
        <Tabs.Screen name="busqueda" options={{ title: 'Buscar en el Reglamento', tabBarLabel: 'Buscar' }} />
      </Tabs>
    </>
  );
}
