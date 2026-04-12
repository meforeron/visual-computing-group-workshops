                                                                                                                                                                   /**
 * Taller - Modelos de Reflexión: Lambert, Phong, Blinn-Phong y PBR
 * Entorno: Processing 4
 *
 * Se renderizan 4 esferas raycast (píxel a píxel) sin usar
 * la GPU de Processing, para que cada ecuación sea visible
 * directamente en el código.
 *
 * Controles:
 *   Mouse X  → mueve la luz horizontalmente
 *   Mouse Y  → mueve la luz verticalmente
 *   1-4      → seleccionar esfera (resaltado)
 *   UP/DOWN  → ajustar shininess
 *   R/M      → ajustar roughness / metalness (esfera PBR)
 */

// ─── Parámetros globales ─────────────────────────────────────
int   SPHERE_R  = 110;       // radio de cada esfera en píxeles
int   COLS      = 4;         // número de esferas
float shininess = 64;        // exponente especular Phong/Blinn
float roughness = 0.4;       // PBR roughness
float metalness = 0.0;       // PBR metalness
int   selected  = -1;        // esfera seleccionada (-1 = ninguna)

// Color base del material (albedo) en 0..1
PVector albedo = new PVector(0.22, 0.50, 0.85);

// Posición de la cámara (usada para calcular V)
PVector camPos = new PVector(0, 0, 500);

// ─── Setup ───────────────────────────────────────────────────
void setup() {
  size(960, 360);
  noSmooth();         // sin anti-alias para ver píxeles nítidos
  textFont(createFont("Monospaced", 12));
}

// ─── Draw ────────────────────────────────────────────────────
void draw() {
  background(18);

  // Posición de la luz: sigue al mouse en el plano de pantalla
  // y se coloca "delante" de las esferas en Z
  PVector lightPos = new PVector(
    map(mouseX, 0, width,  -width/2,  width/2),
    map(mouseY, 0, height, -height/2, height/2),
    300
  );

  // Centros de cada esfera en pantalla
  int totalW = COLS * (SPHERE_R * 2 + 40) - 40;
  int startX = (width - totalW) / 2 + SPHERE_R;
  int cy     = height / 2 - 20;

  int[] cx = new int[COLS];
  for (int i = 0; i < COLS; i++) {
    cx[i] = startX + i * (SPHERE_R * 2 + 40);
  }

  // ── Raycasting: recorrer cada píxel de cada esfera ──────────
  loadPixels();

  for (int col = 0; col < COLS; col++) {
    // Ventana de píxeles de esta esfera
    int x0 = cx[col] - SPHERE_R;
    int x1 = cx[col] + SPHERE_R;
    int y0 = cy    - SPHERE_R;
    int y1 = cy    + SPHERE_R;

    for (int py = y0; py <= y1; py++) {
      for (int px = x0; px <= x1; px++) {
        // Coordenadas locales al centro de la esfera
        float lx = px - cx[col];
        float ly = py - cy;
        float d2 = lx*lx + ly*ly;

        if (d2 > (float)(SPHERE_R * SPHERE_R)) continue; // fuera de la esfera

        // Coordenada Z del punto en la esfera (esfera unitaria escalada)
        float lz = sqrt((float)(SPHERE_R * SPHERE_R) - d2);

        // ── Vectores del modelo de iluminación ───────────────
        // Normal en el punto de la esfera (ya normalizada si la esfera es unitaria)
        PVector N = new PVector(lx, -ly, lz);
        N.normalize();

        // Posición 3D del punto en la escena
        PVector P = new PVector(px - width/2, -(py - height/2), lz);

        // L: dirección desde el punto hacia la luz
        PVector L = PVector.sub(lightPos, P);
        L.normalize();

        // V: dirección desde el punto hacia la cámara
        PVector V = PVector.sub(camPos, P);
        V.normalize();

        // ── Elegir modelo según columna ───────────────────────
        PVector finalColor;
        switch (col) {
          case 0:  finalColor = shaderLambert(N, L);              break;
          case 1:  finalColor = shaderPhong(N, L, V);             break;
          case 2:  finalColor = shaderBlinnPhong(N, L, V);        break;
          case 3:  finalColor = shaderPBR(N, L, V);               break;
          default: finalColor = new PVector(0.5, 0.5, 0.5);
        }

        // Convertir 0..1 a color Processing
        int r = (int) constrain(finalColor.x * 255, 0, 255);
        int g = (int) constrain(finalColor.y * 255, 0, 255);
        int b = (int) constrain(finalColor.z * 255, 0, 255);

        pixels[py * width + px] = color(r, g, b);
      }
    }
  }

  updatePixels();

  // ── UI ───────────────────────────────────────────────────────
  drawLabels(cx, cy);
  drawLightIndicator(lightPos);
  drawHUD();
}

// ─────────────────────────────────────────────────────────────
// SHADER 1: LAMBERT (difuso puro)
// I_diffuse = kd * max(N · L, 0)
// ─────────────────────────────────────────────────────────────
PVector shaderLambert(PVector N, PVector L) {
  float ambient = 0.06;

  // Producto punto: cuánto "mira" la normal hacia la luz
  float NdotL = max(N.dot(L), 0.0);

  float r = albedo.x * (ambient + NdotL);
  float g = albedo.y * (ambient + NdotL);
  float b = albedo.z * (ambient + NdotL);
  return new PVector(r, g, b);
}

// ─────────────────────────────────────────────────────────────
// SHADER 2: PHONG
// I_spec = ks * max(R · V, 0) ^ shininess
// ─────────────────────────────────────────────────────────────
PVector shaderPhong(PVector N, PVector L, PVector V) {
  float ambient = 0.06;
  float NdotL   = max(N.dot(L), 0.0);

  // R = reflect(-L, N) = 2*(N·L)*N - (-L)
  PVector R = PVector.mult(N, 2.0 * NdotL);
  R.sub(PVector.mult(L, -1)); // R = 2(N·L)N + L  → incorrecto
  // Corrección: reflect(-L, N) = 2*(N·L)*N - (-L) ... simplifiquemos:
  // R = 2*(N·L)*N - L ... eso da el rayo reflejado respecto a -L
  // En GLSL: reflect(-L, N). Aquí:
  R = new PVector(
    2 * NdotL * N.x - L.x,
    2 * NdotL * N.y - L.y,
    2 * NdotL * N.z - L.z
  );
  R.normalize();

  // Especular: alineación entre R y V
  float RdotV = max(R.dot(V), 0.0);
  float spec  = pow(RdotV, shininess);

  float r = albedo.x * (ambient + NdotL) + 0.85 * spec;
  float g = albedo.y * (ambient + NdotL) + 0.85 * spec;
  float b = albedo.z * (ambient + NdotL) + 0.85 * spec;
  return new PVector(r, g, b);
}

// ─────────────────────────────────────────────────────────────
// SHADER 3: BLINN-PHONG
// H = normalize(L + V)
// I_spec = ks * max(N · H, 0) ^ shininess
// ─────────────────────────────────────────────────────────────
PVector shaderBlinnPhong(PVector N, PVector L, PVector V) {
  float ambient = 0.06;
  float NdotL   = max(N.dot(L), 0.0);

  // Half vector: vector a mitad de camino entre L y V
  PVector H = PVector.add(L, V);
  H.normalize();

  // Especular usando N·H en lugar de R·V
  float NdotH = max(N.dot(H), 0.0);
  float spec  = pow(NdotH, shininess);

  float r = albedo.x * (ambient + NdotL) + 0.85 * spec;
  float g = albedo.y * (ambient + NdotL) + 0.85 * spec;
  float b = albedo.z * (ambient + NdotL) + 0.85 * spec;
  return new PVector(r, g, b);
}

// ─────────────────────────────────────────────────────────────
// SHADER 4: PBR simplificado (Cook-Torrance aproximado)
//
// Ingredientes clave:
//   D  = distribución de microfacetas (GGX simplificado)
//   F  = Fresnel (Schlick)
//   G  = geometría (Smith simplificado)
//   kd = difuso (1 - metalness)
//   ks = especular (Fresnel)
// ─────────────────────────────────────────────────────────────
PVector shaderPBR(PVector N, PVector L, PVector V) {
  float ambient = 0.04;
  float NdotL   = max(N.dot(L), 0.0);
  if (NdotL == 0) return new PVector(ambient, ambient, ambient);

  PVector H     = PVector.add(L, V); H.normalize();
  float NdotV   = max(N.dot(V), 0.0001);
  float NdotH   = max(N.dot(H), 0.0);
  float VdotH   = max(V.dot(H), 0.0);

  float a  = roughness * roughness;        // alpha (roughness^2)
  float a2 = a * a;

  // ── D: distribución GGX ──────────────────────────────────
  // Modela cuántas microfacetas están orientadas hacia H
  float denom = (NdotH * NdotH) * (a2 - 1.0) + 1.0;
  float D     = a2 / (PI * denom * denom + 0.0001);

  // ── F: Fresnel (Schlick) ─────────────────────────────────
  // F0 = reflectividad a incidencia normal (0° entre V y H)
  // Metales: F0 = albedo. Dieléctricos: F0 ≈ 0.04
  PVector F0 = new PVector(0.04, 0.04, 0.04);
  F0 = PVector.lerp(F0, albedo, metalness);

  float fresnelFactor = pow(1.0 - VdotH, 5.0);
  PVector F = new PVector(
    F0.x + (1 - F0.x) * fresnelFactor,
    F0.y + (1 - F0.y) * fresnelFactor,
    F0.z + (1 - F0.z) * fresnelFactor
  );

  // ── G: geometría (Smith aproximado) ──────────────────────
  // Modela la auto-oclusión entre microfacetas
  float k  = (roughness + 1) * (roughness + 1) / 8.0;
  float G1 = NdotV / (NdotV * (1 - k) + k);
  float G2 = NdotL / (NdotL * (1 - k) + k);
  float G  = G1 * G2;

  // ── Especular Cook-Torrance ───────────────────────────────
  float denomSpec = 4.0 * NdotV * NdotL + 0.0001;
  PVector spec = new PVector(
    D * F.x * G / denomSpec,
    D * F.y * G / denomSpec,
    D * F.z * G / denomSpec
  );

  // ── Difuso: metales no tienen difuso ─────────────────────
  // kd = (1 - F) * (1 - metalness)
  PVector kd = new PVector(
    (1 - F.x) * (1 - metalness),
    (1 - F.y) * (1 - metalness),
    (1 - F.z) * (1 - metalness)
  );
  PVector diffuse = new PVector(
    kd.x * albedo.x / PI,
    kd.y * albedo.y / PI,
    kd.z * albedo.z / PI
  );

  // ── Color final ───────────────────────────────────────────
  float r = ambient * albedo.x + (diffuse.x + spec.x) * NdotL;
  float g = ambient * albedo.y + (diffuse.y + spec.y) * NdotL;
  float b = ambient * albedo.z + (diffuse.z + spec.z) * NdotL;

  // Tone mapping simple (Reinhard) para evitar overexposure
  r = r / (r + 1);
  g = g / (g + 1);
  b = b / (b + 1);

  return new PVector(r, g, b);
}

// ─────────────────────────────────────────────────────────────
// UI HELPERS
// ─────────────────────────────────────────────────────────────
String[] MODEL_NAMES = {"Lambert", "Phong", "Blinn-Phong", "PBR"};

void drawLabels(int[] cx, int cy) {
  for (int i = 0; i < COLS; i++) {
    fill(selected == i ? #ffcc44 : #aaaaaa);
    textAlign(CENTER);
    text(MODEL_NAMES[i], cx[i], cy + SPHERE_R + 22);
  }
}

void drawLightIndicator(PVector lp) {
  // Pequeño círculo amarillo donde está la luz
  int sx = (int)(lp.x + width/2);
  int sy = (int)(-lp.y + height/2);
  noFill();
  stroke(255, 230, 80);
  strokeWeight(1.5);
  ellipse(sx, sy, 14, 14);
  line(sx-8, sy, sx+8, sy);
  line(sx, sy-8, sx, sy+8);
  noStroke();

  fill(180);
  textAlign(LEFT);
  text("Luz", sx + 9, sy + 4);
}

void drawHUD() {
  fill(30);
  noStroke();
  rect(0, height - 68, width, 68);

  fill(140);
  textAlign(LEFT);
  text("Mouse: mover luz   |   1-4: seleccionar   |   UP/DOWN: shininess=" +
       nf(shininess, 0, 0) + "   |   R: roughness=" +
       nf(roughness, 0, 2) + "   |   M: metalness=" +
       nf(metalness, 0, 2),
       10, height - 48);

  fill(100);
  text("Albedo = (" + nf(albedo.x,0,2) + ", " + nf(albedo.y,0,2) + ", " + nf(albedo.z,0,2) + ")   " +
       "  Renderizado por píxel — sin GPU",
       10, height - 28);
}

// ─────────────────────────────────────────────────────────────
// CONTROLES DE TECLADO
// ─────────────────────────────────────────────────────────────
void keyPressed() {
  if (key == '1') selected = 0;
  if (key == '2') selected = 1;
  if (key == '3') selected = 2;
  if (key == '4') selected = 3;

  // Shininess (para Phong y Blinn-Phong)
  if (keyCode == UP)   shininess = min(shininess * 1.25, 512);
  if (keyCode == DOWN) shininess = max(shininess / 1.25, 1);

  // Roughness PBR
  if (key == 'r' || key == 'R') roughness = constrain(roughness + 0.05, 0, 1);
  if (key == 'e' || key == 'E') roughness = constrain(roughness - 0.05, 0, 1);

  // Metalness PBR
  if (key == 'm' || key == 'M') metalness = constrain(metalness + 0.1, 0, 1);
  if (key == 'n' || key == 'N') metalness = constrain(metalness - 0.1, 0, 1);
}
