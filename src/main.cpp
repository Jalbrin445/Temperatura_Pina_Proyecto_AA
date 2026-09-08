#include <Arduino.h>   // <-- ESTO ES OBLIGATORIO EN PLATFORMIO
#include "max6675.h"

// Pines SPI compartidos por software/hardware
const int pinSO  = 12;
const int pinSCK = 13;

// Pines de Selección de Chip (CS) independientes
const int pinCS1 = 10; // Centro Piña
const int pinCS2 = 9;  // Agua
const int pinCS3 = 8;  // Superficie Piña

// Instanciación de las 3 termocuplas
MAX6675 termocuplaCentro(pinSCK, pinCS1, pinSO);
MAX6675 termocuplaAgua(pinSCK, pinCS2, pinSO);
MAX6675 termocuplaSuperficie(pinSCK, pinCS3, pinSO);

void setup() {
  Serial.begin(115200);
  delay(500);
}

void loop() {
  float t_centro     = termocuplaCentro.readCelsius();
  float t_agua       = termocuplaAgua.readCelsius();
  float t_superficie = termocuplaSuperficie.readCelsius();

  Serial.print(t_centro);
  Serial.print(",");
  Serial.print(t_agua);
  Serial.print(",");
  Serial.println(t_superficie);

  delay(1000); 
}