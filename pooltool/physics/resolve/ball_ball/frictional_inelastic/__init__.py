import attrs
import numpy as np

import pooltool.constants as const
import pooltool.ptmath as ptmath
from pooltool.objects.ball.datatypes import Ball, BallState
from pooltool.physics.resolve.ball_ball.core import CoreBallBallCollision
from pooltool.physics.resolve.ball_ball.friction import (
    AlciatoreBallBallFriction,
    BallBallFrictionStrategy,
)
from pooltool.physics.resolve.models import BallBallModel


def _sphere_inertia(m: float, R: float) -> float:
    return 2.0 / 5.0 * m * R * R


def _resolve_ball_ball(rvw1, rvw2, R1, R2, m1, m2, u_b, e_b):
    r1, v1, w1 = rvw1.copy()
    r2, v2, w2 = rvw2.copy()

    n = ptmath.unit_vector(np.array([r2[0] - r1[0], r2[1] - r1[1], 0.0]))
    rel_normal_speed = float(np.dot(v1 - v2, n))

    if rel_normal_speed <= const.EPS:
        return rvw1, rvw2

    inv_m1 = 1.0 / m1
    inv_m2 = 1.0 / m2
    I1 = _sphere_inertia(m1, R1)
    I2 = _sphere_inertia(m2, R2)

    r_contact_1 = R1 * n
    r_contact_2 = -R2 * n
    contact_v1 = v1 + ptmath.cross(w1, r_contact_1)
    contact_v2 = v2 + ptmath.cross(w2, r_contact_2)
    contact_rel = contact_v1 - contact_v2

    v_rel_n = float(np.dot(contact_rel, n))
    v_rel_t = contact_rel - v_rel_n * n

    j_n = (1.0 + e_b) * v_rel_n / (inv_m1 + inv_m2)
    impulse = j_n * n

    v_rel_t_mag = ptmath.norm3d(v_rel_t)
    if v_rel_t_mag > const.EPS:
        t_hat = v_rel_t / v_rel_t_mag
        tangential_mass = inv_m1 + inv_m2 + (R1 * R1) / I1 + (R2 * R2) / I2
        j_t_no_slip = v_rel_t_mag / tangential_mass
        j_t = min(u_b * j_n, j_t_no_slip)
        impulse += j_t * t_hat

    v1_f = v1 - impulse * inv_m1
    v2_f = v2 + impulse * inv_m2
    w1_f = w1 - ptmath.cross(r_contact_1, impulse) / I1
    w2_f = w2 + ptmath.cross(r_contact_2, impulse) / I2

    rvw1_f = rvw1.copy()
    rvw2_f = rvw2.copy()
    rvw1_f[1] = v1_f
    rvw1_f[2] = w1_f
    rvw2_f[1] = v2_f
    rvw2_f[2] = w2_f
    rvw1_f[1][2] = 0.0
    rvw2_f[1][2] = 0.0

    return rvw1_f, rvw2_f


@attrs.define
class FrictionalInelastic(CoreBallBallCollision):
    """A simple ball-ball collision model including ball-ball friction, and coefficient of restitution for equal-mass balls

    Largely inspired by Dr. David Alciatore's technical proofs
    (https://billiards.colostate.edu/technical_proofs), in particular, TP_A-5, TP_A-6,
    and TP_A-14. These ideas have been extended to include motion of both balls, and a
    more complete analysis of velocity and angular velocity in their vector forms.
    """

    friction: BallBallFrictionStrategy = AlciatoreBallBallFriction()

    model: BallBallModel = attrs.field(
        default=BallBallModel.FRICTIONAL_INELASTIC, init=False, repr=False
    )

    def solve(self, ball1: Ball, ball2: Ball) -> tuple[Ball, Ball]:
        """Resolves the collision."""
        rvw1, rvw2 = _resolve_ball_ball(
            ball1.state.rvw.copy(),
            ball2.state.rvw.copy(),
            ball1.params.R,
            ball2.params.R,
            ball1.params.m,
            ball2.params.m,
            u_b=self.friction.calculate_friction(ball1, ball2),
            # Average the coefficient of restitution parameters for the two balls
            e_b=(ball1.params.e_b + ball2.params.e_b) / 2,
        )

        ball1.state = BallState(rvw1, const.sliding)
        ball2.state = BallState(rvw2, const.sliding)

        return ball1, ball2
