import json
import random
from dataclasses import asdict, dataclass, field
from datetime import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Agent:
    name: str
    age: int
    job: str
    personality: str
    initial_memory: List[str] = field(default_factory=list)
    memory: Dict[str, List[str]] = field(default_factory=dict)
    relation_map: Dict[str, str] = field(default_factory=dict)
    daily_plan: List[Dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.memory.setdefault("self", list(self.initial_memory))

    def remember(self, other: str, fact: str) -> None:
        facts = self.memory.setdefault(other, [])
        if fact and fact not in facts:
            facts.append(fact)

    def reflect(self, other: str, text: str) -> None:
        if text:
            self.relation_map[other] = text

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Agent":
        return cls(
            name=str(data["name"]),
            age=int(data["age"]),
            job=str(data["job"]),
            personality=str(data["personality"]),
            initial_memory=list(data.get("initial_memory", [])),
            memory=dict(data.get("memory", {})),
            relation_map=dict(data.get("relation_map", {})),
            daily_plan=list(data.get("daily_plan", [])),
        )


class World:
    def __init__(
        self,
        agents: List[Agent],
        project_title: str,
        discussion_context: str,
        places: List[str],
        active_hours: Tuple[time, time],
        round_topics: List[str],
        expected_insights: Dict[str, List[str]],
        scripted_utterances: Dict[str, Dict[str, str]],
        turns_per_agent: int = 1,
        topic: Optional[str] = None,
    ) -> None:
        self.agents = agents
        self.project_title = project_title
        self.discussion_context = discussion_context
        self.places = places
        self.active_hours = active_hours
        self.round_topics = round_topics
        self.expected_insights = expected_insights
        self.scripted_utterances = scripted_utterances
        self.turns_per_agent = turns_per_agent
        self.topic = topic
        self.round_no = 0
        self.dialogue_log: List[Dict[str, str]] = []

    def plan_day(self) -> None:
        for agent in self.agents:
            agent.daily_plan = self._plan(agent)

    def _plan(self, agent: Agent) -> List[Dict[str, str]]:
        p = self.places
        return [
            {"time": "09:00", "place": p[0], "activity": "오늘의 좌석 이용 상황을 확인한다."},
            {"time": "11:00", "place": p[min(1, len(p) - 1)], "activity": f"{agent.job} 관점에서 문제를 정리한다."},
            {"time": "14:00", "place": p[min(2, len(p) - 1)], "activity": "혼잡 시간대와 자리 점유 문제를 공유한다."},
            {"time": "16:00", "place": p[min(3, len(p) - 1)], "activity": "예약제와 자동 취소 방안을 검토한다."},
            {"time": "18:00", "place": p[-1], "activity": "토론 내용을 정리하고 정책 제안을 준비한다."},
        ]

    def run(self, rounds: int = 2, print_output: bool = True) -> List[Dict[str, str]]:
        if print_output:
            print(f"\n===== {self.project_title} =====")

        self.plan_day()
        for _ in range(rounds):
            self.round_no += 1
            topic, lines = self._round()
            if print_output:
                print(f"\n===== Round {self.round_no}: {topic} =====")
                for line in lines:
                    print(f"{line['speaker']}: {line['text']}")
        return self.dialogue_log

    def _round(self) -> Tuple[str, List[Dict[str, str]]]:
        topic = self.topic or self._round_topic() or "자유 토론"
        agents = self.agents[:]
        random.shuffle(agents)

        lines: List[Dict[str, str]] = []
        for i in range(len(agents) * self.turns_per_agent):
            speaker = agents[i % len(agents)]
            text = self._utter(speaker, topic)
            record = {"round": str(self.round_no), "speaker": speaker.name, "text": text}
            self.dialogue_log.append(record)
            lines.append(record)

        self._learn(lines, agents)
        return topic, lines

    def _round_topic(self) -> Optional[str]:
        idx = self.round_no - 1
        if 0 <= idx < len(self.round_topics):
            return self.round_topics[idx]
        return None

    def _utter(self, speaker: Agent, topic: str) -> str:
        scripted = self.scripted_utterances.get(topic, {})
        if speaker.name in scripted:
            return scripted[speaker.name]

        hint = speaker.initial_memory[-1] if speaker.initial_memory else speaker.personality
        return f"{topic}에 대해 제 입장에서는 {hint}"

    def _learn(self, lines: List[Dict[str, str]], agents: List[Agent]) -> None:
        for line in lines:
            fact = f"{_subject(line['speaker'])} '{line['text']}'라고 말했다."
            for agent in agents:
                if agent.name != line["speaker"]:
                    agent.remember(line["speaker"], fact)

        for observer in agents:
            for target in agents:
                if observer.name == target.name:
                    continue
                if observer.memory.get(target.name):
                    observer.reflect(target.name, f"{_subject(target.name)} 자신의 관점에서 문제를 설명하는 사람으로 보인다.")

    def add_manual_utterance(self, speaker_name: str, text: str) -> Dict[str, str]:
        if self.round_no == 0:
            self.round_no = 1
        record = {"round": str(self.round_no), "speaker": speaker_name, "text": text}
        self.dialogue_log.append(record)
        self._learn([record], self.agents)
        return record

    def find_agent(self, name: str) -> Agent:
        for agent in self.agents:
            if agent.name == name:
                return agent
        raise ValueError(f"Agent를 찾을 수 없습니다: {name}")


def build_world(
    topic: Optional[str] = None,
    turns_per_agent: Optional[int] = None,
    places: Optional[List[str]] = None,
    active_hours: Optional[Tuple[time, time]] = None,
) -> World:
    from config import preset as config

    return World(
        agents=config.build_agents(),
        project_title=config.PROJECT_TITLE,
        discussion_context=config.DISCUSSION_CONTEXT,
        places=places or config.PLACES,
        active_hours=active_hours or (parse_time(config.DEFAULT_START_TIME), parse_time(config.DEFAULT_END_TIME)),
        round_topics=config.ROUND_TOPICS,
        expected_insights=config.EXPECTED_INSIGHTS,
        scripted_utterances=config.SCRIPTED_UTTERANCES,
        turns_per_agent=turns_per_agent or config.DEFAULT_TURNS_PER_AGENT,
        topic=topic,
    )


def format_agent_report(world: World, pov_name: str) -> str:
    pov = world.find_agent(pov_name)
    lines = [
        f"\n===== {pov.name} 관점 리포트 =====",
        f"이름: {pov.name} / 나이: {pov.age} / 역할: {pov.job}",
        f"성격: {pov.personality}",
        "",
        "[하루 계획]",
    ]
    lines += [f"  {p['time']} @ {p['place']}: {p['activity']}" for p in pov.daily_plan]

    for other in world.agents:
        if other.name == pov.name:
            continue
        facts = pov.memory.get(other.name, [])
        lines.append(f"\n[{other.name}에 대해 알고 있는 사실]")
        lines += [f"  - {fact}" for fact in facts] or ["  - 아직 기록된 사실이 없습니다."]
        lines += [
            f"[{other.name}에 대한 Reflection]",
            f"  - {pov.relation_map.get(other.name, '아직 판단할 정보가 충분하지 않습니다.')}",
        ]
    return "\n".join(lines)


def analyze_insights(world: World) -> str:
    labels = [
        ("[문제]", "problems", "{}. {}"),
        ("[원인]", "causes", "- {}"),
        ("[해결책]", "solutions", "{}"),
        ("[예상 효과]", "effects", "- {}"),
    ]
    lines = ["\n===== Insight Analyzer =====", world.project_title, ""]
    for title, key, fmt in labels:
        lines.append(title)
        for i, item in enumerate(world.expected_insights.get(key, []), 1):
            lines.append("  " + (fmt.format(i, item) if fmt.count("{}") == 2 else fmt.format(item)))
        lines.append("")
    return "\n".join(lines).rstrip()


def build_full_report(world: World, pov_name: str) -> str:
    return f"{format_agent_report(world, pov_name)}\n{analyze_insights(world)}"


def save_report(path: str, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def save_world(world: World, path: str) -> None:
    keys = [
        "project_title",
        "discussion_context",
        "places",
        "round_topics",
        "expected_insights",
        "scripted_utterances",
        "turns_per_agent",
        "topic",
        "round_no",
        "dialogue_log",
    ]
    data = {
        "world": {key: getattr(world, key) for key in keys},
        "active_hours": [world.active_hours[0].strftime("%H:%M"), world.active_hours[1].strftime("%H:%M")],
        "agents": [agent.to_dict() for agent in world.agents],
    }
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_world(path: str) -> World:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    world_data = data["world"]
    world = World(
        agents=[Agent.from_dict(item) for item in data["agents"]],
        active_hours=(parse_time(data["active_hours"][0]), parse_time(data["active_hours"][1])),
        project_title=world_data["project_title"],
        discussion_context=world_data["discussion_context"],
        places=world_data["places"],
        round_topics=world_data["round_topics"],
        expected_insights=world_data["expected_insights"],
        scripted_utterances=world_data["scripted_utterances"],
        turns_per_agent=world_data["turns_per_agent"],
        topic=world_data.get("topic"),
    )
    world.round_no = world_data.get("round_no", 0)
    world.dialogue_log = world_data.get("dialogue_log", [])
    return world


def parse_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def _subject(name: str) -> str:
    return f"{name}{'은' if _has_batchim(name) else '는'}"


def _has_batchim(text: str) -> bool:
    if not text:
        return False
    code = ord(text[-1]) - ord("가")
    return 0 <= code <= 11171 and code % 28 != 0


def transcript(lines: List[Dict[str, str]]) -> str:
    return "\n".join(f"{line['speaker']}: {line['text']}" for line in lines)
