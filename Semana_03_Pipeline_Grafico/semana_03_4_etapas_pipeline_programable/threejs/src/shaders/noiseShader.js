
const NOISE_FUNCTIONS = `
  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
  }

  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), u.x),
      mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
      u.y
    );
  }

  // fBm: suma 5 octavas (amp*=0.5, freq*=2) con rotacion entre octavas
  float fbm(vec2 p) {
    float val = 0.0;
    float amp = 0.5;
    float frq = 1.0;
    mat2  rot = mat2(1.6, -1.2, 1.2, 1.6);
    for (int i = 0; i < 5; i++) {
      val += amp * noise(p * frq);
      p    = rot * p;
      amp *= 0.5;
      frq *= 2.0;
    }
    return val;
  }
`;

export const noiseVertexShader = /* glsl */ `
  uniform float uTime;
  uniform float uNoiseStrength;

  varying vec2  vUv;
  varying vec3  vNormal;
  varying float vElevation;

  ${NOISE_FUNCTIONS}

  void main() {
    vUv = uv;

    // Coordenadas de ruido animadas por tiempo
    vec2 nuv  = position.xy * 0.8 + vec2(uTime * 0.12, uTime * 0.07);
    float elev = fbm(nuv);
    vElevation = elev;

    // Desplazar vertice en Z segun elevacion del terreno
    vec3 pos = position;
    pos.z += (elev - 0.5) * uNoiseStrength;

    // Normal aproximada por diferencias finitas
    float eps = 0.01;
    float hx  = fbm(nuv + vec2(eps, 0.0));
    float hy  = fbm(nuv + vec2(0.0, eps));
    vec3 approxN = normalize(vec3(
      -(hx - elev) * uNoiseStrength / eps,
      -(hy - elev) * uNoiseStrength / eps,
      1.0
    ));
    vNormal = normalize(normalMatrix * approxN);

    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`;


export const noiseFragmentShader = /* glsl */ `
  uniform float uTime;
  uniform vec3  uColor1;
  uniform vec3  uColor2;

  varying vec2  vUv;
  varying vec3  vNormal;
  varying float vElevation;

  void main() {
    float t = clamp(vElevation, 0.0, 1.0);

    // Colores animados
    vec3 col1 = uColor1;
    col1.r = 0.05 + 0.2 * sin(uTime * 0.3);
    vec3 col2 = uColor2;
    col2.g = 0.5 + 0.4 * cos(uTime * 0.35 + 1.0);
    col2.b = 0.6 + 0.3 * sin(uTime * 0.5  + 2.0);

    vec3 color = mix(col1, col2, t);

    // Difusa
    vec3  N = normalize(vNormal);
    vec3  L = normalize(vec3(0.5, 0.5, 1.0));
    float d = max(dot(N, L), 0.0) * 0.65 + 0.35;
    color *= d;

    // Lineas de nivel (contornos)
    float bands   = abs(sin(vElevation * 8.0 * 3.14159));
    float contour = smoothstep(0.9, 1.0, bands);
    color = mix(color, color * 0.5, contour * 0.4);

    gl_FragColor = vec4(color, 1.0);
  }
`;
