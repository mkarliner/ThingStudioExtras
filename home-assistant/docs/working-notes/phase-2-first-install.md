# Home Assistant bundle — Phase 2: the first-install path (2026-11-27)

Plan, Phase 2: "Walk the Set up a board → Board settings → deploy steps as an HA user would, fix gaps, and link it
from the bundle README." Done on paper from the user guide at ThingStudio `main` a57d686b (read through the GitHub
API, `docs/user-guide/` only). The steps that need a board are checks for Mike's end-to-end run, at the end.

## Who

Someone who runs Home Assistant, perhaps has flashed an ESPHome board, has never used ThingStudio, and wants a board's
readings and controls in HA. Not a developer.

## The walk

| Step | Guide page | What an HA user meets | Done |
| --- | --- | --- | --- |
| Install ThingStudio | *Getting started*, *Installation details* | The bundle needs `main` (a57d686b). The latest release, v0.13.0 (2026-11-18), is 178 commits behind. So today: a source build with git, `make` and Python 3.11+, a developer's route. | README says so plainly. **Only a release fixes it** (Mike). |
| App or Web | *Use it in your browser*, *custom-nodes.md* | Web is the easy route the guide offers first, but has no custom nodes or libraries. | README: "ThingStudio Web won't do". |
| Install MicroPython | *Step 3* | Fine. The C3 and PSRAM-less ESP32 advice (custom image) matters more with WiFi + MQTT + these nodes. | README step 2 repeats it. |
| Connect, runtime | *Steps 4, 5* | Fine. Web's *Set up a board* page could do it without a terminal, but its runtime would be a release's, and a runtime that doesn't match the editor stops deploys (*Step 5*). Until a release, use the App for both. | Not in README (it would mislead until a release). |
| Board settings | *Connecting over WiFi* | Name and password. An HA user wants the board in place, not on a USB cable: the password is what allows WiFi deploys. The guide doesn't say whether the name set here is the board's hostname, which **ha device** uses as the device name. | README step 4. Hostname question: check at the board. |
| First flow | *Step 6* | A useful check, optional for this user. | README step 5. |
| MQTT in HA | (none: the guide never mentions Home Assistant) | Mosquitto add-on, an HA user, the integration. | README section (1.10). The guide pointer is request `ha-bundle-pointer`. |
| Credentials | *Editor in depth, Config nodes*; *The ThingStudio folder* | The examples named Mike's credentials (`mihome`, `lan-mqtt-broker`). Opening one, ✎ says the credential isn't saved here and saving creates it (*Config nodes*), which is workable but puzzling with someone else's names. | New `starter-ha` example names `home-wifi` and `home-assistant-mqtt`; README walks through ✎. The board-specific examples keep Mike's names (his test setup). |
| A first HA flow | | Both examples were for particular boards (kitchen-sink C3, Freenove S3). | New `examples/starter-ha.flow.json`: any WiFi board, no wiring (uptime, free memory, a test switch with its state wired back, a button). Compile tests on a classic ESP32 and a Pico W; also compiles for C3, S2, S3. |

## Changes

- Bundle README: "What you need" (the App, `main`, why not Web), a new "New to ThingStudio?" route through the guide
  with the choices this user needs, and "Use" starting from the starter example and its credentials.
- `examples/starter-ha.flow.json`, and two compile-test cases (29 cases, 0 failed).

## For Mike

1. **A ThingStudio release that includes a57d686b.** It turns the hardest step (a source build) into the guide's
   normal install. Then the README names that release, and the HA user path is the guide's own.
2. **Checks at the board**, alongside 1.9. Ideally on a board that hasn't run ThingStudio, following the README's
   "New to ThingStudio?" and "Use" as written, noting each place you stop or guess:
   - Does the name set in **Tools → Board settings…** become the device name in HA (with **device name** empty)?
     If not, that's a core request: the guide should say what the board's hostname is.
   - ✎ on the starter's unsaved credentials behaves as the README says.
   - The starter on an ESP32-C3 with the custom image: the free-memory figure HA shows.
   - Deploy over WiFi once the board is away from the computer.
