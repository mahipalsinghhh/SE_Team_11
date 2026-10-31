"""RLRS-12 | TC-MAINT-01"""
from rlrs_core.maintenance import affected_reservations, apply_block
from rlrs_core.types import MaintenanceBlock, Status
from .helpers import iv, res


def test_overlapping_active_reservations_are_cancelled():
    block = MaintenanceBlock(1, 7, iv(1, 10, 0, 12, 0), "calibration")
    inside = res(1, 1, 7, iv(1, 10, 30, 11, 0))
    partial = res(2, 2, 7, iv(1, 11, 30, 12, 30))
    touching = res(3, 3, 7, iv(1, 12, 0, 13, 0))
    other_eq = res(4, 4, 8, iv(1, 10, 30, 11, 0))
    already = res(5, 5, 7, iv(1, 10, 30, 11, 0), Status.CANCELLED)
    hit = apply_block(block, [inside, partial, touching, other_eq, already])
    assert {r.id for r in hit} == {1, 2}
    assert inside.status == partial.status == Status.CANCELLED
    assert touching.status == Status.CONFIRMED and other_eq.status == Status.CONFIRMED


def test_affected_does_not_mutate():
    block = MaintenanceBlock(1, 7, iv(1, 10, 0, 12, 0))
    r = res(1, 1, 7, iv(1, 10, 30, 11, 0))
    assert affected_reservations(block, [r]) == [r] and r.status == Status.CONFIRMED
