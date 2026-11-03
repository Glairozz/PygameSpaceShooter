"""Tiny procedural sound engine for Dragon Roaster.

No audio assets are required: every sound effect is synthesised once at start-up
and stored in memory.  If the mixer cannot be initialised (headless CI, no audio
device, ...) the game silently continues without sound.
"""
from __future__ import annotations

import math
import random
from array import array

import pygame

SAMPLE_RATE = 22050


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class SoundManager:
    """Generates and plays short retro-style sound effects."""

    def __init__(self, settings: dict) -> None:
        self.settings = settings
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.sample_rate = SAMPLE_RATE
        self.channels = 2
        self.typecode = "h"
        self.peak = 32767
        self.offset = 0

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=SAMPLE_RATE,
                    size=-16,
                    channels=2,
                    buffer=512,
                )
            info = pygame.mixer.get_init()
            if info is None:
                return

            frequency, sample_format, channels = info
            if sample_format not in (-16, 16):
                # Re-initialise with a format we know how to synthesise.
                pygame.mixer.quit()
                pygame.mixer.init(
                    frequency=SAMPLE_RATE,
                    size=-16,
                    channels=2,
                    buffer=512,
                )
                info = pygame.mixer.get_init()
                if info is None:
                    return
                frequency, sample_format, channels = info

            self.sample_rate = int(frequency)
            self.channels = int(channels)
            if sample_format == -16:
                self.typecode = "h"
                self.peak = 32767
                self.offset = 0
            else:  # unsigned 16-bit
                self.typecode = "H"
                self.peak = 32767
                self.offset = 32768

            self._build_sounds()
            self.enabled = True
        except (pygame.error, OSError, ValueError):
            self.enabled = False
            self.sounds.clear()

    # -- synthesis ----------------------------------------------------------
    def _render(self, duration, generator, gain=1.0):
        frames = max(1, int(self.sample_rate * duration))
        samples = array(self.typecode)
        peak = self.peak
        offset = self.offset
        for index in range(frames):
            progress = index / frames
            time_value = index / self.sample_rate
            value = _clamp(generator(time_value, progress) * gain, -1.0, 1.0)
            sample = int(value * peak) + offset
            for _ in range(self.channels):
                samples.append(sample)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _build_sounds(self) -> None:
        rng = random.Random(1337)

        def sweep(start, end, shape="sine"):
            def generator(time_value, progress):
                frequency = start + (end - start) * progress
                phase = 2.0 * math.pi * frequency * time_value
                if shape == "square":
                    wave = 1.0 if math.sin(phase) >= 0 else -1.0
                elif shape == "saw":
                    wave = 2.0 * ((frequency * time_value) % 1.0) - 1.0
                else:
                    wave = math.sin(phase)
                envelope = (1.0 - progress) ** 2
                return wave * envelope

            return generator

        def noise_burst(decay=2.0):
            def generator(_time_value, progress):
                return (rng.random() * 2.0 - 1.0) * ((1.0 - progress) ** decay)

            return generator

        def arpeggio(notes, length=0.045):
            def generator(_time_value, progress):
                index = min(len(notes) - 1, int(progress * len(notes)))
                note_progress = (progress * len(notes)) % 1.0
                frequency = notes[index]
                wave = math.sin(2.0 * math.pi * frequency * _time_value)
                envelope = (1.0 - note_progress) * (1.0 - progress * 0.4)
                return wave * envelope

            return generator

        def explosion_generator(time_value, progress):
            rumble = math.sin(2.0 * math.pi * (150 - 110 * progress) * time_value)
            crackle = (rng.random() * 2.0 - 1.0) * 0.7
            envelope = (1.0 - progress) ** 1.6
            return (rumble * 0.55 + crackle * 0.45) * envelope

        def wave_generator(time_value, progress):
            frequency = 660 if progress < 0.5 else 990
            envelope = 1.0 - (progress * 2.0) % 1.0
            return math.sin(2.0 * math.pi * frequency * time_value) * envelope

        self.sounds["shoot"] = self._render(
            0.09, sweep(1200, 420, "square"), gain=0.20
        )
        self.sounds["enemy_shoot"] = self._render(
            0.11, sweep(520, 210, "saw"), gain=0.16
        )
        self.sounds["hit"] = self._render(0.07, noise_burst(3.0), gain=0.22)
        self.sounds["explosion"] = self._render(
            0.32, explosion_generator, gain=0.55
        )
        self.sounds["boss_death"] = self._render(
            0.75, explosion_generator, gain=0.75
        )
        self.sounds["powerup"] = self._render(
            0.28, arpeggio([523, 659, 784, 1046]), gain=0.32
        )
        self.sounds["achievement"] = self._render(
            0.42, arpeggio([784, 988, 1175, 1568, 1976]), gain=0.34
        )
        self.sounds["wave"] = self._render(0.36, wave_generator, gain=0.28)
        self.sounds["player_death"] = self._render(
            0.65, sweep(600, 65, "saw"), gain=0.45
        )
        self.sounds["game_over"] = self._render(
            0.9, sweep(330, 55, "sine"), gain=0.42
        )
        self.sounds["victory"] = self._render(
            0.75, arpeggio([523, 659, 784, 1046, 1318]), gain=0.36
        )
        self.sounds["click"] = self._render(
            0.05, sweep(900, 700, "square"), gain=0.18
        )
        self.sounds["dash"] = self._render(
            0.16, sweep(280, 1250, "saw"), gain=0.22
        )
        self.sounds["minion_death"] = self._render(
            0.14, sweep(700, 140, "square"), gain=0.20
        )
        self.sounds["upgrade"] = self._render(
            0.5, arpeggio([392, 523, 659, 784, 1046]), gain=0.33
        )

    # -- playback -----------------------------------------------------------
    @property
    def muted(self) -> bool:
        return bool(self.settings.get("muted", False))

    def play(self, name: str) -> None:
        if not self.enabled or self.muted:
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        try:
            volume = _clamp(float(self.settings.get("sfx_volume", 0.7)), 0.0, 1.0)
            sound.set_volume(volume)
            sound.play()
        except (pygame.error, ValueError):
            pass

    def toggle_mute(self) -> bool:
        self.settings["muted"] = not self.muted
        return self.muted
