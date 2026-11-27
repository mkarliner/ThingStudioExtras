# Source build fails on Python 3.10, which the guide says is enough

**Type: core** (the requirements and the stated minimum disagree; which one changes is core's call). Status: filed as [#23](https://github.com/mkarliner/ThingStudio/issues/23) on 2026-11-27, then found already fixed on `main` by b5b83cdb (3.11 minimum, `make` checks it). #23 closed with a note, 2026-11-27.

## What we were trying to do

Build the `user-libraries` branch (commit 8f8d137b) from source on Linux x86_64 with Python 3.10.12 and Node 22.23.5.

## What the user guide says

Installation details, "From source": "You need Python 3.10 or later, Node.js 22 ... and `make`." "If your `python3` is
older than 3.10, name a newer one: `make PYTHON=python3.12`."

## What happened

`make` built the editor, then failed installing the backend:

```
.venv/bin/python -m pip install --quiet --require-hashes -r backend/requirements.txt
ERROR: Could not find a version that satisfies the requirement multidict==7.2.1 (from versions: ... 7.0.0, 7.1.0)
ERROR: No matching distribution found for multidict==7.2.1
make: *** [Makefile:111: .venv/.installed] Error 1
```

PyPI gives `multidict` 7.2.1 `requires_python >=3.11`. With `make PYTHON=<python3.12>` the build completed.

## What we need

Either requirements that install on 3.10, or the guide (and `make`'s own check, as it does for Node) saying 3.11 or
later. A version check in `make` would turn the pip error into a clear message.
