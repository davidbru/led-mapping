#include <OctoWS2811.h>
#include <ArtnetNativeEther.h>  // Correct for NativeEthernet on Teensy
#include <NativeEthernet.h>
#include <NativeEthernetUdp.h>

// ================= CONFIG =================
// 21 panels (each 20x10) grouped into 7 LED groups (A-G)
// Each group has 3 panels connected in series to one OctoWS2811 output.
#define PANEL_WIDTH      20
#define PANEL_HEIGHT     10
#define PANEL_PIXELS     (PANEL_WIDTH * PANEL_HEIGHT)

#define NUM_PANELS       21
#define PANELS_PER_GROUP 3
#define NUM_OUTPUTS      7

#define LEDS_PER_OUTPUT  (PANELS_PER_GROUP * PANEL_PIXELS) 
#define TOTAL_LEDS       (NUM_PANELS * PANEL_PIXELS)
#define MAX_UNIVERSES    ((TOTAL_LEDS / 170) + 1)
#define DMX_CHANNELS     (MAX_UNIVERSES * 512)

// ================= BRIGHTNESS =================
#define GLOBAL_BRIGHTNESS 255 // 0-255
float panelBrightness[NUM_PANELS] = {
  1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
  1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
  1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
}; // 0.0-1.0

// ================= OCTO =================
DMAMEM int displayMemory[LEDS_PER_OUTPUT * 8];
int drawingMemory[LEDS_PER_OUTPUT * 8];

OctoWS2811 leds(
  LEDS_PER_OUTPUT,
  displayMemory,
  drawingMemory,
  WS2811_RGB | WS2811_800kHz
);

// ================= ETHERNET =================
byte mac[] = { 0x04, 0xE9, 0xE5, 0x00, 0x00, 0x01 };

// ================= ARTNET RECEIVER =================
ArtnetNativeEther artnet;
uint8_t dmxBuffer[DMX_CHANNELS]; 

// ================= PANEL ORIENTATION =================
enum Orientation {
  TOP_LEFT,
  TOP_RIGHT,
  BOTTOM_LEFT,
  BOTTOM_RIGHT
};

Orientation panelOrientation[NUM_PANELS] = {
  TOP_RIGHT,    // 1
  TOP_LEFT,     // 2
  TOP_LEFT,     // 3
  TOP_RIGHT,    // 4
  TOP_LEFT,     // 5
  BOTTOM_RIGHT, // 6
  BOTTOM_RIGHT, // 7
  BOTTOM_LEFT,  // 8
  BOTTOM_RIGHT, // 9
  TOP_LEFT,     // 10
  TOP_RIGHT,    // 11
  TOP_LEFT,     // 12
  TOP_LEFT,     // 13
  TOP_RIGHT,    // 14
  BOTTOM_RIGHT, // 15
  BOTTOM_RIGHT, // 16
  BOTTOM_LEFT,  // 17
  BOTTOM_RIGHT, // 18
  BOTTOM_RIGHT, // 19
  BOTTOM_LEFT,  // 20
  BOTTOM_LEFT   // 21
};

const uint8_t panelGroups[NUM_OUTPUTS][PANELS_PER_GROUP] = {
  {2, 1, 6},   // Group A
  {3, 8, 7},   // Group B
  {5, 4, 9},   // Group C
  {10, 14, 18},// Group D
  {12, 11, 15},// Group E
  {13, 17, 16},// Group F
  {19, 20, 21} // Group G
};

// ================= PANEL LUT =================
const uint16_t panelLUT[PANEL_PIXELS] = {
  0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,
  199,198,197,196,195,194,193,192,191,190,189,188,187,186,185,184,183,182,181,20,
  162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,21,
  161,160,159,158,157,156,155,154,153,152,151,150,149,148,147,146,145,144,143,22,
  124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,23,
  123,122,121,120,119,118,117,116,115,114,113,112,111,110,109,108,107,106,105,24,
  86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,25,
  85,84,83,82,81,80,79,78,77,76,75,74,73,72,71,70,69,68,67,26,
  48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,27,
  47,46,45,44,43,42,41,40,39,38,37,36,35,34,33,32,31,30,29,28
};

// ================= HELPERS =================
inline uint16_t orientIndex(uint8_t x, uint8_t y, Orientation o) {
  switch (o) {
    case TOP_LEFT:     return y * PANEL_WIDTH + x;
    case TOP_RIGHT:    return y * PANEL_WIDTH + (PANEL_WIDTH - 1 - x);
    case BOTTOM_LEFT:  return (PANEL_HEIGHT - 1 - y) * PANEL_WIDTH + x;
    case BOTTOM_RIGHT: return (PANEL_HEIGHT - 1 - y) * PANEL_WIDTH + (PANEL_WIDTH - 1 - x);
  }
  return 0;
}

// ================= ARTDMX CALLBACK =================
void handleArtDmx(const uint8_t *data, uint16_t size,
                  const ArtDmxMetadata &metadata,
                  const ArtNetRemoteInfo &remote)
{
  uint16_t uni = metadata.universe;
  uint32_t base = uni * 512U;
  
  if (base + size > DMX_CHANNELS) return;
  memcpy(dmxBuffer + base, data, size);
}

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("Ethernet starting (DHCP)...");
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP");
  }

  Serial.print("IP address: ");
  Serial.println(Ethernet.localIP());

  artnet.begin();
  artnet.subscribeArtDmx([](const uint8_t *data, uint16_t size,
                             const ArtDmxMetadata &metadata,
                             const ArtNetRemoteInfo &remote){
    handleArtDmx(data, size, metadata, remote);
  });

  leds.begin();
  leds.show();
  Serial.println("Ready!");
}

void loop() {
  artnet.parse();

  // Convert DMX buffer to LED output
  uint32_t globalPixel = 0;
  for (uint8_t out = 0; out < NUM_OUTPUTS; out++) {
    uint32_t outputBase = out * LEDS_PER_OUTPUT;
    for (uint8_t p = 0; p < PANELS_PER_GROUP; p++) {
      uint8_t panelIdx = panelGroups[out][p] - 1;
      Orientation o = panelOrientation[panelIdx];
      uint32_t panelBase = outputBase + p * PANEL_PIXELS;
      for (uint8_t y = 0; y < PANEL_HEIGHT; y++) {
        for (uint8_t x = 0; x < PANEL_WIDTH; x++) {
          uint16_t logical  = orientIndex(x, y, o);
          uint16_t physical = panelLUT[logical];
          uint32_t ledIndex = panelBase + physical;

          uint32_t currentUniverse = globalPixel / 170;
          uint32_t pixelInUniverse = globalPixel % 170;
          uint32_t dmxIndex = (currentUniverse * 512) + (pixelInUniverse * 3);

          uint8_t r = dmxBuffer[dmxIndex + 0];
          uint8_t g = dmxBuffer[dmxIndex + 1];
          uint8_t b = dmxBuffer[dmxIndex + 2];

          // Apply brightness
          float multiplier = panelBrightness[panelIdx] * (GLOBAL_BRIGHTNESS / 255.0);
          r = (uint8_t)(r * multiplier);
          g = (uint8_t)(g * multiplier);
          b = (uint8_t)(b * multiplier);

          leds.setPixel(ledIndex, (r << 16) | (g << 8) | b);
          globalPixel++;
        }
      }
    }
  }

  leds.show();
}
