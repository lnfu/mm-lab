# Copyright (c) 2026, Enfu Liao.
# SPDX-License-Identifier: BSD-3-Clause

"""Load the ED305 room and look at it.

With a viewer (``--viz kit`` or ``--livestream``) the simulation runs until the window or stream client closes it.
Headless runs load the room, optionally save two camera views, and exit.

.. code-block:: bash

    uv run python scripts/view_room.py --livestream 2     # watch with the WebRTC Streaming Client
    DISPLAY=:1 uv run python scripts/view_room.py --viz kit
    uv run python scripts/view_room.py --save-images      # headless, images in logs/view_room/
    uv run python scripts/view_room.py --backend physx    # PhysX instead of Newton
"""

import argparse
import math
import os
from types import SimpleNamespace

from isaaclab.app import add_launcher_args, launch_simulation

parser = argparse.ArgumentParser(description="Load the ED305 room and look at it.")
# Not "--physics": Isaac Lab's launcher reads args.physics itself (e.g. physics=newton_mjwarp).
parser.add_argument("--backend", choices=("newton", "physx"), default="newton", help="Physics backend.")
parser.add_argument("--save-images", action="store_true", help="Save two camera views.")
parser.add_argument("--output-dir", default="logs/view_room", help="Where to write images.")
add_launcher_args(parser)
args_cli = parser.parse_args()
args_cli.enable_cameras = args_cli.save_images
# Isaac Lab 3: without a visualizer (--viz) or livestream (--livestream / LIVESTREAM) the run is headless.
livestream = args_cli.livestream if args_cli.livestream is not None and args_cli.livestream >= 0 else -1
livestream = livestream if livestream >= 0 else int(os.environ.get("LIVESTREAM", 0))
interactive = livestream > 0 or str(args_cli.visualizer or "none").lower() not in ("none", "[]")

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.assets import AssetBaseCfg  # noqa: E402
from isaaclab.scene import InteractiveSceneCfg  # noqa: E402
from isaaclab.sensors.camera import CameraCfg  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from isaaclab.utils import configclass, instantiate  # noqa: E402

from mm_lab.assets import ED305_META, ED305_ROOM_CFG  # noqa: E402

(X0, Y0), (X1, Y1) = ED305_META["bounds_xy"]
CX, CY, Z_CEIL = (X0 + X1) / 2, (Y0 + Y1) / 2, ED305_META["ceiling_z"]
VIEWS = {  # name: (eye, target); inside the room, because the scan includes the ceiling
    "corner_high": ((X1 - 0.6, Y0 + 0.6, Z_CEIL - 0.3), (CX - 2.0, CY + 1.0, 0.0)),
    "corner_eye": ((X0 + 2.0, Y0 + 1.0, 1.6), (CX + 2.0, CY + 1.0, 0.6)),
}


def look_at(eye, target) -> tuple[float, float, float, float]:
    """Quaternion (x, y, z, w) of a world-convention camera (+X forward, +Z up) at ``eye`` looking at ``target``."""
    dx, dy, dz = np.subtract(target, eye)
    yaw, pitch = math.atan2(dy, dx), -math.atan2(dz, math.hypot(dx, dy))
    cy, sy, cp, sp = math.cos(yaw / 2), math.sin(yaw / 2), math.cos(pitch / 2), math.sin(pitch / 2)
    return (-sy * sp, cy * sp, sy * cp, cy * cp)  # Rz(yaw) * Ry(pitch)


def camera(name: str) -> CameraCfg:
    # Pose fixed at spawn: with Newton, poses set later (set_world_poses) do not reach the RTX renderer.
    eye, target = VIEWS[name]
    return CameraCfg(
        prim_path=f"{{ENV_REGEX_NS}}/Camera_{name}",
        update_period=0,
        height=720,
        width=1280,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(focal_length=14.0, clipping_range=(0.05, 100.0)),
        offset=CameraCfg.OffsetCfg(pos=eye, rot=look_at(eye, target), convention="world"),
    )


@configclass
class RoomSceneCfg(InteractiveSceneCfg):
    """The room and its lights. Newton only simulates assets that are declared in an interactive scene."""

    room = ED305_ROOM_CFG
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight", spawn=sim_utils.DomeLightCfg(intensity=1500.0, color=(0.9, 0.9, 0.9))
    )
    sun_light = AssetBaseCfg(prim_path="/World/SunLight", spawn=sim_utils.DistantLightCfg(intensity=1500.0, angle=1.0))


@configclass
class RoomSceneWithCamerasCfg(RoomSceneCfg):
    camera_corner_high = camera("corner_high")
    camera_corner_eye = camera("corner_eye")


def physics_cfg():
    if args_cli.backend == "physx":
        from isaaclab_physx.physics import PhysxCfg

        return PhysxCfg()
    # MJWarp, Newton's main solver, needs at least one joint, and the room alone is static. XPBD accepts a static
    # scene. Use NewtonCfg(solver_cfg=MJWarpSolverCfg()) for scenes with robots or other moving bodies.
    from isaaclab_newton.physics import NewtonCfg, XPBDSolverCfg

    return NewtonCfg(solver_cfg=XPBDSolverCfg())


def main():
    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0, device=args_cli.device, physics=physics_cfg())
    scene_cfg = (RoomSceneWithCamerasCfg if args_cli.save_images else RoomSceneCfg)(num_envs=1, env_spacing=0.0)
    # Pass the scene too: the launcher starts Isaac Sim (Kit) only if it finds a Kit camera or viewer in the configs.
    with launch_simulation(SimpleNamespace(sim=sim_cfg, scene=scene_cfg), args_cli):
        sim = SimulationContext(sim_cfg)
        scene = instantiate(scene_cfg)
        sim.set_camera_view(*VIEWS["corner_eye"])
        sim.reset()
        solver_cfg = getattr(sim.cfg.physics, "solver_cfg", None)
        solver = f" ({type(solver_cfg).__name__})" if solver_cfg is not None else ""
        print(f"[view] ED305 room loaded with {type(sim.cfg.physics).__name__}{solver} (ceiling z={Z_CEIL:.3f})")
        dt = sim.get_physics_dt()

        if args_cli.save_images:
            for _ in range(30):  # let the renderer converge
                sim.step()
                scene.update(dt)
            os.makedirs(args_cli.output_dir, exist_ok=True)
            for name in VIEWS:
                rgb = scene[f"camera_{name}"].data.output["rgb"][0, ..., :3].cpu().numpy().astype(np.uint8)
                Image.fromarray(rgb).save(f"{args_cli.output_dir}/{name}.png")
            print(f"[view] saved images to {args_cli.output_dir}/")

        while interactive and sim.is_running():
            sim.step()


if __name__ == "__main__":
    main()
