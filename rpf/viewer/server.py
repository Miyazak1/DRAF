from __future__ import annotations

import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from rpf.scenarios.loader import load_scenario


STATIC_DIR = Path(__file__).with_name("static")
ZH = {
    "material_urgency": "物质紧迫",
    "unacknowledged_help": "未被承认的帮助",
    "practical_repair": "实际补偿",
    "public_politeness": "公开礼貌",
    "delayed_reply": "延迟回应",
    "short_answer": "短促回答",
    "gaze_avoidance": "回避目光",
    "refused": "被拒绝",
    "misunderstood": "被误解",
    "postponed": "被推迟",
    "displaced": "被转移",
    "unspeakable": "变得不可说",
    "granted": "承认成功",
    "partial": "部分承认",
    "fragile": "脆弱",
    "locked-in": "锁定",
    "cold-war": "冷战",
    "repair-avoidant": "回避修复",
    "cls-debt-named": "债务命名",
    "irr-symbolic-debt-lock": "象征债务锁定",
}


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _read_timeline(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def build_viewer_payload(output_dir: Path) -> dict[str, Any]:
    run_dir = output_dir.resolve()
    metrics = _read_json(run_dir / "metrics.json", {})
    timeline = _read_timeline(run_dir / "timeline.jsonl")
    manifest = _read_json(run_dir / "timeline_manifest.json", {})
    payload = {
        "run_dir": str(run_dir),
        "manifest": manifest,
        "render_canon": _read_render_canon(run_dir, manifest),
        "derived_views": _read_json(run_dir / "derived_views.json", {}),
        "metrics": metrics,
        "scheduler": _read_json(run_dir / "scheduler_diagnostics.json", []),
        "projection": _read_json(run_dir / "projection_trace.json", []),
        "affordance": _read_json(run_dir / "affordance_trace.json", []),
        "action": _read_json(run_dir / "action_trace.json", []),
        "expression": _read_json(run_dir / "expression_trace.json", []),
        "recognition": _read_json(run_dir / "recognition_trace.json", []),
        "fate": _read_json(run_dir / "fate_transition_trace.json", []),
        "memory": _read_json(run_dir / "memory_trace.json", []),
        "rpp_activation": _read_json(run_dir / "rpp_activation_trace.json", []),
        "rpp_dynamics": _read_json(run_dir / "rpp_dynamics_trace.json", []),
        "irreversibility": _read_json(run_dir / "irreversibility_report.json", {}),
        "timeline": timeline,
    }
    payload["story"] = build_story_frames(payload)
    payload["summary"] = {
        "event_count": metrics.get("event_count", len(timeline)),
        "phase": payload["derived_views"].get("relationship_view", {}).get("phase_label", "unknown"),
        "trust": payload["derived_views"].get("trust_view", {}),
        "resentment": payload["derived_views"].get("resentment_pressure_view", {}),
        "repair": payload["derived_views"].get("repair_capacity_view", {}),
        "top_events": _top_counts(metrics.get("event_type_counts", {}), 8),
        "top_rpps": _top_counts(metrics.get("rpp_activation_score_sums", {}), 5),
        "top_compositions": _top_counts(metrics.get("rpp_composition_score_sums", {}), 5),
    }
    return payload


def build_story_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cast = payload.get("render_canon", {}).get("cast", {})
    scheduler = payload.get("scheduler", [])
    projection_by_tick = {item.get("tick"): item for item in payload.get("projection", [])}
    action_by_tick = {item.get("tick"): item.get("selected_action", {}) for item in payload.get("action", [])}
    expression_by_tick = {item.get("tick"): item.get("selected_expression", {}) for item in payload.get("expression", [])}
    recognition_by_tick = {item.get("tick"): item for item in payload.get("recognition", [])}
    memories_by_tick: dict[int, list[dict[str, Any]]] = {}
    for memory in payload.get("memory", []):
        memories_by_tick.setdefault(int(memory.get("tick", 0)), []).append(memory)
    fate_by_tick: dict[int, list[dict[str, Any]]] = {}
    for fate in payload.get("fate", []):
        fate_by_tick.setdefault(int(fate.get("tick", 0)), []).append(fate)
    previous_phase = None
    frames: list[dict[str, Any]] = []
    for tick in scheduler:
        tick_index = int(tick.get("tick_index", 0))
        tick_type = str(tick.get("selected_tick_type", "unknown"))
        projection = projection_by_tick.get(tick_index, {})
        action = action_by_tick.get(tick_index, {})
        expression = expression_by_tick.get(tick_index, {})
        recognition = recognition_by_tick.get(tick_index)
        memories = memories_by_tick.get(tick_index, [])
        fates = fate_by_tick.get(tick_index, [])
        phase = projection.get("relationship_phase") or previous_phase or "unknown"
        phase_changed = previous_phase is not None and phase != previous_phase
        previous_phase = phase
        summary_parts = [_tick_sentence(tick_type, tick)]
        if action:
            summary_parts.append(_action_sentence(action))
        if expression:
            summary_parts.append(_expression_sentence(expression))
        if recognition:
            summary_parts.append(_recognition_sentence(recognition))
        if fates:
            summary_parts.append(_fate_sentence(fates))
        if memories:
            summary_parts.append(_memory_sentence(memories))
        frames.append(
            {
                "tick": tick_index,
                "tick_type": tick_type,
                "phase": phase,
                "phase_changed": phase_changed,
                "summary": " ".join(part for part in summary_parts if part),
                "participants": _participants(action, cast),
                "action": action,
                "expression": expression,
                "recognition": recognition or {},
                "memory_count": len(memories),
                "fate_count": len(fates),
                "pressure": tick.get("input_factors", {}),
                "time_reason": tick.get("time_mapping_reason", ""),
                "simulated_time_delta_seconds": tick.get("simulated_time_delta_seconds", 0),
            }
        )
    return frames


def _tick_sentence(tick_type: str, tick: dict[str, Any]) -> str:
    if tick_type == "latent":
        return "这一段没有直接交锋，压力在关系里继续累积。"
    if tick_type == "micro_interaction":
        return "一次短暂接触变得有意义。"
    if tick_type == "scene":
        return "压力结晶成一个可见场景。"
    return str(tick.get("time_mapping_reason", ""))


def _action_sentence(action: dict[str, Any]) -> str:
    mode = action.get("action_mode")
    signal = _zh(action.get("signal_type", "unknown"))
    if mode == "inhibited":
        return f"原本可能发生的行动被压住，只剩下 {signal}。"
    if mode == "substituted":
        return f"直接行动没有出现，关系改用 {signal} 作为替代。"
    if mode == "escalated":
        return f"行动升级为更明确的 {signal}。"
    return f"关系通过 {signal} 直接显现。"


def _expression_sentence(expression: dict[str, Any]) -> str:
    mode = expression.get("expression_mode")
    signal = _zh(expression.get("surface_signal", "unknown"))
    if mode == "silence":
        return f"这个行动最终表现为沉默或延迟，表层信号是 {signal}。"
    if mode == "public_performance":
        return f"它被包装成公开可接受的表现：{signal}。"
    if mode == "gesture":
        return f"它没有完全说出口，而是通过姿态显现：{signal}。"
    if mode == "timing_distortion":
        return f"它通过停顿和时机变形显现：{signal}。"
    if mode == "tonal_shift":
        return f"它通过语气变化显现：{signal}。"
    return f"它以相对直接的表达出现：{signal}。"


def _recognition_sentence(recognition: dict[str, Any]) -> str:
    outcome = recognition.get("outcome", "unknown")
    if outcome == "refused":
        return "承认请求被拒绝，修复债继续上升。"
    if outcome == "misunderstood":
        return "对方回应了错误层面，承认请求被误解。"
    if outcome == "postponed":
        return "承认被推迟，问题没有真正进入修复。"
    if outcome == "displaced":
        return "承认被转移成别的形式。"
    if outcome == "unspeakable":
        return "承认变得不可说。"
    if outcome == "partial":
        return "出现了部分承认，但仍有残余。"
    if outcome == "granted":
        return "承认被给出，修复暂时变得可能。"
    return ""


def _fate_sentence(fates: list[dict[str, Any]]) -> str:
    labels = "，".join(_zh(item.get("transition_id", "")) for item in fates)
    return f"关系跨过命运阈值：{labels}。"


def _memory_sentence(memories: list[dict[str, Any]]) -> str:
    owners = sorted({str(item.get("owner_process_id", "")) for item in memories if item.get("owner_process_id")})
    return f"这一步被重构进记忆，影响到 {'、'.join(owners)}。"


def _zh(value: Any) -> str:
    text = str(value)
    return ZH.get(text, text)


def _participants(action: dict[str, Any], cast: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for role, key in (("source", "source_process"), ("target", "target_process")):
        pid = action.get(key)
        if pid:
            result[role] = _participant(pid, cast)
    return result


def _participant(pid: str, cast: dict[str, Any]) -> dict[str, Any]:
    if pid in cast:
        return {
            "process_id": pid,
            "name": cast[pid].get("name", pid),
            "pronoun": cast[pid].get("pronoun", ""),
        }
    if pid == "field":
        return {"process_id": pid, "name": "场域", "pronoun": ""}
    pieces = [piece for piece in pid.replace(",", "-").split("-") if piece]
    if len(pieces) > 1 and all(piece in cast for piece in pieces):
        return {
            "process_id": pid,
            "name": "、".join(cast[piece].get("name", piece) for piece in pieces),
            "pronoun": "",
        }
    return {"process_id": pid, "name": pid, "pronoun": ""}


def _read_render_canon(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    direct = _read_json(run_dir / "render_canon.json", None)
    if isinstance(direct, dict):
        return direct
    scenario_path = manifest.get("scenario_path")
    if not scenario_path:
        return {}
    try:
        scenario = load_scenario(Path(scenario_path))
    except Exception:
        return {}
    canon = scenario.get("render_canon", {})
    return canon if isinstance(canon, dict) else {}


def _top_counts(mapping: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    items = sorted(mapping.items(), key=lambda item: float(item[1]), reverse=True)
    return [{"key": key, "value": value} for key, value in items[:limit]]


class ViewerServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], output_dir: Path) -> None:
        self.output_dir = output_dir.resolve()
        self.session_lock = threading.Lock()
        self.session_stop = threading.Event()
        self.session_thread: threading.Thread | None = None
        self.session_status: dict[str, Any] = {
            "state": "idle",
            "message": "尚未开始持续模拟",
        }
        super().__init__(server_address, ViewerHandler)


class ViewerHandler(BaseHTTPRequestHandler):
    server: ViewerServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/run":
            self._send_json(build_viewer_payload(self.server.output_dir))
            return
        if parsed.path == "/api/simulate/status":
            self._send_json(self._session_status())
            return
        path = "index.html" if parsed.path in {"/", ""} else parsed.path.lstrip("/")
        target = (STATIC_DIR / path).resolve()
        try:
            target.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self.send_error(404)
            return
        if not target.exists() or not target.is_file():
            self.send_error(404)
            return
        self._send_file(target)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/render":
            self._handle_render()
            return
        if parsed.path == "/api/simulate/start":
            self._handle_simulate_start()
            return
        if parsed.path == "/api/simulate/stop":
            self.server.session_stop.set()
            with self.server.session_lock:
                if self.server.session_status.get("state") == "running":
                    self.server.session_status["state"] = "stopping"
                    self.server.session_status["message"] = "正在停止..."
            self._send_json(self._session_status())
            return
        self.send_error(404)

    def _handle_render(self) -> None:
        try:
            request = self._read_json_body()
            from rpf.llm.renderer import render_output

            result = render_output(
                self.server.output_dir,
                use_llm=bool(request.get("use_llm", True)),
                provider=request.get("provider") or None,
                model=request.get("model") or None,
                base_url=request.get("base_url") or None,
                api_key=request.get("api_key") or None,
                thinking=request.get("thinking") or None,
                reasoning_effort=request.get("reasoning_effort") or None,
                max_frames=_positive_int(request.get("max_frames")),
            )
            output_path = Path(result["output"])
            self._send_json({
                **result,
                "text": output_path.read_text(encoding="utf-8") if output_path.exists() else "",
            })
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _handle_simulate_start(self) -> None:
        try:
            request = self._read_json_body()
            with self.server.session_lock:
                running = self.server.session_thread and self.server.session_thread.is_alive()
                if running:
                    self._send_json({"error": "已有持续模拟正在运行"}, status=409)
                    return
                self.server.session_stop.clear()
                self.server.session_status = _initial_session_status(request, self.server.output_dir)
            thread = threading.Thread(
                target=_run_session,
                args=(self.server, request),
                daemon=True,
            )
            self.server.session_thread = thread
            thread.start()
            self._send_json(self._session_status())
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _session_status(self) -> dict[str, Any]:
        with self.server.session_lock:
            return dict(self.server.session_status)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        data = self.rfile.read(length).decode("utf-8")
        parsed = json.loads(data)
        if not isinstance(parsed, dict):
            raise ValueError("Request body must be a JSON object")
        return parsed

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path) -> None:
        data = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve_viewer(output_dir: Path, host: str, port: int) -> str:
    if not output_dir.exists():
        raise FileNotFoundError(f"Run output directory does not exist: {output_dir}")
    server = ViewerServer((host, port), output_dir)
    url = f"http://{host}:{server.server_port}"
    print(f"RPF viewer: {url}")
    print(f"Run output: {output_dir.resolve()}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return url


def _positive_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    parsed = int(value)
    return parsed if parsed > 0 else None


def _initial_session_status(request: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    target_seconds = _duration_seconds(request)
    return {
        "state": "running",
        "message": "真实时间持续模拟已启动",
        "output_dir": str(output_dir),
        "target_seconds": target_seconds,
        "elapsed_seconds": 0,
        "tick": 0,
        "render_mode": request.get("render_mode", "deterministic"),
        "last_render_output": None,
        "last_render_error": None,
    }


def _run_session(server: ViewerServer, request: dict[str, Any]) -> None:
    from rpf.engine.simulator import Simulator
    from rpf.llm.segments import next_render_segment, render_and_append_segment

    try:
        scenario_path = _scenario_path_for_output(server.output_dir)
        scenario = load_scenario(scenario_path)
        seed = int(request.get("seed") or _manifest_seed(server.output_dir) or 42)
        target_seconds = _duration_seconds(request)
        tick_interval_seconds = float(request.get("tick_interval_seconds") or 30)
        write_interval = int(request.get("write_interval_ticks") or 1)
        max_steps = int(request.get("max_steps") or 10000)
        render_mode = str(request.get("render_mode") or "deterministic")
        segment_policy = {
            "micro_count": int(request.get("segment_micro_count") or 3),
            "latent_seconds": int(float(request.get("segment_latent_hours") or 6) * 60 * 60),
            "max_ticks": int(request.get("segment_max_ticks") or request.get("render_every_ticks") or 8),
            "max_seconds": int(float(request.get("segment_max_days") or 1) * 24 * 60 * 60),
        }

        sim = Simulator.from_scenario(scenario, scenario_path, seed=seed)

        def on_update(update: dict[str, Any]) -> None:
            with server.session_lock:
                server.session_status.update(
                    {
                        "state": "running",
                        "message": "持续模拟中",
                        "elapsed_seconds": update.get("elapsed_seconds", server.session_status.get("elapsed_seconds", 0)),
                        "target_seconds": update.get("target_seconds", target_seconds),
                        "tick": update.get("tick", server.session_status.get("tick", 0)),
                        "event_count": update.get("metrics", {}).get("event_count"),
                        "render_policy": segment_policy,
                    }
                )
            if render_mode == "none":
                return
            try:
                segment = next_render_segment(
                    server.output_dir,
                    policy=segment_policy,
                    force=bool(update.get("completed")),
                )
                if not segment:
                    return
                result = render_and_append_segment(
                    server.output_dir,
                    segment,
                    use_llm=render_mode == "llm",
                    provider="deepseek" if render_mode == "llm" else None,
                    model=request.get("model") or None,
                    api_key=request.get("api_key") or None,
                    thinking=request.get("thinking") or None,
                    reasoning_effort=request.get("reasoning_effort") or None,
                )
                with server.session_lock:
                    server.session_status["last_render_output"] = result.get("output")
                    server.session_status["last_render_text"] = result.get("text", "")
                    server.session_status["last_render_segment"] = {
                        "segment_id": result.get("segment_id"),
                        "tick_start": result.get("tick_start"),
                        "tick_end": result.get("tick_end"),
                        "boundary_reason": result.get("boundary_reason"),
                        "segment_count": result.get("segment_count"),
                    }
                    server.session_status["last_render_error"] = None
            except Exception as exc:
                with server.session_lock:
                    server.session_status["last_render_error"] = str(exc)

        result = sim.run_for_wall_clock(
            duration_seconds=target_seconds,
            output_dir=server.output_dir,
            tick_interval_seconds=tick_interval_seconds,
            max_steps=max_steps,
            write_interval_ticks=write_interval,
            on_update=on_update,
            should_stop=server.session_stop.is_set,
        )
        with server.session_lock:
            stopped = server.session_stop.is_set()
            server.session_status.update(
                {
                    "state": "stopped" if stopped else "completed",
                    "message": "已停止" if stopped else "持续模拟已完成",
                    "elapsed_seconds": result.get("elapsed_seconds"),
                    "target_seconds": result.get("target_seconds"),
                    "tick": result.get("tick"),
                    "event_count": result.get("metrics", {}).get("event_count"),
                    "final_state_hash": result.get("final_state_hash"),
                }
            )
    except Exception as exc:
        with server.session_lock:
            server.session_status.update({"state": "error", "message": str(exc)})


def _duration_seconds(request: dict[str, Any]) -> int:
    value = float(request.get("duration_value") or 1)
    unit = str(request.get("duration_unit") or "hours")
    multipliers = {
        "minutes": 60,
        "hours": 60 * 60,
        "days": 24 * 60 * 60,
    }
    if unit not in multipliers:
        raise ValueError(f"Unsupported duration unit: {unit}")
    seconds = int(value * multipliers[unit])
    if seconds <= 0:
        raise ValueError("Duration must be positive")
    return seconds


def _scenario_path_for_output(output_dir: Path) -> Path:
    manifest = _read_json(output_dir / "timeline_manifest.json", {})
    scenario_path = manifest.get("scenario_path")
    if not scenario_path:
        raise ValueError("Cannot find scenario_path in timeline_manifest.json")
    return Path(scenario_path)


def _manifest_seed(output_dir: Path) -> int | None:
    manifest = _read_json(output_dir / "timeline_manifest.json", {})
    seed = manifest.get("seed")
    return int(seed) if seed is not None else None
