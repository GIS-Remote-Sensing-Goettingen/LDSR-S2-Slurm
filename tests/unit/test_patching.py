from ldsrs2_launcher.domain.patching import build_patches, compute_centers, meters_to_lat_deg


def test_compute_centers_single_patch() -> None:
    centers = compute_centers(0.0, 0.0, 0.6, 0.5)
    assert centers == [0.0]


def test_build_patches_returns_one_patch_for_point_bbox() -> None:
    patches = build_patches(0.0, 0.0, 0.0, 0.0, 512, 10.0, 128.0)
    assert len(patches) == 1
    assert patches[0].patch_id == "patch_000001"


def test_meters_to_lat_deg() -> None:
    assert round(meters_to_lat_deg(111_320), 3) == 1.0
