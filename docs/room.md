# ED305 room model

ED305 is a classroom in Engineering Building 4 (ED) of National Yang Ming Chiao Tung University (NYCU).

## Use the room in code

```python
from mm_lab.assets import ED305_META, ED305_ROOM_CFG
```

- `ED305_ROOM_CFG` is an `AssetBaseCfg` at `/World/Room`. Spawn it one time only.
- `ED305_META` contains the floor height, the ceiling height, and the xy limits.

The room uses the frame of the real map: z up, meters, floor at z = 0.

## Parts of the model

| Prim | Contents | Collision |
|---|---|---|
| `/Room/PointCloud/Room` | Color point cloud from a real scan | No |
| `/Room/PointCloud/Ceiling` | Ceiling points of the scan | No |
| `/Room/Structure/Floor` | Floor at z = 0.005 | Box |
| `/Room/Structure/Ceiling` | Ceiling at z = 2.786 (not visible) | Box |
| `/Room/Structure/Walls` | Walls | Triangle mesh |
| `/Room/Structure/Door_0` | Closed door | Box |
| `/Room/Structure/Window_0`, `Window_1` | Windows | Box |

To see into the room from above, set `/Room/PointCloud/Ceiling` to not visible.

## Files

The files are in `src/mm_lab/assets/data/ed305/`:

| File | Contents |
|---|---|
| `ed305_room.usd` | The room. It refers to the point cloud file. |
| `ed305_room_pointcloud.usd` | The point cloud (37 MB, Git LFS) |
| `ed305_room.json` | Floor height, ceiling height, and xy limits |
