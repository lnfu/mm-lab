# Development

## Commands

| Command | Result |
|---|---|
| `env -u PYTHONPATH uv run pytest` | Runs the tests. |
| `uv run ruff check .` | Checks the code. |
| `uv run ruff format .` | Formats the code. |
| `uv run isaaclab list_envs --show_presets` | Shows the registered tasks. Use it after you add a task. |
| `uv run isaaclab --editor` | Makes the Python settings for VS Code or Cursor. |

## Run the tests

If your shell loads ROS, `PYTHONPATH` contains `/opt/ros/...`.
These ROS paths cause pytest to fail.
Thus, remove `PYTHONPATH` before you run the tests:

```bash
env -u PYTHONPATH uv run pytest
```

