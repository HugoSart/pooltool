import pooltool as pt


def test_e2e_simulate_rack_with_larger_cue_ball():
    cue_ball_diameter_m = 0.054
    object_ball_diameter_m = 0.050

    cue_ball_radius_m = cue_ball_diameter_m / 2
    object_ball_radius_m = object_ball_diameter_m / 2

    table = pt.Table.default()

    balls = pt.get_rack(
        game_type=pt.GameType.EIGHTBALL,
        table=table,
        ball_params=pt.BallParams(R=object_ball_radius_m),
        spacing_factor=1e-5,
    )
    balls["cue"] = pt.Ball.create(
        "cue",
        xy=(table.w / 2, table.l / 4),
        R=cue_ball_radius_m,
    )

    system = pt.System(
        cue=pt.Cue.default(),
        table=table,
        balls=balls,
    )

    system.strike(V0=2.0, phi=pt.aim.at_ball(system, "1", cut=0))

    simulated = pt.simulate(system, inplace=False)

    assert simulated.simulated
    assert simulated.balls["cue"].params.R == cue_ball_radius_m
    assert all(
        ball.params.R == object_ball_radius_m
        for ball_id, ball in simulated.balls.items()
        if ball_id != "cue"
    )
