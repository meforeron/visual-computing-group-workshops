
# Taller - Cálculo y Visualización de Normales

## Objetivo del taller

Calcular vectores normales de superficies 3D y utilizarlos para iluminación correcta. Comprender la diferencia entre normales de vértices y caras, smooth shading vs flat shading, y visualizar normales para debugging.

---

## Actividades por entorno

Este taller puede desarrollarse en **Python**, **Unity** y **Three.js**.

---

### Python (trimesh, NumPy)

**Herramientas necesarias:**
- `trimesh`
- `numpy`
- `matplotlib`
- `vedo` (opcional, para visualización 3D)

**Pasos a implementar:**

1. **Cálculo de normales de caras:**
   - Cargar modelo 3D (.obj, .stl, .gltf)
   - Para cada triángulo, calcular normal con producto cruz:
     ```python
     v1 = vertex_B - vertex_A
     v2 = vertex_C - vertex_A
     normal = np.cross(v1, v2)
     normal = normal / np.linalg.norm(normal)  # Normalizar
     ```
   - Verificar que normales apunten hacia afuera
   - Visualizar normales de caras como flechas

2. **Cálculo de normales de vértices:**
   - Para cada vértice, promediar normales de caras adyacentes
   - Normalizar el resultado
   - Comparar con trimesh.vertex_normals automático
   - Visualizar normales de vértices

3. **Comparación Flat vs Smooth Shading:**
   - Renderizar modelo con normales de caras (flat)
   - Renderizar modelo con normales de vértices (smooth)
   - Crear visualización lado a lado
   - Analizar diferencias visuales

4. **Validación de normales:**
   - Verificar que todas las normales tengan magnitud 1
   - Detectar normales invertidas
   - Corregir orientación de normales si es necesaria
   - Calcular consistencia de orientación

---

### Unity

**Escenario:**

- Importar modelo 3D
- Crear script C# para:
  - Acceder a mesh.normals
  - Calcular normales manualmente desde mesh.triangles
  - Recalcular normales: mesh.RecalculateNormals()
  - Dibujar normales con Debug.DrawLine() o Gizmos
- Comparar flat shading vs smooth shading
- Crear material con Normal Visualization shader

**Ejemplo de visualización de normales:**
```csharp
void OnDrawGizmos() {
    Mesh mesh = GetComponent<MeshFilter>().sharedMesh;
    Vector3[] vertices = mesh.vertices;
    Vector3[] normals = mesh.normals;

    for (int i = 0; i < vertices.Length; i++) {
        Vector3 worldPos = transform.TransformPoint(vertices[i]);
        Vector3 worldNormal = transform.TransformDirection(normals[i]);
        Gizmos.DrawLine(worldPos, worldPos + worldNormal * 0.1f);
    }
}
```

---

### Three.js con React Three Fiber

**Escenario:**

- Cargar modelo GLTF o crear geometría procedural
- Acceder a geometry.attributes.normal
- Calcular normales manualmente desde geometría
- Usar geometry.computeVertexNormals() para smooth
- Usar geometry.computeFaceNormals() para flat (deprecated, usar grupos)
- Visualizar normales con VertexNormalsHelper:
  ```jsx
  import { VertexNormalsHelper } from 'three/examples/jsm/helpers/VertexNormalsHelper'
  ```
- Crear shader para colorear según dirección de normal

---

## Entrega

Crear carpeta con el nombre: `semana_3_3_calculo_visualizacion_normales` en tu repositorio de GitLab.

Dentro de la carpeta, crear la siguiente estructura:

```
semana_3_3_calculo_visualizacion_normales/
├── python/
├── unity/
├── threejs/
├── media/  # Imágenes, videos, GIFs de resultados
└── README.md
```

### Requisitos del README.md

El archivo `README.md` debe contener obligatoriamente:

1. **Título del taller**: Taller Calculo Visualizacion Normales
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
- Nombre de carpeta correcto: `semana_3_3_calculo_visualizacion_normales`
- Cálculo correcto de normales de caras y vértices
- Visualización clara de normales como líneas/flechas
- Comparación visual entre flat y smooth shading
- Validación de normales (magnitud, orientación)
