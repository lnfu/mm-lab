# mm-lab

An Isaac Lab 3.0.0 project (Isaac Sim 6.2, Newton physics) with a model of classroom ED305.

## Install

```bash
uv sync
export OMNI_KIT_ACCEPT_EULA=yes
```

## Show the room

| Command | Result |
|---|---|
| `uv run python scripts/view_room.py --livestream 2` | Sends the view to a WebRTC client. |
| `DISPLAY=:1 uv run python scripts/view_room.py --viz kit` | Opens an Isaac Sim window on display `:1`. |
| `uv run python scripts/view_room.py --save-images` | Saves two images in `logs/view_room/`. |

Add `--backend physx` to use PhysX instead of Newton.

For the livestream, use the [Isaac Sim WebRTC Streaming Client](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/download.html).
Connect to `10.50.80.1`.
The network must not block TCP 49100 and UDP 47998.

## Documents

- [docs/room.md](docs/room.md): The room model
- [docs/structure.md](docs/structure.md): The project structure
- [docs/development.md](docs/development.md): Tests and code checks
