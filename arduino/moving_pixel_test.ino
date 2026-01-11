#include <OctoWS2811.h>

// ---------------------------
// Configuration
// ---------------------------
const int ledsPerStrip = 200;        // LEDs per panel
const int numStrips = 2;             // Number of strips/panels

// DMA buffers (correct size)
DMAMEM int displayMemory[ledsPerStrip * 6 * numStrips];
int drawingMemory[ledsPerStrip * 6 * numStrips];

const int config = WS2811_RGB | WS2811_800kHz;
OctoWS2811 leds(ledsPerStrip, displayMemory, drawingMemory, config);

#define WHITE 0xFFFFFF
#define BLACK 0x000000

// Maximum brightness (0-255)
#define MAX_BRIGHTNESS 64

// ---------------------------
// Scale a 24-bit RGB color
// ---------------------------
uint32_t scaleColor(uint32_t color) {
  uint8_t r = (color >> 16) & 0xFF;
  uint8_t g = (color >> 8) & 0xFF;
  uint8_t b = color & 0xFF;

  r = (r * MAX_BRIGHTNESS) / 255;
  g = (g * MAX_BRIGHTNESS) / 255;
  b = (b * MAX_BRIGHTNESS) / 255;

  return (r << 16) | (g << 8) | b;
}

// ---------------------------
// Setup
// ---------------------------
void setup() {
  leds.begin();

  // Clear ALL pixels
  for (int i = 0; i < leds.numPixels(); i++) {
    leds.setPixel(i, BLACK);
  }
  leds.show();
}

// ---------------------------
// Loop
// ---------------------------
void loop() {
  static int pos = 0;

  // Total number of LEDs across both panels
  const int totalLEDs = ledsPerStrip * numStrips;

  // Clear all pixels
  for (int i = 0; i < totalLEDs; i++) {
    leds.setPixel(i, BLACK);
  }

  // Set the current pixel with brightness-limited WHITE
  leds.setPixel(pos, scaleColor(WHITE));
  leds.show();

  // Move to the next pixel
  pos = (pos + 1) % totalLEDs;

  delay(50);
}
