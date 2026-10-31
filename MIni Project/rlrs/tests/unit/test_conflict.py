"""RLRS-4 | TC-CONF-01..04"""
from rlrs_core.conflict import find_conflicts, is_free
from rlrs_core.types import MaintenanceBlock, Status
from .helpers import iv, res

BASE = res(1, 1, 7, iv(1, 10, 0, 11, 0))


def test_before_and_after_do_not_conflict():
    assert is_free(7, iv(1, 8, 0, 9, 0), [BASE])
    assert is_free(7, iv(1, 12, 0, 13, 0), [BASE])


def test_touching_back_to_back_is_accepted():
    assert is_free(7, iv(1, 9, 0, 10, 0), [BASE])
    assert is_free(7, iv(1, 11, 0, 12, 0), [BASE])


def test_partial_overlap_rejected_with_range():
    c = find_conflicts(7, iv(1, 10, 30, 11, 30), [BASE])
    assert len(c) == 1 and c[0].id == 1 and c[0].interval == BASE.interval


def test_containing_and_contained_rejected():
    assert not is_free(7, iv(1, 9, 0, 12, 0), [BASE])
    assert not is_free(7, iv(1, 10, 15, 10, 45), [BASE])


def test_identical_slot_rejected():
    assert not is_free(7, iv(1, 10, 0, 11, 0), [BASE])


def test_other_equipment_unaffected():
    assert is_free(8, iv(1, 10, 0, 11, 0), [BASE])


def test_cancelled_slot_can_be_rebooked():
    BASE_C = res(2, 1, 7, iv(1, 10, 0, 11, 0), Status.CANCELLED)
    assert is_free(7, iv(1, 10, 0, 11, 0), [BASE_C])
    for s in (Status.REJECTED, Status.COMPLETED, Status.NO_SHOW):
        assert is_free(7, iv(1, 10, 0, 11, 0), [res(3, 1, 7, iv(1, 10, 0, 11, 0), s)])


def test_pending_blocks_slot():
    assert not is_free(7, iv(1, 10, 0, 11, 0), [res(4, 1, 7, iv(1, 10, 0, 11, 0), Status.PENDING)])


def test_maintenance_block_conflicts():
    b = MaintenanceBlock(9, 7, iv(1, 14, 0, 16, 0))
    c = find_conflicts(7, iv(1, 15, 0, 15, 30), [], [b])
    assert c and c[0].kind == "maintenance"
