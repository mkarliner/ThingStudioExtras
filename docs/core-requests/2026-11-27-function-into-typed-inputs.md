# A computed value can't reach a number input

**Type: core** (or **docs**, if there is a documented way we missed). Status: not filed.

## What we were trying to do

Write the Home Assistant set's example flow for the Freenove ESP32-S3 4" board: a Home Assistant switch and a
brightness slider (0-100 %) driving the screen backlight on GPIO 45 through a **pwm out** node. Each needs a small
calculation (percent to a 0.0-1.0 duty, and 0 when the switch is off), which is a **function** node's job.

## What the user guide says

- *Nodes, pwm out, "Wiring"*: "A string, even `"0.5"`, fails: convert it first, in a [function](function.md) node."
- *Nodes, function, "Wiring"*: "Every output has type `any`."
- *Working in the editor, "Wiring"*: "An `any` output, such as the output of a function node, connects only to
  `any`, `bool` and `bytes` inputs." pwm out's input is `number`.
- *Typed values*: **change** can set a typed literal, but not a value computed from the message.

So the pwm out page's advice can't be followed, and nothing in the guide gives a way to turn a computed value into a
`number` for **pwm out** (or any `number` or `int` input).

## What happened

```
node dist-cli/thingstudio-compile.mjs --custom-nodes <bundle> --board board:freenove-s3-4in freenove-s3-ha.flow.json
error: wire from node brightfn output 1 to node backlight input 1: the editor would refuse this wire (any from function into number to pwm_out)
```

ThingStudio `main` at a57d686b. The example now wires **ha number** (typed `number`) straight into **pwm out**, as a
0-1 fraction, and the switch does something else.

## What we need

A documented way for a computed value to reach a `number` or `int` input. For example, a function node whose outputs
can be given a type (checked on the board like a string into a number input is today), or `number`/`int` inputs
accepting `any` with the same board-side check. And the pwm out page's sentence fixed to match.
