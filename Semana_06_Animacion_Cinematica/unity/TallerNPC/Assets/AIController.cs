using UnityEngine;
using UnityEngine.AI;

public enum AIState { Idle, Patrol, Chase }

public class AIController : MonoBehaviour {

    [Header("Navegación")]
    public Transform[] waypoints;
    public Transform player;

    [Header("Detección")]
    public float detectionRadius = 10f;
    public float loseRadius = 15f;

    private NavMeshAgent agent;
    private Animator animator;
    private AIState currentState = AIState.Idle;
    private int waypointIndex = 0;
    private float idleTimer = 0f;

    void Start() {
        agent = GetComponent<NavMeshAgent>();
        animator = GetComponent<Animator>();
        agent.SetDestination(waypoints[0].position);
    }

    void Update() {
        animator.SetFloat("Speed", agent.velocity.magnitude);

        switch (currentState) {
            case AIState.Idle:    HandleIdle();    break;
            case AIState.Patrol:  HandlePatrol();  break;
            case AIState.Chase:   HandleChase();   break;
        }
    }

    void HandleIdle() {
        agent.speed = 2f;
        agent.isStopped = true;
        idleTimer += Time.deltaTime;
        if (idleTimer > 2f) {
            idleTimer = 0f;
            currentState = AIState.Patrol;
            agent.isStopped = false;
        }
    }

    void HandlePatrol() {
        agent.speed = 3f;
        if (!agent.pathPending && agent.remainingDistance < 0.5f) {
            waypointIndex = (waypointIndex + 1) % waypoints.Length;
            agent.SetDestination(waypoints[waypointIndex].position);
        }
        float dist = Vector3.Distance(transform.position, player.position);
        if (dist < detectionRadius) {
            currentState = AIState.Chase;
        }
    }

    void HandleChase() {
        agent.isStopped = false;
        agent.speed = 6f;
        agent.SetDestination(player.position);
        float dist = Vector3.Distance(transform.position, player.position);
        if (dist > loseRadius) {
            currentState = AIState.Patrol;
        }
    }
}