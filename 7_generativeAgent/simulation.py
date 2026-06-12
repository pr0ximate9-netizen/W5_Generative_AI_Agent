from config import preset as config
from scripts.agent import build_full_report, build_world


def run_default_simulation(rounds: int = config.DEFAULT_ROUNDS, turns: int = config.DEFAULT_TURNS_PER_AGENT) -> str:
    """기본 SeatWise 시뮬레이션을 실행하고 최종 리포트를 반환한다."""

    world = build_world(turns_per_agent=turns)
    world.run(rounds=rounds, print_output=True)
    final_report = build_full_report(world, config.DEFAULT_REPORT_AGENT)
    print(final_report)
    return final_report


if __name__ == "__main__":
    run_default_simulation()
