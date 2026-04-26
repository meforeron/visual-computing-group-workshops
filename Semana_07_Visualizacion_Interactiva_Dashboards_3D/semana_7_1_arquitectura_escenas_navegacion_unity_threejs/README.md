# Taller Interfaces Multimodales Voz Gestos

## Nombres

- Andres Felipe Galindo Gonzalez
- Stephan Alian Roland Martiquet Garcia
- Melissa Dayana Forero Narváez
- Gabriel Andres Anzola Tachak
- Carlos Arturo Murcia

## Fecha de entrega

`2026-04-25`

---

## Descripción

Este taller pretende dar a entender cómo es la organización de un proyecto o aplicación interactiva a gran escala o con diversos componentes, pero cuál es el problema: si se escribe todo un juego o app en un solo archivo o escena no puede ser escalable, es decir, si se quiere agregar una nueva funcionalidad o componente se vuelve un caos. Por lo que la solución está en dividirlo en escenas independientes con una capa de navegación que permita moverse entre ellas. Aquí la escena es la unidad de organización o el concepto clave, porque en ella se define qué recursos están cargando en memoria, qué lógica se está ejecutando y qué es lo que ve el usuario, es decir, la interfaz. Por lo que cuando el usuario le da en jugar, se está construyendo el mundo desde cero, bajándolo desde la memoria, y ese proceso es lo que se llama navegación entre escenas.

Existen 4 capas de manera general:
- **Presentación**: Es la interfaz, lo que ve el usuario, lo que se muestra en pantalla. En Unity vendría siendo el Canvas, mientras que en Three.js es el renderizado de la escena con WebGL y las mallas.
- **Lógica del juego**: Son las reglas y comportamientos que definen cómo se interactúa con el mundo, como las puntuaciones, colisiones, condiciones de victoria, etc. En Unity son los MonoBehaviour, y en Three.js es el código JavaScript que actualiza su estado en cada frame.
- **Navegación entre escenas**: Es lo que decide qué escena cargar a continuación. En Unity es el SceneManager, mientras que en Three.js es react-router-dom o un sistema propio de JavaScript.
- **Estado global**: Son los datos que sobreviven al cambio entre escenas, como la puntuación, nombre del jugador, configuraciones, etc. En Unity se emplea el Singleton con DontDestroyOnLoad, mientras que en web es una variable de módulo JavaScript.

## Implementación