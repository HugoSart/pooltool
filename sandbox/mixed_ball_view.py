import argparse

import pooltool as pt


def mass_from_radius(radius_m: float, reference: pt.BallParams) -> float:
    density_scale = reference.m / (reference.R**3)
    return density_scale * (radius_m**3)


def recolor_rack_balls(
    balls: dict[str, pt.Ball],
    *,
    radius_m: float,
    mass_kg: float,
) -> None:
    for ball_id, ball in balls.items():
        if ball_id == "cue":
            continue

        ball.params = pt.BallParams(
            m=mass_kg,
            R=radius_m,
        )
        ball.state.rvw[0][2] = radius_m


def build_system(
    *,
    cue_ball_radius_m: float,
    cue_ball_mass_kg: float,
    object_ball_radius_m: float,
    object_ball_mass_kg: float,
    speed: float,
    max_events: int,
) -> pt.System:
    table = pt.Table.default()
    ballset = pt.objects.BallSet("pooltool_pocket")

    balls = pt.get_rack(
        game_type=pt.GameType.EIGHTBALL,
        table=table,
        ball_params=pt.BallParams(R=object_ball_radius_m, m=object_ball_mass_kg),
        ballset=ballset,
        spacing_factor=1e-5,
    )
    recolor_rack_balls(
        balls,
        radius_m=object_ball_radius_m,
        mass_kg=object_ball_mass_kg,
    )

    balls["cue"] = pt.Ball.create(
        "cue",
        xy=(table.w / 2, table.l / 4),
        ballset=ballset,
        R=cue_ball_radius_m,
        m=cue_ball_mass_kg,
    )

    system = pt.System(
        cue=pt.Cue.default(),
        table=table,
        balls=balls,
    )
    system.strike(V0=speed, phi=pt.aim.at_ball(system, "1", cut=0))
    pt.simulate(system, inplace=True, max_events=max_events)
    return system


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Visualize a mixed-ball shot in the 3D viewer. The viewer opens with two "
            "shots: a reference rack where every ball matches the colored-ball size, "
            "and a mixed rack with a larger/heavier cue ball. Use n/p to switch shots."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--cue-ball-diameter-mm",
        type=float,
        default=54.0,
        help="Cue ball diameter in millimeters for the mixed-ball shot.",
    )
    parser.add_argument(
        "--object-ball-diameter-mm",
        type=float,
        default=50.0,
        help="Object ball diameter in millimeters.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=2.0,
        help="Cue strike speed in meters per second.",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=200,
        help="Safety cap for event-based simulation.",
    )
    args = parser.parse_args()

    reference = pt.BallParams.default()
    cue_ball_radius_m = args.cue_ball_diameter_mm / 2000
    object_ball_radius_m = args.object_ball_diameter_mm / 2000
    cue_ball_mass_kg = mass_from_radius(cue_ball_radius_m, reference)
    object_ball_mass_kg = mass_from_radius(object_ball_radius_m, reference)

    reference_system = build_system(
        cue_ball_radius_m=object_ball_radius_m,
        cue_ball_mass_kg=object_ball_mass_kg,
        object_ball_radius_m=object_ball_radius_m,
        object_ball_mass_kg=object_ball_mass_kg,
        speed=args.speed,
        max_events=args.max_events,
    )
    mixed_system = build_system(
        cue_ball_radius_m=cue_ball_radius_m,
        cue_ball_mass_kg=cue_ball_mass_kg,
        object_ball_radius_m=object_ball_radius_m,
        object_ball_mass_kg=object_ball_mass_kg,
        speed=args.speed,
        max_events=args.max_events,
    )

    pt.show(
        pt.MultiSystem([reference_system, mixed_system]),
        title=(
            "Mixed-ball viewer: shot 1 = equal balls, shot 2 = mixed cue ball. "
            "Use n/p to switch shots."
        ),
    )


if __name__ == "__main__":
    main()
