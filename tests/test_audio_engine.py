import sys
import tempfile
import time
import unittest
import wave
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.runtime.audio_engine import AudioEngine, render_music  # noqa: E402


class FakeAudioBackend:
    def __init__(self, fail_repeat=False):
        self.available = True
        self.fail_repeat = fail_repeat
        self.commands = []
        self.counter = 0

    def send(self, command):
        self.commands.append(command)
        if self.fail_repeat and command.endswith(" repeat"):
            return False
        return True

    def next_alias(self, prefix):
        self.counter += 1
        return f"{prefix}_{self.counter}"


class AudioEngineTests(unittest.TestCase):
    def wav_peak(self, path):
        with wave.open(str(path), "rb") as file:
            frames = file.readframes(file.getnframes())
        values = struct.unpack("<" + "h" * (len(frames) // 2), frames)
        return max(abs(value) for value in values) / 32767

    def test_sfx_file_is_generated_as_mono_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = AudioEngine(Path(tmp), music_volume=0, sfx_volume=0)
            path = engine.ensure_sfx_file("click")

            self.assertTrue(path.exists())
            with wave.open(str(path), "rb") as file:
                self.assertEqual(file.getnchannels(), 1)
                self.assertEqual(file.getframerate(), 16000)
                self.assertGreater(file.getnframes(), 0)
            self.assertGreater(self.wav_peak(path), 0.55)

    def test_music_renderer_writes_complete_wav_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short.wav"
            render_music(
                path,
                {"root": 50, "mode": "major", "bpm": 120, "intensity": 0.25, "beats": 4, "lead": "sine"},
            )

            with wave.open(str(path), "rb") as file:
                self.assertEqual(file.getnchannels(), 1)
                self.assertEqual(file.getsampwidth(), 2)
                self.assertGreater(file.getnframes(), 1000)
            self.assertGreater(self.wav_peak(path), 0.65)

    def test_music_falls_back_when_repeat_play_is_not_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = AudioEngine(Path(tmp), music_volume=0.5, sfx_volume=0)
            engine.backend = FakeAudioBackend(fail_repeat=True)
            engine.music_path("home").parent.mkdir(parents=True, exist_ok=True)
            engine.music_path("home").write_bytes(b"placeholder")
            engine._play_music_now("home")

            self.assertIn("play bonus_guess_music repeat", engine.backend.commands)
            self.assertIn("play bonus_guess_music", engine.backend.commands)
            self.assertEqual(engine._music_track, "home")
            engine.shutdown()

    def test_music_prefers_packaged_mp3_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            asset_path = asset_dir / "plains_of_luminescence_loop.mp3"
            asset_path.write_bytes(b"ID3 placeholder")
            engine = AudioEngine(root / "cache", music_volume=0.5, sfx_volume=0, music_asset_dir=asset_dir)
            engine.backend = FakeAudioBackend()

            self.assertEqual(engine.music_playback_path("home"), asset_path)
            engine._play_music_now("home")

            open_commands = [command for command in engine.backend.commands if command.startswith("open ")]
            self.assertTrue(any("type mpegvideo" in command for command in open_commands))
            engine.shutdown()

    def test_home_music_catalog_tracks_can_use_packaged_wav_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            asset_path = asset_dir / "Loop-Menu.wav"
            asset_path.write_bytes(b"RIFF placeholder")
            engine = AudioEngine(root / "cache", music_volume=0.5, sfx_volume=0, music_asset_dir=asset_dir)
            engine.backend = FakeAudioBackend()

            self.assertEqual(engine.music_playback_path("home_menu_loop"), asset_path)
            engine._play_music_now("home_menu_loop")

            open_commands = [command for command in engine.backend.commands if command.startswith("open ")]
            self.assertTrue(any("type waveaudio" in command for command in open_commands))
            engine.shutdown()

    def test_same_music_asset_is_not_reopened_for_different_track_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "assets"
            asset_dir.mkdir()
            asset_path = asset_dir / "plains_of_luminescence_loop.mp3"
            asset_path.write_bytes(b"ID3 placeholder")
            engine = AudioEngine(root / "cache", music_volume=0.5, sfx_volume=0, music_asset_dir=asset_dir)
            engine.backend = FakeAudioBackend()

            engine._play_music_now("free")
            open_count = sum(1 for command in engine.backend.commands if command.startswith("open "))
            engine._play_music_now("result")
            second_open_count = sum(1 for command in engine.backend.commands if command.startswith("open "))

            self.assertEqual(open_count, 1)
            self.assertEqual(second_open_count, 1)
            self.assertEqual(engine._music_track, "result")
            engine.shutdown()

    def test_sfx_prefers_packaged_assets_and_softens_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_dir = root / "sfx"
            asset_dir.mkdir()
            asset_path = asset_dir / "click.wav"
            asset_path.write_bytes(b"placeholder")
            engine = AudioEngine(root / "cache", music_volume=0, sfx_volume=0.8, sfx_asset_dir=asset_dir)
            engine.backend = FakeAudioBackend()

            self.assertEqual(engine.sfx_playback_path("click"), asset_path)
            engine._play_sfx_now("click")

            self.assertTrue(any(str(asset_path.resolve()) in command for command in engine.backend.commands if command.startswith("open ")))
            self.assertIn("setaudio sfx_1 volume to 368", engine.backend.commands)
            engine.shutdown()

    def test_sfx_missing_file_generation_does_not_block_play_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = AudioEngine(Path(tmp), music_volume=0, sfx_volume=0.5)
            engine.backend = FakeAudioBackend()

            def slow_generate(_kind):
                time.sleep(0.25)
                return engine.sfx_path("click")

            engine.ensure_sfx_file = slow_generate
            started = time.perf_counter()
            engine.play_sfx("click")
            elapsed = time.perf_counter() - started
            engine.shutdown()

            self.assertLess(elapsed, 0.08)


if __name__ == "__main__":
    unittest.main()
