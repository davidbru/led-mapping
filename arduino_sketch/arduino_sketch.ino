#include <NativeEthernet.h>
#include <NativeEthernetUdp.h>
#include <FastLED.h>

#define ADD_STRIP(CHIP, PIN, OFFSET, COUNT) FastLED.addLeds<CHIP, PIN, RGB>(leds + OFFSET, COUNT);

// UPDATE ACCORDING TO LIVE SCENARIO
const uint16_t ledCounts[] = {200, 60};
#define STRIP_1_GPIO 2
#define STRIP_2_GPIO 3


const uint16_t NUM_LEDS_TOTAL = ledCounts[0] + ledCounts[1];

CRGB leds[NUM_LEDS_TOTAL];

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
EthernetUDP Udp;
const unsigned int localPort = 7000;

void setup() {
  Serial.begin(9600);
  while (!Serial);


  // UPDATE ACCORDING TO LIVE SCENARIO
  uint16_t offset = 0;
  ADD_STRIP(WS2812B, STRIP_1_GPIO, offset, ledCounts[0]); offset += ledCounts[0];
//  ADD_STRIP(WS2812B, STRIP_2_GPIO, offset, ledCounts[1]); offset += ledCounts[1];


  // DEFINE MAX BRIGHTNESS OF ALL LEDS ACROSS ALL PANELS
  FastLED.setMaxPowerInVoltsAndMilliamps(5, 200);


  FastLED.clear();
  FastLED.show();

  // Initialize Ethernet with DHCP
  if (Ethernet.begin(mac) == 0) {
    Serial.println("DHCP failed. Check your router.");
    while (true);
  }

  Serial.print("My IP: ");
  Serial.println(Ethernet.localIP());

  Udp.begin(localPort);
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize > 0) {
    byte buffer[1500];  // Max expected size
    int len = Udp.read(buffer, sizeof(buffer));

    // First byte = GPIO pin
    byte gpioPin = buffer[0];
    Serial.print("GPIO Pin: ");
    Serial.println(gpioPin);

    // Map GPIO pin to LED strip offset and length
    uint16_t offset = 0;
    uint16_t count = 0;


    // UPDATE ACCORDING TO LIVE SCENARIO
    if (gpioPin == STRIP_1_GPIO) {
      offset = 0;
      count = ledCounts[0];
    } else if (gpioPin == STRIP_2_GPIO) {
      offset = ledCounts[0];
      count = ledCounts[1];
    } else {
      Serial.println("Unknown GPIO pin in UDP data!");
      return;
    }


    // Ensure we don't read beyond bounds
    uint16_t maxLEDs = min((len - 1) / 3, count);
    Serial.print("Updating ");
    Serial.print(maxLEDs);
    Serial.print(" LEDs at offset ");
    Serial.println(offset);

    for (uint16_t i = 0; i < maxLEDs; i++) {
      uint16_t idx = 1 + i * 3;  // skip GPIO byte
      leds[offset + i] = CRGB(buffer[idx], buffer[idx + 1], buffer[idx + 2]);

      // Debug first few LEDs
      if (i < 5) {
        Serial.print("LED ");
        Serial.print(offset + i);
        Serial.print(": ");
        Serial.print(buffer[idx]);
        Serial.print(", ");
        Serial.print(buffer[idx + 1]);
        Serial.print(", ");
        Serial.println(buffer[idx + 2]);
      }
    }

    FastLED.show();
    Serial.println("LEDs updated.\n");
  }
}