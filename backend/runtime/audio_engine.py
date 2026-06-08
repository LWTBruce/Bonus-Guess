from __future__ import annotations

import ctypes
import math
import os
import queue
import struct
import threading
import time
import wave
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


SAMPLE_RATE = 16000
MAX_AMPLITUDE = 32767
AUDIO_CACHE_VERSION = "v2"


MUSIC_ASSET_FILES = {
    "home": "plains_of_luminescence_loop.mp3",
    "menu": "four_loop.mp3",
    "settings": "plains_of_luminescence_loop.mp3",
    "archive": "dumus_0.mp3",
    "free": "plains_of_luminescence_loop.mp3",
    "clue": "four_loop.mp3",
    "timed": "fast_background.mp3",
    "crossword": "tempo.mp3",
    "rank_menu": "dumus_0.mp3",
    "rank_1_5": "fast_background.mp3",
    "rank_6_10": "dumus_0.mp3",
    "rank_11_15": "tempo.mp3",
    "rank_16_20": "boss_battle_loop.mp3",
    "result": "plains_of_luminescence_loop.mp3",
    "home_menu_loop": "Loop-Menu.wav",
    "home_once_upon_time": "once_upon_a_time_loop.mp3",
    "home_pointless_loop": "pointless_loop.mp3",
    "home_background_loop": "background_music_loop.mp3",
}


SFX_ASSET_FILES = {
    "click": "click.wav",
    "confirm": "confirm.wav",
    "back": "back.wav",
    "hint": "hint.wav",
    "warning": "warning.wav",
    "success": "success.wav",
    "fail": "fail.wav",
    "popup": "popup.wav",
}


SFX_ASSET_VOLUME_SCALE = {
    "click": 0.46,
    "confirm": 0.42,
    "back": 0.55,
    "hint": 0.42,
    "warning": 0.50,
    "success": 0.44,
    "fail": 0.72,
    "popup": 0.42,
}


TRACK_SPECS = {
    "home": {"root": 50, "mode": "major", "bpm": 86, "intensity": 0.42, "beats": 32, "lead": "sine"},
    "menu": {"root": 52, "mode": "major", "bpm": 92, "intensity": 0.46, "beats": 32, "lead": "sine"},
    "settings": {"root": 48, "mode": "major", "bpm": 76, "intensity": 0.34, "beats": 24, "lead": "sine"},
    "archive": {"root": 45, "mode": "minor", "bpm": 82, "intensity": 0.38, "beats": 32, "lead": "sine"},
    "free": {"root": 50, "mode": "major", "bpm": 72, "intensity": 0.32, "beats": 24, "lead": "sine"},
    "clue": {"root": 47, "mode": "minor", "bpm": 78, "intensity": 0.45, "beats": 32, "lead": "triangle"},
    "timed": {"root": 45, "mode": "minor", "bpm": 118, "intensity": 0.68, "beats": 32, "lead": "square"},
    "crossword": {"root": 43, "mode": "minor", "bpm": 96, "intensity": 0.58, "beats": 32, "lead": "triangle"},
    "rank_menu": {"root": 43, "mode": "minor", "bpm": 104, "intensity": 0.62, "beats": 32, "lead": "triangle"},
    "rank_1_5": {"root": 43, "mode": "minor", "bpm": 106, "intensity": 0.66, "beats": 32, "lead": "triangle"},
    "rank_6_10": {"root": 42, "mode": "minor", "bpm": 124, "intensity": 0.78, "beats": 32, "lead": "square"},
    "rank_11_15": {"root": 41, "mode": "minor", "bpm": 140, "intensity": 0.92, "beats": 32, "lead": "square"},
    "rank_16_20": {"root": 40, "mode": "minor", "bpm": 156, "intensity": 1.08, "beats": 32, "lead": "square"},
    "result": {"root": 52, "mode": "major", "bpm": 84, "intensity": 0.36, "beats": 24, "lead": "sine"},
    "home_menu_loop": {"root": 52, "mode": "major", "bpm": 96, "intensity": 0.48, "beats": 32, "lead": "triangle"},
    "home_once_upon_time": {"root": 55, "mode": "major", "bpm": 78, "intensity": 0.36, "beats": 32, "lead": "sine"},
    "home_pointless_loop": {"root": 45, "mode": "minor", "bpm": 86, "intensity": 0.40, "beats": 32, "lead": "sine"},
    "home_background_loop": {"root": 47, "mode": "minor", "bpm": 104, "intensity": 0.64, "beats": 32, "lead": "triangle"},
}


SFX_DURATIONS = {
    "click": 0.10,
    "confirm": 0.18,
    "back": 0.15,
    "hint": 0.28,
    "warning": 0.26,
    "success": 0.55,
    "fail": 0.45,
    "popup": 0.16,
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def midi_to_frequency(note: float) -> float:
    return 440.0 * (2.0 ** ((note - 69.0) / 12.0))


def waveform_value(kind: str, phase: float) -> float:
    if kind == "square":
        return 1.0 if math.sin(phase) >= 0 else -1.0
    if kind == "triangle":
        return 2.0 / math.pi * math.asin(math.sin(phase))
    if kind == "saw":
        return 2.0 * ((phase / (2.0 * math.pi)) % 1.0) - 1.0
    return math.sin(phase)


def envelope(position: int, total: int, attack: float = 0.06, release: float = 0.16) -> float:
    if total <= 1:
        return 1.0
    x = position / total
    if x < attack:
        return x / max(attack, 0.001)
    if x > 1.0 - release:
        return max(0.0, (1.0 - x) / max(release, 0.001))
    return 1.0


def add_tone(buffer: List[float], start: float, duration: float, frequency: float, gain: float, kind: str = "sine") -> None:
    start_index = max(0, int(start * SAMPLE_RATE))
    count = max(1, int(duration * SAMPLE_RATE))
    end_index = min(len(buffer), start_index + count)
    phase_step = 2.0 * math.pi * frequency / SAMPLE_RATE
    phase = 0.0
    for index in range(start_index, end_index):
        env = envelope(index - start_index, count)
        buffer[index] += waveform_value(kind, phase) * gain * env
        phase += phase_step


def add_noise(buffer: List[float], start: float, duration: float, gain: float) -> None:
    start_index = max(0, int(start * SAMPLE_RATE))
    count = max(1, int(duration * SAMPLE_RATE))
    end_index = min(len(buffer), start_index + count)
    value = 0.12345
    for index in range(start_index, end_index):
        value = (value * 3.87) % 1.0
        env = envelope(index - start_index, count, attack=0.01, release=0.5)
        buffer[index] += (value * 2.0 - 1.0) * gain * env


def normalize_and_write(path: Path, buffer: List[float], target_peak: float = 0.70) -> None:
    peak = max((abs(sample) for sample in buffer), default=1.0)
    scale = 0.0 if peak <= 0 else target_peak / peak
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    with wave.open(str(temp_path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for sample in buffer:
            value = int(max(-1.0, min(1.0, sample * scale)) * MAX_AMPLITUDE)
            frames.extend(struct.pack("<h", value))
        file.writeframes(bytes(frames))
    temp_path.replace(path)


def scale_for_mode(mode: str) -> List[int]:
    if mode == "major":
        return [0, 2, 4, 7, 9, 12]
    return [0, 3, 5, 7, 10, 12]


def render_music(path: Path, spec: Dict[str, object]) -> None:
    bpm = float(spec["bpm"])
    beats = int(spec["beats"])
    seconds_per_beat = 60.0 / bpm
    duration = beats * seconds_per_beat
    buffer = [0.0] * int(duration * SAMPLE_RATE)
    root = int(spec["root"])
    mode = str(spec["mode"])
    intensity = float(spec["intensity"])
    lead_kind = str(spec["lead"])
    scale = scale_for_mode(mode)
    progression = [0, -3, -5, -2] if mode == "minor" else [0, -5, -3, -4]
    melody_steps = [0, 2, 4, 5, 4, 2, 1, 2, 4, 5, 7, 5, 4, 2, 0, -1]

    for beat in range(beats):
        start = beat * seconds_per_beat
        chord_root = root + progression[(beat // 4) % len(progression)]
        add_tone(buffer, start, seconds_per_beat * 0.92, midi_to_frequency(chord_root - 12), 0.10 * intensity, "sine")
        if beat % 2 == 0:
            add_tone(buffer, start, seconds_per_beat * 1.8, midi_to_frequency(chord_root), 0.035 * intensity, "sine")
            add_tone(buffer, start, seconds_per_beat * 1.8, midi_to_frequency(chord_root + scale[2]), 0.03 * intensity, "sine")
            add_tone(buffer, start, seconds_per_beat * 1.8, midi_to_frequency(chord_root + scale[3]), 0.028 * intensity, "sine")
        if intensity >= 0.62:
            add_noise(buffer, start, seconds_per_beat * 0.18, 0.026 * intensity)
        for sub in (0.0, 0.5):
            arp_note = chord_root + scale[(beat + int(sub * 2)) % len(scale)] + 12
            add_tone(
                buffer,
                start + sub * seconds_per_beat,
                seconds_per_beat * 0.40,
                midi_to_frequency(arp_note),
                0.035 * intensity,
                "triangle",
            )
        if beat % (3 if intensity >= 0.75 else 4) == 0:
            melody = root + 12 + melody_steps[(beat // 2) % len(melody_steps)]
            add_tone(buffer, start, seconds_per_beat * 0.85, midi_to_frequency(melody), 0.045 * intensity, lead_kind)

    normalize_and_write(path, buffer, target_peak=0.72)


def render_sfx(path: Path, kind: str) -> None:
    duration = SFX_DURATIONS.get(kind, 0.12)
    buffer = [0.0] * int(duration * SAMPLE_RATE)
    if kind == "confirm":
        for offset, note in enumerate((72, 76, 79)):
            add_tone(buffer, offset * 0.045, 0.11, midi_to_frequency(note), 0.34, "triangle")
    elif kind == "back":
        for offset, note in enumerate((67, 62, 55)):
            add_tone(buffer, offset * 0.045, 0.12, midi_to_frequency(note), 0.28, "triangle")
    elif kind == "hint":
        for offset, note in enumerate((79, 84, 88, 91)):
            add_tone(buffer, offset * 0.055, 0.16, midi_to_frequency(note), 0.22, "sine")
    elif kind == "warning":
        add_tone(buffer, 0.00, 0.13, midi_to_frequency(58), 0.30, "square")
        add_tone(buffer, 0.13, 0.13, midi_to_frequency(55), 0.28, "square")
    elif kind == "success":
        for offset, note in enumerate((67, 72, 76, 79, 84)):
            add_tone(buffer, offset * 0.075, 0.22, midi_to_frequency(note), 0.25, "triangle")
    elif kind == "fail":
        for offset, note in enumerate((55, 52, 48, 43)):
            add_tone(buffer, offset * 0.09, 0.18, midi_to_frequency(note), 0.24, "sine")
    elif kind == "popup":
        add_tone(buffer, 0.00, 0.12, midi_to_frequency(76), 0.22, "sine")
        add_tone(buffer, 0.04, 0.12, midi_to_frequency(83), 0.18, "sine")
    else:
        add_tone(buffer, 0.00, 0.08, midi_to_frequency(74), 0.27, "triangle")
        add_tone(buffer, 0.035, 0.06, midi_to_frequency(86), 0.18, "sine")
    normalize_and_write(path, buffer, target_peak=0.62)


class MciAudioBackend:
    def __init__(self) -> None:
        self.available = os.name == "nt"
        self._counter = 0
        self._lock = threading.RLock()
        self._mci = None
        if self.available:
            try:
                self._mci = ctypes.windll.winmm.mciSendStringW
            except Exception:
                self.available = False

    def send(self, command: str) -> bool:
        if not self.available or self._mci is None:
            return False
        buffer = ctypes.create_unicode_buffer(256)
        try:
            return self._mci(command, buffer, 255, None) == 0
        except Exception:
            self.available = False
            return False

    def next_alias(self, prefix: str) -> str:
        with self._lock:
            self._counter += 1
            return f"bg_{prefix}_{self._counter}"


class AudioEngine:
    def __init__(
        self,
        cache_dir: Path,
        music_volume: float = 0.55,
        sfx_volume: float = 0.75,
        music_asset_dir: Optional[Path] = None,
        sfx_asset_dir: Optional[Path] = None,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.music_asset_dir = Path(music_asset_dir) if music_asset_dir else None
        self.sfx_asset_dir = Path(sfx_asset_dir) if sfx_asset_dir else None
        self.music_volume = clamp(music_volume)
        self.sfx_volume = clamp(sfx_volume)
        self.backend = MciAudioBackend()
        self._lock = threading.RLock()
        self._music_alias = "bonus_guess_music"
        self._music_track: Optional[str] = None
        self._music_source: Optional[str] = None
        self._desired_track: Optional[str] = None
        self._building: set[str] = set()
        self._sfx_building: set[str] = set()
        self._closed = False
        self._queue: queue.Queue[Tuple[str, str]] = queue.Queue()
        self._music_loop_timer: Optional[threading.Timer] = None
        self._worker = threading.Thread(target=self._audio_worker, daemon=True)
        self._worker.start()

    def prepare_async(self) -> None:
        threading.Thread(target=self.ensure_core_assets, daemon=True).start()

    def ensure_core_assets(self) -> None:
        for kind in ("click", "confirm", "back", "hint", "warning", "success", "fail", "popup"):
            if not self.sfx_asset_path(kind):
                self.ensure_sfx_file(kind)

    def music_path(self, track: str) -> Path:
        return self.cache_dir / AUDIO_CACHE_VERSION / "music" / f"{track}.wav"

    def music_asset_path(self, track: str) -> Optional[Path]:
        if not self.music_asset_dir:
            return None
        filename = MUSIC_ASSET_FILES.get(track)
        if not filename:
            return None
        path = self.music_asset_dir / filename
        return path if path.exists() else None

    def music_playback_path(self, track: str) -> Path:
        return self.music_asset_path(track) or self.music_path(track)

    def sfx_path(self, kind: str) -> Path:
        return self.cache_dir / AUDIO_CACHE_VERSION / "sfx" / f"{kind}.wav"

    def sfx_asset_path(self, kind: str) -> Optional[Path]:
        if not self.sfx_asset_dir:
            return None
        filename = SFX_ASSET_FILES.get(kind)
        if not filename:
            return None
        path = self.sfx_asset_dir / filename
        return path if path.exists() else None

    def sfx_playback_path(self, kind: str) -> Path:
        return self.sfx_asset_path(kind) or self.sfx_path(kind)

    def ensure_music_file(self, track: str) -> Optional[Path]:
        spec = TRACK_SPECS.get(track)
        if not spec:
            return None
        path = self.music_path(track)
        if not path.exists():
            render_music(path, spec)
        return path

    def ensure_sfx_file(self, kind: str) -> Optional[Path]:
        if kind not in SFX_DURATIONS:
            kind = "click"
        path = self.sfx_path(kind)
        if not path.exists():
            render_sfx(path, kind)
        return path

    def set_volumes(self, music_volume: float, sfx_volume: float) -> None:
        self.music_volume = clamp(music_volume)
        self.sfx_volume = clamp(sfx_volume)
        if self.music_volume <= 0:
            self.stop_music(close_alias=True)
        elif self._music_track:
            self._enqueue("volume", "")
        elif self._desired_track:
            self.play_music(self._desired_track)

    @staticmethod
    def mci_volume(volume: float) -> int:
        return int(round(clamp(volume) * 1000))

    def play_music(self, track: str) -> None:
        if self._closed:
            return
        if track not in TRACK_SPECS:
            track = "menu"
        self._desired_track = track
        if self.music_volume <= 0 or not self.backend.available:
            return
        path = self.music_playback_path(track)
        if not path.exists():
            self._build_music_async(track)
            return
        self._enqueue("music", track)

    def _build_music_async(self, track: str) -> None:
        with self._lock:
            if track in self._building:
                return
            self._building.add(track)

        def build() -> None:
            try:
                self.ensure_music_file(track)
            finally:
                with self._lock:
                    self._building.discard(track)
            if self._desired_track == track and not self._closed:
                self.play_music(track)

        threading.Thread(target=build, daemon=True).start()

    def play_sfx(self, kind: str) -> None:
        if self._closed or self.sfx_volume <= 0 or not self.backend.available:
            return
        if kind not in SFX_DURATIONS:
            kind = "click"
        path = self.sfx_playback_path(kind)
        if not path.exists():
            self._build_sfx_async(kind)
            return
        self._enqueue("sfx", kind)

    def _enqueue(self, action: str, value: str) -> None:
        if self._closed and action not in {"stop", "shutdown"}:
            return
        try:
            self._queue.put_nowait((action, value))
        except queue.Full:
            pass

    def _audio_worker(self) -> None:
        while True:
            try:
                action, value = self._queue.get()
            except Exception:
                continue
            if action == "shutdown":
                return
            if self._closed and action != "stop":
                continue
            try:
                if action == "music":
                    self._play_music_now(value)
                elif action == "volume":
                    self._set_music_volume_now()
                elif action == "sfx":
                    self._play_sfx_now(value)
                elif action == "music_loop":
                    self._loop_music_now(value)
                elif action == "stop":
                    self._stop_music_now(close_alias=value == "close")
            except Exception:
                pass

    def _play_music_now(self, track: str) -> None:
        if self._closed or self.music_volume <= 0 or not self.backend.available:
            return
        path = self.music_playback_path(track)
        if not path.exists():
            return
        source = self.canonical_audio_path(path)
        with self._lock:
            if self._music_track == track or (self._music_source and self._music_source == source):
                self._music_track = track
                self._set_music_volume_now()
                if self._music_loop_timer:
                    self._schedule_music_loop(track)
                return
            self._cancel_music_loop_timer()
            self.backend.send(f"stop {self._music_alias}")
            self.backend.send(f"close {self._music_alias}")
            quoted = str(path.resolve()).replace('"', "")
            open_type = self.mci_file_type(path)
            if not self.backend.send(f'open "{quoted}" type {open_type} alias {self._music_alias}'):
                self._music_track = None
                return
            self.backend.send(f"setaudio {self._music_alias} volume to {self.mci_volume(self.music_volume)}")
            if self.backend.send(f"play {self._music_alias} repeat"):
                self._music_track = track
                self._music_source = source
            elif self.backend.send(f"play {self._music_alias}"):
                self._music_track = track
                self._music_source = source
                self._schedule_music_loop(track)
            else:
                self.backend.send(f"close {self._music_alias}")
                self._music_track = None
                self._music_source = None

    def _set_music_volume_now(self) -> None:
        if self._music_track:
            self.backend.send(f"setaudio {self._music_alias} volume to {self.mci_volume(self.music_volume)}")

    def _track_duration(self, track: str) -> float:
        path = self.music_asset_path(track)
        if path and path.suffix.lower() == ".wav":
            try:
                with wave.open(str(path), "rb") as file:
                    frames = file.getnframes()
                    rate = file.getframerate() or SAMPLE_RATE
                    return frames / rate
            except Exception:
                pass
        spec = TRACK_SPECS.get(track, {})
        try:
            return int(spec.get("beats", 24)) * 60.0 / float(spec.get("bpm", 90))
        except (TypeError, ValueError, ZeroDivisionError):
            return 16.0

    def _schedule_music_loop(self, track: str) -> None:
        self._cancel_music_loop_timer()
        delay = max(1.0, self._track_duration(track) - 0.10)

        def restart() -> None:
            self._enqueue("music_loop", track)

        timer = threading.Timer(delay, restart)
        timer.daemon = True
        self._music_loop_timer = timer
        timer.start()

    def _cancel_music_loop_timer(self) -> None:
        timer = self._music_loop_timer
        self._music_loop_timer = None
        if timer:
            try:
                timer.cancel()
            except Exception:
                pass

    def _loop_music_now(self, track: str) -> None:
        if self._closed or self.music_volume <= 0 or self._music_track != track or self._desired_track != track:
            return
        self.backend.send(f"seek {self._music_alias} to start")
        if self.backend.send(f"play {self._music_alias}"):
            self._schedule_music_loop(track)

    def _build_sfx_async(self, kind: str) -> None:
        with self._lock:
            if kind in self._sfx_building:
                return
            self._sfx_building.add(kind)

        def build() -> None:
            try:
                path = self.ensure_sfx_file(kind)
            except Exception:
                return
            finally:
                with self._lock:
                    self._sfx_building.discard(kind)
            if path and not self._closed and self.sfx_volume > 0:
                self._enqueue("sfx", kind)

        threading.Thread(target=build, daemon=True).start()

    def _play_sfx_now(self, kind: str) -> None:
        if self._closed or self.sfx_volume <= 0 or not self.backend.available:
            return
        path = self.sfx_playback_path(kind)
        if not path.exists():
            return
        alias = self.backend.next_alias("sfx")
        quoted = str(path.resolve()).replace('"', "")
        if not self.backend.send(f'open "{quoted}" type {self.mci_file_type(path)} alias {alias}'):
            return
        volume = self.sfx_volume
        if self.sfx_asset_path(kind):
            volume *= SFX_ASSET_VOLUME_SCALE.get(kind, 0.5)
        self.backend.send(f"setaudio {alias} volume to {self.mci_volume(volume)}")
        self.backend.send(f"play {alias}")

        def close_alias() -> None:
            self.backend.send(f"close {alias}")

        timer = threading.Timer(self._sfx_duration(kind, path) + 0.35, close_alias)
        timer.daemon = True
        timer.start()

    def _sfx_duration(self, kind: str, path: Path) -> float:
        if path.suffix.lower() == ".wav":
            try:
                with wave.open(str(path), "rb") as file:
                    frames = file.getnframes()
                    rate = file.getframerate() or SAMPLE_RATE
                    return frames / rate
            except Exception:
                pass
        return SFX_DURATIONS.get(kind, 0.12)

    @staticmethod
    def mci_file_type(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".mp3":
            return "mpegvideo"
        return "waveaudio"

    @staticmethod
    def canonical_audio_path(path: Path) -> str:
        try:
            return str(path.resolve()).casefold()
        except OSError:
            return str(path.absolute()).casefold()

    def stop_music(self, close_alias: bool = False) -> None:
        self._enqueue("stop", "close" if close_alias else "")

    def _stop_music_now(self, close_alias: bool = False) -> None:
        self._cancel_music_loop_timer()
        self.backend.send(f"stop {self._music_alias}")
        if close_alias:
            self.backend.send(f"close {self._music_alias}")
            self._music_track = None
            self._music_source = None

    def shutdown(self) -> None:
        self._closed = True
        self._enqueue("stop", "close")
        self._enqueue("shutdown", "")
