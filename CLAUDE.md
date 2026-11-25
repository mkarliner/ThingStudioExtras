# Project rules for ThingStudioExtras (Claude Code)

@AGENTS.md

The sections below are specific to the Claude Code agent sandbox, which shares a live-mounted copy of this repo with
Mike's real Mac.

## Folder access

Only `~/Src/ThingStudioExtras` is attached to this project. Don't ask for access to `~/Src/ThingStudio` or any other
checkout of core: the "user documentation only" rule in `AGENTS.md` depends on it.

## Commands handed to Mike: zsh on macOS, no comments

Mike runs commands in zsh on a Mac. Interactive zsh doesn't treat `#` as a comment and can misread `~`. Give command
blocks with no comments; put explanation in the prose around them.

## Git writes from the agent sandbox

The sandbox cannot delete files it creates in the shared repo, so git commands from it (even `git status`) can leave
`.git/index.lock` behind and silently block Mike's next commit. Read-only git from the sandbox is fine for what it
reports. For `add`/`commit`, hand Mike the exact commands, always starting with `rm -f .git/index.lock`.

## Scratch files

Keep scratch work (MicroPython builds, ThingStudio installs, test drivers) in the session's own workspace, not in this
folder: files created here can't be deleted from the sandbox.
