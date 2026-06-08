from ._shared import *
from backend.runtime.audio_engine import AudioEngine


class AudioMixin:
    def init_audio(self):
        self.audio = AudioEngine(
            PROJECT_DIR / "profile" / "audio_cache",
            music_volume=self.player_settings.get("music_volume", 0.55),
            sfx_volume=self.player_settings.get("sfx_volume", 0.75),
            music_asset_dir=ASSETS_DIR / "audio" / "music",
            sfx_asset_dir=ASSETS_DIR / "audio" / "sfx",
        )
        set_button_sound_callback(self.play_button_sound)
        self.audio.prepare_async()

    def apply_audio_settings(self):
        if not getattr(self, "audio", None):
            return
        self.audio.set_volumes(
            self.player_settings.get("music_volume", 0.55),
            self.player_settings.get("sfx_volume", 0.75),
        )

    def play_music(self, track):
        if getattr(self, "audio", None):
            if track == "home":
                track = self.selected_home_music_track()
            self.audio.play_music(track)

    def selected_home_music_track(self):
        try:
            rating = load_record_summary()["rating"]
        except Exception:
            rating = 0.0
        music_id = coerce_home_music_id(
            self.player_settings.get("home_music_id"),
            rating,
            reveal_all=self.admin_reveal_hidden_enabled(),
        )
        return home_music_track(music_id)

    def preview_home_music(self, music_id):
        if getattr(self, "audio", None):
            self.audio.play_music(home_music_track(music_id))

    def play_sfx(self, kind):
        if getattr(self, "audio", None):
            self.audio.play_sfx(self.selected_sfx_kind(kind))

    def selected_sfx_kind(self, kind):
        choices = normalize_sfx_choices(self.player_settings.get("sfx_choices"))
        return choices.get(str(kind or "").strip(), kind)

    def preview_sfx_choice(self, sound_id):
        if getattr(self, "audio", None):
            self.audio.play_sfx(sound_id)

    def play_button_sound(self, text, _accent=None):
        label = str(text or "")
        if any(word in label for word in ("提示", "词库")):
            self.play_sfx("hint")
        elif any(word in label for word in ("揭晓", "删除", "恢复默认", "退出登录")):
            self.play_sfx("warning")
        elif any(word in label for word in ("返回", "取消", "关闭", "退出旁观")):
            self.play_sfx("back")
        elif any(word in label for word in ("确认", "保存", "开始", "登录", "注册", "挑战", "下一步", "再来", "再练", "进入")):
            self.play_sfx("confirm")
        else:
            self.play_sfx("click")

    def rank_music_track(self, rank_id=None):
        try:
            value = int(rank_id if rank_id is not None else self.rank_id)
        except (TypeError, ValueError):
            value = 1
        if value <= 5:
            return "rank_1_5"
        if value <= 10:
            return "rank_6_10"
        if value <= 15:
            return "rank_11_15"
        return "rank_16_20"

    def round_music_track(self):
        if self.rank_mode:
            return self.rank_music_track()
        if self.custom_mode:
            play_kind = self.custom_config.get("play_kind", "")
            if play_kind == "字谜":
                return "crossword"
            if play_kind == "线索":
                return "clue"
            if self.is_custom_timed_enabled():
                return "timed"
            return "free"
        if self.play_mode == "线索":
            return "clue"
        if self.play_mode == "限时":
            return "timed"
        if self.play_mode == "字谜":
            return "crossword"
        return "free"

    def shutdown_audio(self):
        set_button_sound_callback(None)
        if getattr(self, "audio", None):
            self.audio.shutdown()
