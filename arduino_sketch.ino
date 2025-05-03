#include <NativeEthernet.h>
#include <NativeEthernetUdp.h>
#include <FastLED.h>

#define DATA_PIN 2
#define NUM_LEDS 200  // Set to the number of LEDs you expect
CRGB leds[NUM_LEDS];

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
EthernetUDP Udp;
const unsigned int localPort = 7000;

void setup() {
  Serial.begin(9600);
  while (!Serial);

  // Initialize Ethernet with DHCP
  if (Ethernet.begin(mac) == 0) {
    Serial.println("DHCP failed. Check your router.");
    while (true);
  }

  Serial.print("My IP: ");
  Serial.println(Ethernet.localIP());

  Udp.begin(localPort);

  // Setup FastLED
  FastLED.addLeds<WS2812B, DATA_PIN, RGB>(leds, NUM_LEDS);
  FastLED.clear();
  FastLED.show();
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize > 0) {
    Serial.print("Received packet of size ");
    Serial.println(packetSize);

    Serial.print("From IP: ");
    Serial.println(Udp.remoteIP());

    byte buffer[1500];  // Max expected size
    int len = Udp.read(buffer, sizeof(buffer));

    int ledCount = min(len / 3, NUM_LEDS);
    Serial.print("Updating ");
    Serial.print(ledCount);
    Serial.println(" LEDs");

    for (int i = 0; i < ledCount; i++) {
      int idx = i * 3;
      leds[i] = CRGB(buffer[idx], buffer[idx + 1], buffer[idx + 2]);

      // Print the first 5 LEDs for debugging
      if (i < 5) {
        Serial.print("LED ");
        Serial.print(i);
        Serial.print(":");
        Serial.print(buffer[idx]);
        Serial.print(";");
        Serial.print(buffer[idx + 1]);
        Serial.print(";");
        Serial.println(buffer[idx + 2]);
      }
    }

    FastLED.show();
    Serial.println("LEDs updated.\n");
  }
}