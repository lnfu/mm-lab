# Project structure

```
scripts/
  view_room.py          Loads the room. Shows it or saves images.
src/mm_lab/
  assets/ed305.py       Defines ED305_ROOM_CFG and ED305_META.
  assets/data/ed305/    Contains the room files.
  tasks/                Contains the Isaac Lab tasks. There are no tasks at this time.
tests/                  Contains the pytest tests. The tests do not start the simulator.
docs/                   Contains the project documents.
```

## Tasks

Put new Isaac Lab tasks in `src/mm_lab/tasks/`.
The `isaaclab.tasks` entry point in `pyproject.toml` registers them.

