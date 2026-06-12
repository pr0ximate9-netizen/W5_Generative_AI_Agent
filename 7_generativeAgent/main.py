import argparse

from config import preset as config
from scripts.agent import build_full_report, build_world, load_world, parse_time, save_report, save_world


def main() -> None:
    parser = argparse.ArgumentParser(description="SeatWise multi-agent simulator")
    parser.add_argument("--rounds", type=int, default=config.DEFAULT_ROUNDS, help="실행할 토론 라운드 수")
    parser.add_argument("--turns", type=int, default=config.DEFAULT_TURNS_PER_AGENT, help="라운드마다 Agent별 발화 수")
    parser.add_argument("--topic", default=config.DEFAULT_TOPIC, help="직접 지정할 토론 주제")
    parser.add_argument("--report-agent", default=config.DEFAULT_REPORT_AGENT, help="리포트를 출력할 Agent 이름")
    parser.add_argument("--start", default=config.DEFAULT_START_TIME, help="활동 시작 시간")
    parser.add_argument("--end", default=config.DEFAULT_END_TIME, help="활동 종료 시간")
    parser.add_argument("--places", default=",".join(config.PLACES), help="쉼표로 구분한 공간 목록")
    parser.add_argument("--save-state", default=None, help="시뮬레이션 상태를 JSON 파일로 저장")
    parser.add_argument("--load-state", default=None, help="저장된 JSON 상태에서 이어서 실행")
    parser.add_argument("--save-report", default=None, help="최종 리포트를 텍스트 파일로 저장")
    args = parser.parse_args()

    if args.load_state:
        world = load_world(args.load_state)
    else:
        world = build_world(
            topic=args.topic,
            turns_per_agent=args.turns,
            places=[place.strip() for place in args.places.split(",") if place.strip()],
            active_hours=(parse_time(args.start), parse_time(args.end)),
        )

    world.run(rounds=args.rounds, print_output=True)
    final_report = build_full_report(world, args.report_agent)
    print(final_report)

    if args.save_state:
        save_world(world, args.save_state)
        print(f"\n[저장] 시뮬레이션 상태: {args.save_state}")

    if args.save_report:
        save_report(args.save_report, final_report)
        print(f"[저장] 리포트: {args.save_report}")


if __name__ == "__main__":
    main()
