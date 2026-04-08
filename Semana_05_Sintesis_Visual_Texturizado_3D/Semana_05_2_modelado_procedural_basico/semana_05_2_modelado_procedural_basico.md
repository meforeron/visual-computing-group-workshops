
# Taller - Modelado Procedural Básico: Geometría desde Código

## Objetivo del taller

Crear modelos 3D simples a partir de algoritmos, sin necesidad de modelado manual. El objetivo es entender cómo se genera y manipula la geometría directamente desde código para crear estructuras dinámicas y reutilizables.

---

## Actividades por entorno

Este taller puede desarrollarse en **Unity** o **Three.js con React Three Fiber**, generando geometría en tiempo de ejecución y modificando vértices o estructuras.

---

### Unity (versión LTS) – Ejemplo básico replicable

**Escenario:**

- Crear un script en C# que genere varias primitivas (`Cube`, `Sphere`, `Cylinder`) con `GameObject.CreatePrimitive()` y las ubique en una estructura como:
 - Una fila o rejilla de cubos.
 - Una espiral de cilindros.
 - Una pirámide fractal simple (opcional).
- Aplicar transformaciones a los objetos generados (posición, rotación, escala) con bucles `for`.
- Crear mallas personalizadas con `Mesh`, `Vector3[]` y `int[]` para construir un objeto desde cero.

---

### Three.js con React Three Fiber – Ejemplo básico replicable

**Escenario:**

- Usar React Three Fiber para crear múltiples objetos con geometría básica (`boxGeometry`, `sphereGeometry`).
- Mapear arrays para generar estructuras repetitivas: por ejemplo, una cuadrícula o espiral.
- Modificar dinámicamente los vértices usando `bufferGeometry.attributes.position.array`.
- Usar `useFrame()` para aplicar transformación animada sobre la geometría o su estructura.
- Implementar un patrón fractal básico como árbol recursivo de objetos.

---

## Entrega

Crear carpeta con el nombre: `semana_5_2_modelado_procedural_basico` en tu repositorio de GitLab.

Dentro de la carpeta, crear la siguiente estructura:

```
semana_5_2_modelado_procedural_basico/
├── unity/
├── threejs/
├── media/ # Imágenes, videos, GIFs de resultados
└── README.md
```

### Requisitos del README.md

El archivo `README.md` debe contener obligatoriamente:

1. **Título del taller**: Taller Modelado Procedural Basico
2. **Nombre del estudiante**
3. **Fecha de entrega**
4. **Descripción breve**: Explicación del objetivo y lo desarrollado
5. **Implementaciones**: Descripción de cada implementación realizada por entorno
6. **Resultados visuales**: 
 - **Imágenes, videos o GIFs** que muestren el funcionamiento
 - Deben estar en la carpeta `media/` y referenciados en el README
 - Mínimo 2 capturas/GIFs por implementación
7. **Código relevante**: Snippets importantes o enlaces al código
8. **Prompts utilizados**: Descripción de prompts usados (si aplicaron IA generativa)
9. **Aprendizajes y dificultades**: Reflexión personal sobre el proceso

### Estructura de carpetas

- Cada entorno de desarrollo debe tener su propia subcarpeta (`python/`, `unity/`, `threejs/`, etc.)
- La carpeta `media/` debe contener todos los recursos visuales (imágenes, GIFs, videos)
- Nombres de archivos en minúsculas, sin espacios (usar guiones bajos o guiones medios)

---

## Criterios de evaluación

- Cumplimiento de los objetivos del taller
- Código limpio, comentado y bien estructurado
- README.md completo con toda la información requerida
- Evidencias visuales claras (imágenes/GIFs/videos en carpeta `media/`)
- Repositorio organizado siguiendo la estructura especificada
- Commits descriptivos en inglés
- Nombre de carpeta correcto: `semana_5_2_modelado_procedural_basico`
