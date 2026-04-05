import pytest

from pooltool.objects.ball.datatypes import Ball
from pooltool.system.datatypes import System


def test_cue_ball_id_mismatch():
    system = System.example()

    # Cannot create instance with cue_ball_id not in balls
    system.cue.cue_ball_id = "absent"
    with pytest.raises(ValueError):
        System(
            cue=system.cue,
            balls=system.balls,
            table=system.table,
        )


def test_system_accepts_unequal_radii():
    cue_ball = Ball.create("cue", R=1.0)
    object_ball = Ball.create("1", R=1.5)

    template = System.example()

    system = System(
        balls={"cue": cue_ball, "1": object_ball},
        cue=template.cue,
        table=template.table,
    )

    assert system.balls["cue"].params.R == 1.0
    assert system.balls["1"].params.R == 1.5
