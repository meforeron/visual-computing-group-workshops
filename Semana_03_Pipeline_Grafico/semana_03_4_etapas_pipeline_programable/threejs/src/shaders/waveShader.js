
export const waveVertexShader = /* glsl */ `
  uniform float uTime;
  uniform float uAmplitude;
  uniform float uFrequency;

  varying vec2 vUv;
  varying vec3 vNormal;

  void main() {
    vUv    = uv;
    // normalMatrix = inversa-transpuesta de modelViewMatrix (3x3)
    // transforma normales de espacio objeto a espacio vista
    vNormal = normalize(normalMatrix * normal);

    vec3 pos = position;

    // Onda sinusoidal en X modulada por tiempo
    // dot(n, l) = coseno del angulo -> intensidad de onda
    float wave = sin(pos.x * uFrequency + uTime)
               * cos(pos.y * uFrequency * 0.7 + uTime * 1.3);

    // Desplazar a lo largo de la normal -> inflar/deflactar
    pos += normal * wave * uAmplitude;

    // Transformacion final: espacio objeto -> clip space
    // projectionMatrix * modelViewMatrix * pos
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`;


export const waveFragmentShader = /* glsl */ `
  uniform float uTime;

  varying vec2 vUv;
  varying vec3 vNormal;

  void main() {
    vec3 n = normalize(vNormal);

    // Iluminacion difusa basica (Lambert)
    // lightDir fija en espacio vista apuntando hacia camara
    vec3  lightDir = normalize(vec3(1.0, 1.0, 1.5));
    float diffuse  = max(dot(n, lightDir), 0.0) * 0.7 + 0.3;

    // Color procedural por UV: arcoiris desfasado 120 grados (2pi/3)
    float h = uTime * 0.25;
    vec3 color = vec3(
      0.5 + 0.5 * sin(vUv.x * 6.2832 + h),
      0.5 + 0.5 * sin(vUv.y * 6.2832 + h + 2.094),
      0.5 + 0.5 * sin((vUv.x + vUv.y) * 6.2832 + h + 4.189)
    );

    gl_FragColor = vec4(color * diffuse, 1.0);
  }
`;
