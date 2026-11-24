# Copyright (c) 2026, Enfu Liao.
# SPDX-License-Identifier: BSD-3-Clause

"""Load the ED305 room and look at it.

With a viewer (``--viz kit`` or ``--livestream``) the simulation runs until the window or stream client closes it.
Headless runs load the room, optionally save two camera views, and exit.

.. code-block:: bash

    uv run python scripts/view_room.py --livestream 2     # watch with the WebRTC Streaming Client
    DISPLAY=:1 uv run python scripts/view_room.py --viz kit
    uv run python scripts/view_room.py --save_images      # headless, images in logs/view_room/
"""

import argparse
import os

from isaaclab.app import add_launcher_args, launch_simulation

parser = argparse.ArgumentParser(description="Load the ED305 room and look at it.")
parser.add_argument("--save_images", action="store_true", help="Save two camera views.")
parser.add_argument("--output_dir", default="logs/view_room", help="Where to write images.")
add_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.enable_cameras = args_cli.save_images
# Isaac Lab 3: without a visualizer (--viz) or livestream (--livestream / LIVESTREAM) the run is headless.
livestream = args_cli.livestream if args_cli.livestream is not None and args_cli.livestream >= 0 else -1
livestream = livestream if livestream >= 0 else int(os.environ.get("LIVESTREAM", 0))
interactive = livestream > 0 or str(args_cli.visualizer or "none").lower() not in ("none", "[]")

import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402

import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from isaaclab.utils import instantiate  # noqa: E402

from mm_lab.assets import ED305_META, ED305_ROOM_CFG  # noqa: E402


def make_cameras():
    """Two cameras; ``main`` places one high in a corner and one at eye height in another corner."""
    from isaaclab.sensors.camera import CameraCfg

    for k in range(2):
        sim_utils.create_prim(f"/World/Cams/Cam_{k}", "Xform")
    # "[^/]+" matches one path segment; in Isaac Lab 3 ".*" would also match "/".
    return instantiate(
        CameraCfg(
            prim_path="/World/Cams/Cam_[^/]+/Sensor",
            update_period=0,
            height=720,
            width=1280,
            data_types=["rgb"],
            spawn=sim_utils.PinholeCameraCfg(focal_length=14.0, clipping_range=(0.05, 100.0)),
        )
    )


def main():
    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0, device=args_cli.device)
    with launch_simulation(sim_cfg, args_cli):
        sim = SimulationContext(sim_cfg)
        ED305_ROOM_CFG.spawn.func(ED305_ROOM_CFG.prim_path, ED305_ROOM_CFG.spawn)
        for path, light in (
            ("/World/DomeLight", sim_utils.DomeLightCfg(intensity=1500.0, color=(0.9, 0.9, 0.9))),
            ("/World/SunLight", sim_utils.DistantLightCfg(intensity=1500.0, angle=1.0)),
        ):
            light.func(path, light)

        (x0, y0), (x1, y1) = ED305_META["bounds_xy"]
        cx, cy, z_ceil = (x0 + x1) / 2, (y0 + y1) / 2, ED305_META["ceiling_z"]
        # Start inside the room: the scan includes the ceiling, which hides the room from above.
        sim.set_camera_view([x0 + 2.0, y0 + 1.0, 1.7], [cx + 2.0, cy + 1.0, 0.6])
        camera = make_cameras() if args_cli.save_images else None
        sim.reset()

        if camera is not None:
            eyes = torch.tensor([[x1 - 0.6, y0 + 0.6, z_ceil - 0.3], [x0 + 2.0, y0 + 1.0, 1.6]], device=sim.device)
            targets = torch.tensor([[cx - 2.0, cy + 1.0, 0.0], [cx + 2.0, cy + 1.0, 0.6]], device=sim.device)
            camera.set_world_poses_from_view(eyes, targets)
            for _ in range(30):  # let the renderer converge
                sim.step()
                camera.update(sim.get_physics_dt())
            os.makedirs(args_cli.output_dir, exist_ok=True)
            rgb = camera.data.output["rgb"].cpu().numpy()[..., :3].astype(np.uint8)
            for k, view in enumerate(("corner_high", "corner_eye")):
                Image.fromarray(rgb[k]).save(f"{args_cli.output_dir}/{view}.png")
            print(f"[view] saved images to {args_cli.output_dir}/")

        print(f"[view] ED305 room loaded (floor z={ED305_META['floor_z']:.3f}, ceiling z={z_ceil:.3f})")
        while interactive and sim.is_running():
            sim.step()


if __name__ == "__main__":
    main()
