import argparse
import math

import numpy as np
import attrs

import pooltool as pt
from pooltool.events import EventType
from pooltool.objects import BilliardTableSpecs


def mass_from_radius(radius_m: float, reference: pt.BallParams) -> float:
    density_scale = reference.m / (reference.R**3)
    return density_scale * (radius_m**3)


def rolling_angular_velocity(velocity: np.ndarray, radius_m: float) -> np.ndarray:
    return pt.ptmath.cross(np.array([0.0, 0.0, 1.0]), velocity) / radius_m


def heading_deg(vector: np.ndarray) -> float:
    return math.degrees(math.atan2(vector[1], vector[0]))


def wrap_angle_deg(angle_deg: float) -> float:
    wrapped = (angle_deg + 180.0) % 360.0 - 180.0
    return wrapped


def place_half_ball_pair(
    *,
    cue_id: str,
    object_id: str,
    object_center_xy: tuple[float, float],
    cue_radius_m: float,
    cue_mass_kg: float,
    object_radius_m: float,
    object_mass_kg: float,
    speed_mps: float,
    approach_distance_m: float,
) -> dict[str, pt.Ball]:
    half_ball_offset_m = (cue_radius_m + object_radius_m) / 2.0

    object_ball = pt.Ball.create(
        object_id,
        xy=object_center_xy,
        R=object_radius_m,
        m=object_mass_kg,
    )

    cue_xy = (
        object_center_xy[0] + half_ball_offset_m,
        object_center_xy[1] - approach_distance_m,
    )
    cue_ball = pt.Ball.create(
        cue_id,
        xy=cue_xy,
        R=cue_radius_m,
        m=cue_mass_kg,
    )

    velocity = np.array([0.0, speed_mps, 0.0])
    cue_ball.params = attrs.evolve(cue_ball.params, u_s=0.05, u_r=0.002)
    object_ball.params = attrs.evolve(object_ball.params, u_s=0.05, u_r=0.002)
    cue_ball.state.rvw[1] = velocity
    cue_ball.state.rvw[2] = rolling_angular_velocity(velocity, cue_radius_m)
    cue_ball.state.s = pt.constants.rolling

    return {
        cue_id: cue_ball,
        object_id: object_ball,
    }


def place_comparison_ball(
    *,
    ball_id: str,
    center_xy: tuple[float, float],
    radius_m: float,
    mass_kg: float,
) -> pt.Ball:
    return pt.Ball.create(
        ball_id,
        xy=center_xy,
        R=radius_m,
        m=mass_kg,
    )


def find_pair_collision(system: pt.System, ball_a: str, ball_b: str):
    target_ids = {ball_a, ball_b}
    for event in system.events:
        if event.event_type != EventType.BALL_BALL:
            continue
        if set(event.ids) == target_ids:
            return event
    raise ValueError(f"No collision found for pair {ball_a}/{ball_b}")


def summarize_pair(system: pt.System, cue_id: str, object_id: str) -> str:
    event = find_pair_collision(system, cue_id, object_id)

    cue_ball_after = event.get_ball(cue_id, initial=False)
    object_ball_after = event.get_ball(object_id, initial=False)

    initial_heading = 90.0
    cue_heading = heading_deg(cue_ball_after.vel)
    object_heading = heading_deg(object_ball_after.vel)

    cue_deflection = wrap_angle_deg(cue_heading - initial_heading)
    object_launch = wrap_angle_deg(object_heading - initial_heading)

    return (
        f"{cue_id} -> {object_id} at t={event.time:.6f}s | "
        f"cue heading={cue_heading:.3f} deg "
        f"(deflection {cue_deflection:+.3f} deg), "
        f"object heading={object_heading:.3f} deg "
        f"(launch {object_launch:+.3f} deg)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Simulate two half-ball hits on the same table: 54 mm cue into 54 mm "
            "object ball, and 54 mm cue into 50 mm object ball. Prints the resulting "
            "post-collision headings, then opens the single-table shot in the 3D viewer."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--cue-ball-diameter-mm", type=float, default=54.0)
    parser.add_argument("--object-ball-54-mm", type=float, default=54.0)
    parser.add_argument("--object-ball-50-mm", type=float, default=50.0)
    parser.add_argument("--speed", type=float, default=3.0)
    parser.add_argument("--approach-distance", type=float, default=0.9)
    parser.add_argument("--max-events", type=int, default=800)
    args = parser.parse_args()

    reference = pt.BallParams.default()
    cue_radius = args.cue_ball_diameter_mm / 2000.0
    object_54_radius = args.object_ball_54_mm / 2000.0
    object_50_radius = args.object_ball_50_mm / 2000.0

    cue_mass = mass_from_radius(cue_radius, reference)
    object_54_mass = mass_from_radius(object_54_radius, reference)
    object_50_mass = mass_from_radius(object_50_radius, reference)

    table = pt.Table.from_table_specs(BilliardTableSpecs(l=4.0, w=2.4))
    ballset = pt.objects.BallSet("pooltool_pocket")

    balls = {}
    balls.update(
        place_half_ball_pair(
            cue_id="cue",
            object_id="2",
            object_center_xy=(table.w * 0.20, table.l * 0.68),
            cue_radius_m=cue_radius,
            cue_mass_kg=cue_mass,
            object_radius_m=object_54_radius,
            object_mass_kg=object_54_mass,
            speed_mps=args.speed,
            approach_distance_m=args.approach_distance,
        )
    )
    balls.update(
        place_half_ball_pair(
            cue_id="9",
            object_id="3",
            object_center_xy=(table.w * 0.80, table.l * 0.68),
            cue_radius_m=cue_radius,
            cue_mass_kg=cue_mass,
            object_radius_m=object_50_radius,
            object_mass_kg=object_50_mass,
            speed_mps=args.speed,
            approach_distance_m=args.approach_distance,
        )
    )
    balls["10"] = place_comparison_ball(
        ball_id="10",
        center_xy=(table.w * 0.46, table.l * 0.25),
        radius_m=object_54_radius,
        mass_kg=object_54_mass,
    )
    balls["11"] = place_comparison_ball(
        ball_id="11",
        center_xy=(table.w * 0.54, table.l * 0.25),
        radius_m=object_50_radius,
        mass_kg=object_50_mass,
    )

    for ball in balls.values():
        ball.ballset = ballset

    system = pt.System(
        balls=balls,
        table=table,
        cue=pt.Cue(cue_ball_id="cue"),
    )

    pt.simulate(system, inplace=True, max_events=2000, continuous=True)

    print("Blue target (54 mm):", summarize_pair(system, "cue", "2"))
    print("Red target (50 mm):", summarize_pair(system, "9", "3"))

    pt.show(
        system,
        title=(
            "Single-table half-ball comparison: left blue target = 54 mm, right red "
            "target = 50 mm. Lower pair shows 54 mm blue vs 50 mm red size comparison."
        ),
    )


if __name__ == "__main__":
    main()
