# ha binary sensor

Shows the input in Home Assistant as on or off.

Needs an **ha device** node in the flow.

## Properties

- **name**: the entity's name in Home Assistant. Required.
- **device class**: what it senses, such as `door`, `motion` or `problem`: Home Assistant shows on and off as open and
  closed, detected and clear, and so on. Default `none`.
- **on start**: the state the sensor starts with at flow start: `unknown` (default), `off`, or `on`.

## Wiring

**Input**: `payload` is on when it's true in Python (`True`, a non-zero number, non-empty text) and off when it's
false (`False`, `0`, empty text). `None` sends nothing.

## Behavior

Each message sends on or off to Home Assistant at once. The broker keeps the latest, so a Home Assistant that
restarts shows it straight away.

For one fed by events, such as a button, set **on start** to the resting state, `off`: the sensor starts with it,
so it doesn't show unknown while the first event is still to come.

## Errors

These stop the compile: no **ha device** in the flow, an empty name.
