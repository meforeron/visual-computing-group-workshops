using UnityEngine;

public class ColisionParticulas : MonoBehaviour
{
    [Tooltip("Arrastra aquí el sistema de partículas que deseas instanciar o mover.")]
    public ParticleSystem efecto;

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
}
