# Copyright (c) 2026, Enfu Liao.
# SPDX-License-Identifier: BSD-3-Clause

"""Static checks on the generated ED305 room USD (no simulator needed)."""

import numpy as np
import pytest
from pxr import Usd, UsdGeom, UsdPhysics

from mm_lab.assets import ED305_META, ED305_USD_PATH

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def stage():
    if not ED305_USD_PATH.exists():
        pytest.skip("room USD not generated; run preprocess/build_room_usd.py")
    return Usd.Stage.Open(str(ED305_USD_PATH))


def test_units_and_up_axis(stage):
    assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z
    assert UsdGeom.GetStageMetersPerUnit(stage) == 1.0


def test_only_room_shell_collides(stage):
    colliders = [p for p in stage.Traverse() if p.HasAPI(UsdPhysics.CollisionAPI)]
    paths = {str(p.GetPath()) for p in colliders}
    assert {"/Room/Structure/Floor", "/Room/Structure/Ceiling"} <= paths
    assert any(p.startswith("/Room/Structure/Walls/Wall_") for p in paths)
    assert all(p.startswith("/Room/Structure/") for p in paths)
    # Boxes only: Newton/MuJoCo would collide a triangle mesh as its convex hull.
    assert all(p.IsA(UsdGeom.Cube) for p in colliders)


def test_room_is_static(stage):
    assert not any(p.HasAPI(UsdPhysics.RigidBodyAPI) for p in stage.Traverse())


def test_metadata(stage):
    assert ED305_META["ceiling_z"] - ED305_META["floor_z"] > 2.0


def test_point_cloud_is_coloured_and_visible(stage):
    prim = stage.GetPrimAtPath("/Room/PointCloud/Room")
    assert prim.IsA(UsdGeom.Points)
    assert stage.GetPrimAtPath("/Room/PointCloud/Ceiling").IsA(UsdGeom.Points)
    assert UsdGeom.Imageable(prim).ComputeVisibility() != UsdGeom.Tokens.invisible
    points = UsdGeom.Points(prim)
    colours = UsdGeom.PrimvarsAPI(prim).GetPrimvar("displayColor")
    assert len(points.GetPointsAttr().Get()) > 100_000
    assert colours.GetInterpolation() == UsdGeom.Tokens.vertex
    assert len(np.unique(np.round(np.array(colours.Get()), 2), axis=0)) > 1000  # real colours, not a flat tint
