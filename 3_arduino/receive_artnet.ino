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

// 1 panel = 200 pixels = 600 channels.
// Art-Net universe = 512 channels.
// The Teensy expects 170 pixels per universe (510 channels).
// 21 panels * 200 pixels = 4200 pixels.
// 4200 / 170 = 24.7 -> 25 universes (0 to 24).

#define MAX_UNIVERSES    32 // Increased for safety
#define DMX_CHANNELS     (MAX_UNIVERSES * 512)

// ================= SYNC =================
#define LAST_UNIVERSE    (MAX_UNIVERSES - 1)

// ================= BRIGHTNESS =================
#define GLOBAL_BRIGHTNESS 64 // 0-255
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
  {5, 4, 9},   // Group A
  {13, 17, 16},   // Group B
  {10, 14, 18},   // Group C
  {3, 8, 7},// Group D
  {2, 1, 6},// Group E
  {12, 11, 15},// Group F
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

// ================= PRECOMPUTED MAPPING =================
uint32_t pixelDmxIndex[TOTAL_LEDS];
uint32_t pixelLedIndex[TOTAL_LEDS];
float pixelMultiplier[TOTAL_LEDS];

void precomputeMapping() {
  // First, find where each panel is physically located on the Octo outputs
  uint32_t panelLedBase[NUM_PANELS];
  for (uint8_t out = 0; out < NUM_OUTPUTS; out++) {
    for (uint8_t p = 0; p < PANELS_PER_GROUP; p++) {
      uint8_t panelIdx = panelGroups[out][p] - 1; // 0-indexed
      panelLedBase[panelIdx] = (out * LEDS_PER_OUTPUT) + (p * PANEL_PIXELS);
    }
  }

  // Now, map panels 1 to 21 sequentially to Art-Net universes
  // Panel 1 (index 0) = Universe 0, Channel 0
  // Panel 2 (index 1) = next 600 channels, etc.
  uint32_t globalPixel = 0;
  for (uint8_t panelIdx = 0; panelIdx < NUM_PANELS; panelIdx++) {
    Orientation o = panelOrientation[panelIdx];
    uint32_t ledBase = panelLedBase[panelIdx];
    
    for (uint8_t y = 0; y < PANEL_HEIGHT; y++) {
      for (uint8_t x = 0; x < PANEL_WIDTH; x++) {
        uint16_t logical  = orientIndex(x, y, o);
        uint16_t physical = panelLUT[logical];
        
        pixelLedIndex[globalPixel] = ledBase + physical;
        
        // This calculates the DMX address assuming panels 1, 2, 3... are sequential in the DMX stream
        uint32_t currentUniverse = globalPixel / 170;
        uint32_t pixelInUniverse = globalPixel % 170;
        pixelDmxIndex[globalPixel] = (currentUniverse * 512) + (pixelInUniverse * 3);
        
        pixelMultiplier[globalPixel] = panelBrightness[panelIdx] * (GLOBAL_BRIGHTNESS / 255.0);
        
        globalPixel++;
      }
    }
  }
}

// ================= ARTNET RECEIVER =================
ArtnetNativeEther artnet;
uint8_t dmxBuffer[DMX_CHANNELS];
uint8_t dmxBufferBack[DMX_CHANNELS]; // Second buffer to prevent tearing
volatile bool newFrame = false;
volatile uint32_t universesSeen = 0;
uint32_t lastUniverseReceived = 0;
uint32_t maxUniverseSeen = 0;
uint32_t totalPackets = 0;

// ================= ARTDMX CALLBACK =================
void handleArtDmx(const uint8_t *data, uint16_t size,
                  const ArtDmxMetadata &metadata,
                  const ArtNetRemoteInfo &remote)
{
  // Calculate absolute universe: (Subnet * 16) + Universe
  // Art-Net uses 4 bits for Universe and 4 bits for Subnet.
  uint16_t absoluteUni = (metadata.subnet << 4) | metadata.universe;
  
  lastUniverseReceived = absoluteUni;
  totalPackets++;
  if (absoluteUni > maxUniverseSeen) maxUniverseSeen = absoluteUni;
  
  if (absoluteUni >= MAX_UNIVERSES) return;

  uint32_t base = absoluteUni * 512U;
  memcpy(dmxBufferBack + base, data, size);
  
  static uint32_t universeMask = 0;
  universeMask |= (1UL << absoluteUni);
  universesSeen++;

  // Flexible swap: 
  // 1. We see the last expected absolute universe (24)
  // 2. OR we see the current highest known universe
  // 3. OR we've seen enough packets
  if (absoluteUni == 24 || absoluteUni == maxUniverseSeen || universesSeen >= 25) {
    memcpy(dmxBuffer, dmxBufferBack, DMX_CHANNELS);
    newFrame = true;
    universeMask = 0;
    universesSeen = 0;
  }
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

  Serial.print("Listening for ");
  Serial.print(MAX_UNIVERSES);
  Serial.println(" universes.");

  artnet.begin();
  artnet.subscribeArtDmx([](const uint8_t *data, uint16_t size,
                             const ArtDmxMetadata &metadata,
                             const ArtNetRemoteInfo &remote){
    handleArtDmx(data, size, metadata, remote);
  });

  leds.begin();
  precomputeMapping();
  leds.show();
  Serial.println("Ready!");
}

void loop() {
  artnet.parse();

  static uint32_t lastStats = 0;
  static uint32_t frameCount = 0;
  static uint32_t lastShow = 0;

  // Update LEDs if a frame is ready, or if it's been a while since the last update
  // even if not all universes arrived (to keep the display alive).
  // Throttle to 60fps max (16.6ms) to avoid blocking ethernet.
  uint32_t now = micros();
  bool timeout = (now - lastShow > 50000); // 20fps fallback (50ms)
  
  if ((newFrame || timeout) && (now - lastShow > 16666)) {
    newFrame = false;
    frameCount++;
    lastShow = now;

    // Optional: Print diagnostic info to serial once per second
    if (timeout && (frameCount % 12 == 0)) {
       Serial.println("Frame triggered by timeout (missing universes?)");
    }

    // Wait if OctoWS2811 is still busy sending the previous frame
    while (leds.busy()) { /* wait */ }

    // Copy to drawing memory as fast as possible
    for (uint32_t i = 0; i < TOTAL_LEDS; i++) {
      uint32_t dmxIdx = pixelDmxIndex[i];
      // Inline the brightness math to be as fast as possible
      uint32_t r = (uint32_t)(dmxBuffer[dmxIdx + 0] * pixelMultiplier[i]);
      uint32_t g = (uint32_t)(dmxBuffer[dmxIdx + 1] * pixelMultiplier[i]);
      uint32_t b = (uint32_t)(dmxBuffer[dmxIdx + 2] * pixelMultiplier[i]);

      leds.setPixel(pixelLedIndex[i], (r << 16) | (g << 8) | b);
    }

    leds.show();
  }

  if (millis() - lastStats >= 1000) {
    Serial.print("FPS: ");
    Serial.print(frameCount);
    Serial.print(" | LastUni: ");
    Serial.print(lastUniverseReceived);
    Serial.print(" | MaxUni: ");
    Serial.print(maxUniverseSeen);
    Serial.print(" | Pkts: ");
    Serial.println(totalPackets);
    
    frameCount = 0;
    totalPackets = 0;
    lastStats = millis();
  }
}
