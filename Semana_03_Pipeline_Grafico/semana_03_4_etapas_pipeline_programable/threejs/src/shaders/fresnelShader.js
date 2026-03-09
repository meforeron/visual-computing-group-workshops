
export const fresnelVertexShader = /* glsl */ `
  uniform float uTime;

  varying vec2  vUv;
  varying vec3  vNormal;    // Normal en espacio vista
  varying vec3  vViewDir;   // Vector de vista (cámara → vértice, normalizado)
  varying vec3  vWorldNormal; // Normal en espacio mundo

  void main() {
    vUv = uv;

    // Normal en espacio vista
    vNormal = normalize(normalMatrix * normal);

    // Normal en espacio mundo (para efectos globales)
    vWorldNormal = normalize(mat3(modelMatrix) * normal);

    // Posición del vértice en espacio vista
    vec4 viewPos = modelViewMatrix * vec4(position, 1.0);

    // Vector de vista: desde el vértice hacia la cámara (en espacio vista)
    // La cámara está en el origen del espacio vista → viewDir = -viewPos
    vViewDir = normalize(-viewPos.xyz);

    gl_Position = projectionMatrix * viewPos;
  }
`;

export const fresnelFragmentShader = /* glsl */ `
  precision mediump float;

  uniform float uTime;
  uniform vec3  uBaseColor;     // Color base del objeto
  uniform vec3  uFresnelColor;  // Color del borde (glow Fresnel)
  uniform float uFresnelPower;  // Exponente Fresnel (3–6 típico)
  uniform float uRimPower;      // Potencia del rim light

  varying vec2  vUv;
  varying vec3  vNormal;
  varying vec3  vViewDir;
  varying vec3  vWorldNormal;

  void main() {
    vec3 N = normalize(vNormal);
    vec3 V = normalize(vViewDir);

    // ── Efecto Fresnel ────────────────────────────────────────────
    // La ecuación de Schlick aproxima la reflectancia especular:
    // R = R0 + (1 - R0)(1 - cos θ)^n
    // Cuando V·N ≈ 0 (ángulo rasante) → fresnel ≈ 1 (borde brillante)
    // Cuando V·N ≈ 1 (vista frontal)  → fresnel ≈ 0 (color base)
    float cosTheta = max(dot(V, N), 0.0);
    float fresnel = pow(1.0 - cosTheta, uFresnelPower);

    // ── Rim Lighting ──────────────────────────────────────────────
    // Luz que ilumina los bordes del objeto desde atrás.
    // Sin = 1-cosTheta resalta los silhouettes.
    float rim = 1.0 - cosTheta;
    float rimLight = smoothstep(0.4, 1.0, pow(rim, uRimPower));

    // ── Iluminación difusa básica ─────────────────────────────────
    vec3 lightDir = normalize(vec3(1.0, 1.5, 1.0));
    float diffuse = max(dot(N, lightDir), 0.0) * 0.6 + 0.4;

    // ── Color base dinámico ───────────────────────────────────────
    // Animamos el matiz del color base en el tiempo
    vec3 baseCol = uBaseColor;
    baseCol.b = 0.4 + 0.4 * sin(uTime * 0.6);
    baseCol.r = 0.2 + 0.3 * cos(uTime * 0.4);

    // ── Composición final ─────────────────────────────────────────
    // 1. Color base iluminado
    vec3 color = baseCol * diffuse;
    // 2. Mezcla fresnel en los bordes
    color = mix(color, uFresnelColor, fresnel * 0.85);
    // 3. Añadir rim light (blanco-azulado)
    color += vec3(0.5, 0.7, 1.0) * rimLight * 0.6;

    // Alpha: ligera transparencia en el centro, opaco en bordes
    float alpha = mix(0.75, 1.0, fresnel * 0.6 + rimLight * 0.4);

    gl_FragColor = vec4(color, alpha);
  }
`;
