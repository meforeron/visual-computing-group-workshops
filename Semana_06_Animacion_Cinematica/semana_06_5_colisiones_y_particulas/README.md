# Taller Colisiones Y Particulas

**Nombre del estudiante**: Stef
**Fecha de entrega**: 15 de abril de 2026

## Descripción breve
En este taller se implementa un sistema básico de físicas y efectos visuales en Unity. Consiste en la detección de colisiones entre objetos con Rigidbodies (cubos y esferas) y el disparo de un sistema de partículas interactivo en el momento y posición exacta del impacto. 

## Implementaciones

### Entorno: Unity
1. **Escena Física**: Se configuró un plano como suelo y esferas/cubos con `Rigidbody` que caen afectados por la gravedad. Todos los objetos tienen sus respectivos `Colliders`.
2. **Sistema de Partículas (Particle System)**: Se creó un efecto visual en Unity configurado para no reproducirse automáticamente (`Play on Awake = false`), ademas hay que crear un efecto de particulas para cada objeto si no se trasnfieren lasparticulas de un objeto al otro.


## Resultados visuales
VIDEO COlISION en GIF.gif



## Código relevante

**ColisionParticulas.cs**:
```csharp
 private void OnCollisionEnter(Collision collision)
    {
        // Solo queremos hacer el efecto si choca contra el suelo 
        if (collision.gameObject.name == "Plane")
        {
            Debug.Log("¡Chocó con el suelo!");

            if (efecto != null)
            {
                // Movemos la partícula al punto de impacto
                efecto.transform.position = collision.contacts[0].point;
                
                
                efecto.Emit(30); 
            }
            else
            {
                Debug.LogWarning("⚠️ Falta arrastrar el Particle System al script.");
            }
        }
    }

```

## Descripción general del comportamiento de colisiones y eventos
Cuando un objeto dinámico (con `Rigidbody`) impacta contra el suelo o contra otro objeto sólido en la escena, el motor de físicas de Unity calcula la intersección de sus colliders. En ese instante, Unity dispara el evento `OnCollisionEnter`. El script capta este evento, obteniendo los datos exactos del choque mediante los 'contacts', lo que permite mover nuestro sistema de partículas a las coordenadas de impacto exactas y dar la orden de reproducirlo. Todo esto ocurre casi instantáneamente dando un feedback visual directo a las simulaciones de físicas.


## Prompts utilizados
- "ayúdame a crear la estructura base para el README de acuerdo a los requerimientos de la semana 6.5."

## Aprendizajes y dificultades
Al inicio no entendia por que las particulas se movian de formas extranas asi que en vez de play para no tener un loop, se cambio a emit para un numero fijo de particulas al momento del impacto.
