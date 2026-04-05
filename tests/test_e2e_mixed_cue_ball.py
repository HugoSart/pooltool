import pooltool as pt


def test_e2e_simulate_rack_with_larger_cue_ball():
    cue_ball_diameter_m = 0.054
    object_ball_diameter_m = 0.050

    cue_ball_radius_m = cue_ball_diameter_m / 2
    object_ball_radius_m = object_ball_diameter_m / 2
    default_params = pt.BallParams.default()
    density_scale = default_params.m / (default_params.R**3)
    object_ball_mass_kg = density_scale * (object_ball_radius_m**3)
    cue_ball_mass_kg = density_scale * (cue_ball_radius_m**3)

    table = pt.Table.default()

    balls = pt.get_rack(
        game_type=pt.GameType.EIGHTBALL,
        table=table,
        ball_params=pt.BallParams(R=object_ball_radius_m),
        spacing_factor=1e-5,
    )
    for ball_id, ball in balls.items():
        if ball_id == "cue":
            continue

        ball.params = pt.BallParams(
            m=object_ball_mass_kg,
            R=object_ball_radius_m,
        )
        ball.state.rvw[0][2] = object_ball_radius_m

    balls["cue"] = pt.Ball.create(
        "cue",
        xy=(table.w / 2, table.l / 4),
        R=cue_ball_radius_m,
        m=cue_ball_mass_kg,
    )

    system = pt.System(
        cue=pt.Cue.default(),
        table=table,
        balls=balls,
    )

    system.strike(V0=2.0, phi=pt.aim.at_ball(system, "1", cut=0))

    simulated = pt.simulate(system, inplace=False, max_events=200)

    assert simulated.simulated
    assert simulated.balls["cue"].params.R == cue_ball_radius_m
    assert simulated.balls["cue"].params.m == cue_ball_mass_kg
    assert all(
        ball.params.R == object_ball_radius_m
        for ball_id, ball in simulated.balls.items()
        if ball_id != "cue"
    )
    assert all(
        ball.params.m == object_ball_mass_kg
        for ball_id, ball in simulated.balls.items()
        if ball_id != "cue"
    )
