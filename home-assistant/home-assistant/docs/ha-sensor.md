# ha sensor

Shows the input's value in Home Assistant as a sensor: a number or text.

Needs an **ha device** node in the flow.

## Properties

- **name**: the entity's name in Home Assistant. Required.
- **device class**: what the sensor measures, such as `temperature` or `humidity`: Home Assistant picks the icon and
  the units it accepts from it. Default `none`.
- **unit**: the unit of the value, such as `°C`, `%` or `V`. With a device class it must be one Home Assistant
  accepts for that class (below).
- **state class**: `measurement` for a value that goes up and down, `total` or `total increasing` for a running
  total. Home Assistant keeps long-term statistics for these. Default `none`.
- **icon**: a Material Design icon, such as `mdi:knob`. Optional: the device class gives one.

| Device class | Units |
| --- | --- |
| temperature | °C, °F, K |
| humidity, battery | % |
| pressure | Pa, hPa, kPa, bar, mbar, mmHg, inHg, psi |
| illuminance | lx |
| voltage | V, mV |
| current | A, mA |
| power | W, kW |
| energy | Wh, kWh, MWh |
| signal strength | dB, dBm |
| duration | d, h, min, s, ms |

## Wiring

**Input**: the value in `payload`:

| `payload` | Home Assistant shows |
| --- | --- |
| an int | it, as written |
| a float | it, as short as it can be written exactly, with no exponent for everyday sizes (0.1, not 1e-01) |
| text | the text |
| `None` | nothing is sent; the sensor keeps its last value |

## Behavior

Each message sends the value to Home Assistant at once. The broker keeps the latest, so a Home Assistant that
restarts shows it straight away.

The sensor shows as unknown until the flow sends it a value: see "Showing a value from the start" in the bundle README.

## Errors

- **`payload` is `True` or `False`.** The node raises `a sensor shows numbers or text -- use ha binary sensor for
  true/false`.
- **`payload` is a dict.** The node raises an error saying to pick one field first, for example with a function node.

These stop the compile: no **ha device** in the flow, an empty name, a unit the device class doesn't accept.
