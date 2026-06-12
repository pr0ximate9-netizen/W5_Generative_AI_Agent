import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import streamlit as st
except ImportError:
    st = None

from config import preset as config
from scripts.agent import analyze_insights, build_world, format_agent_report, load_world, save_world


def main() -> None:
    if st is None:
        print("Streamlit이 설치되어 있지 않습니다. `pip install streamlit` 후 다시 실행하세요.")
        return

    st.set_page_config(page_title="SeatWise", layout="wide")
    st.title("SeatWise")
    st.caption("컴퓨터 실습실 좌석 부족 문제를 토론하는 Multi-Agent 시뮬레이션")

    if "world" not in st.session_state:
        st.session_state.world = build_world()

    world = st.session_state.world
    tab_manual, tab_auto, tab_report, tab_storage = st.tabs(["수동 대화", "자동 시뮬레이션", "리포트", "저장/불러오기"])

    with tab_manual:
        st.subheader("수동 대화")
        speaker = st.selectbox("발화 Agent", [agent.name for agent in world.agents])
        text = st.text_area("발화 내용", height=100)
        if st.button("대화 추가", type="primary") and text.strip():
            world.add_manual_utterance(speaker, text.strip())
            st.success("대화가 추가되었고 memory/reflection이 갱신되었습니다.")
        show_dialogue_log(world)

    with tab_auto:
        st.subheader("자동 시뮬레이션")
        rounds = st.number_input("라운드 수", min_value=1, max_value=10, value=config.DEFAULT_ROUNDS)
        turns = st.number_input("Agent별 발화 수", min_value=1, max_value=5, value=config.DEFAULT_TURNS_PER_AGENT)
        col_run, col_reset = st.columns(2)
        if col_run.button("자동 실행", type="primary"):
            world.turns_per_agent = int(turns)
            world.run(rounds=int(rounds), print_output=False)
            st.success("자동 시뮬레이션이 완료되었습니다.")
        if col_reset.button("초기화"):
            st.session_state.world = build_world()
            st.rerun()
        show_dialogue_log(world)

    with tab_report:
        st.subheader("리포트")
        pov = st.selectbox("리포트 시점", [agent.name for agent in world.agents], key="report_pov")
        st.text_area("Agent 리포트", format_agent_report(world, pov), height=320)
        st.text_area("Insight Analyzer", analyze_insights(world), height=320)

    with tab_storage:
        st.subheader("저장/불러오기")
        default_path = str(Path(tempfile.gettempdir()) / "seatwise_state.json")
        path = st.text_input("JSON 파일 경로", default_path)
        col_save, col_load = st.columns(2)
        if col_save.button("상태 저장"):
            save_world(world, path)
            st.success(f"저장 완료: {path}")
        if col_load.button("상태 불러오기"):
            st.session_state.world = load_world(path)
            st.success(f"불러오기 완료: {path}")
            st.rerun()


def show_dialogue_log(world) -> None:
    st.subheader("대화 로그")
    if not world.dialogue_log:
        st.info("아직 대화가 없습니다.")
        return
    for line in world.dialogue_log:
        st.markdown(f"**Round {line['round']} / {line['speaker']}**: {line['text']}")


if __name__ == "__main__":
    main()
