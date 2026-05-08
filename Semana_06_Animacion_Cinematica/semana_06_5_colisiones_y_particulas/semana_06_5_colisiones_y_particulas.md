
# Taller - Colisiones y Partículas: Reacciones Visuales Interactivas

## Objetivo del taller

Aprender a usar **Colliders** para detectar colisiones entre objetos y disparar **efectos visuales con partículas** al momento de una interacción. Este taller permitirá a los estudiantes entender el sistema de físicas de Unity y cómo integrarlo con efectos gráficos simples.

---

## Actividades por entorno

### Entorno: Unity (versión LTS)

**Herramientas necesarias:**
- Unity Editor
- Rigidbody y Colliders (Box, Sphere o Mesh)
- Particle System
- Script en C# para detección de colisiones

---

### 🔧 Actividades paso a paso

1. **Crear una escena básica:**
 - Agrega un `Plane` como suelo.
 - Agrega varios `Cubes` o `Spheres` con `Rigidbody` para que caigan.
 - Asegúrate de que los objetos tengan **Colliders**.

2. **Crear un sistema de partículas:**
 - Ve a **GameObject > Effects > Particle System**.
 - Ajusta el color, duración y forma del efecto.
 - Desactiva el sistema para que no se reproduzca automáticamente (`play on awake = false`).

3. **Crear un script de colisión:**

```csharp
using UnityEngine;

public class ColisionParticulas : MonoBehaviour
{
 public ParticleSystem efecto;

 private void OnCollisionEnter(Collision collision)
 {
 if (efecto != null)
 {
 efecto.transform.position = collision.contacts[0].point;
 efecto.Play();
 }
 }
}
```

4. **Asignar el script y efecto:**
 - Añade el script a los objetos que se moverán.
 - Arrastra el sistema de partículas al campo `efecto` del script.

5. **Probar la escena:**
 - Al iniciar el juego, deja que los objetos caigan y choquen.
 - El sistema de partículas se activará en el punto de impacto.

**Bonus:**
- Cambiar el color o forma de las partículas dependiendo del tipo de objeto.
- Usar `OnTriggerEnter` con `isTrigger` activado para colisiones sin físicas reales.
- Agregar sonido al colisionar.

---

## Entrega

Crear carpeta con el nombre: `semana_6_5_colisiones_y_particulas` en tu repositorio de GitLab.

Dentro de la carpeta, crear la siguiente estructura:

```
semana_6_5_colisiones_y_particulas/
├── unity/
├── media/ # Imágenes, videos, GIFs de resultados
└── README.md
```

### Requisitos del README.md

El archivo `README.md` debe contener obligatoriamente:

1. **Título del taller**: Taller Colisiones Y Particulas
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
- Nombre de carpeta correcto: `semana_6_5_colisiones_y_particulas`

### Contenido del `README.md`:

- Descripción breve del comportamiento esperado.
- GIFs mostrando:
 - La colisión.
 - El efecto de partículas activado.
- Código del script.
- **Descripción general del comportamiento de colisiones y eventos**.
- Reflexión: ¿Qué otras cosas podrías activar con una colisión (luz, animación, sonido)?

---
