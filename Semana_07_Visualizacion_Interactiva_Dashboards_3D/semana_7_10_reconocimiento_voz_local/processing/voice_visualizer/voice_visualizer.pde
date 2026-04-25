import oscP5.*;
import netP5.*;

OscP5 oscP5;

int r = 70;
int g = 120;
int b = 255;

boolean shouldSpin = false;
boolean running = true;
float angleY = 0.0;

void setup() {
  size(900, 600, P3D);
  oscP5 = new OscP5(this, 12000);
  textSize(20);
}

void draw() {
  background(20);
  lights();

  if (running && shouldSpin) {
    angleY += 0.02;
  }

  pushMatrix();
  translate(width / 2, height / 2, 0);
  rotateY(angleY);
  fill(r, g, b);
  noStroke();
  box(180);
  popMatrix();

  fill(255);
  text("Comandos: rojo, azul, verde, girar, iniciar, detener", 20, 32);
  text("running: " + running + " | spin: " + shouldSpin, 20, 60);
}

void oscEvent(OscMessage msg) {
  if (msg.checkAddrPattern("/color") && msg.typetag().equals("iii")) {
    r = msg.get(0).intValue();
    g = msg.get(1).intValue();
    b = msg.get(2).intValue();
    running = true;
  } else if (msg.checkAddrPattern("/spin") && msg.typetag().equals("i")) {
    shouldSpin = msg.get(0).intValue() == 1;
  } else if (msg.checkAddrPattern("/running") && msg.typetag().equals("i")) {
    running = msg.get(0).intValue() == 1;
  }
}
