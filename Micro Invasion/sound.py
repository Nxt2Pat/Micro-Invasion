"""
sound.py — Procedural retro sound generation
Generates simple waveform (sine, square, noise) WAV files in memory and loads them into pygame.mixer.Sound.
Authentic 8-bit/16-bit retro feel.
"""
import pygame
import wave
import struct
import io
import math
import random

def create_wave_sound(samples, sample_rate=44100):
    """Create a pygame.mixer.Sound from raw 16-bit PCM mono samples."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        # Pack list of integers into binary string (little-endian shorts)
        data = struct.pack('<' + 'h' * len(samples), *samples)
        w.writeframes(data)
    buf.seek(0)
    return pygame.mixer.Sound(buf)

def generate_square_wave(freq, duration, volume=0.5, fade_out=True):
    """Generate a retro square wave (NES/Gameboy feel)."""
    sample_rate = 44100
    length = int(sample_rate * duration)
    samples = []
    for i in range(length):
        t = i / sample_rate
        # Create square wave
        val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
        
        # Envelope overlay
        env = 1.0
        if fade_out:
            env = max(0.0, 1.0 - (i / length))
            
        samples.append(int(val * env * volume * 32767))
    return create_wave_sound(samples, sample_rate)

def generate_noise(duration, volume=0.5, fade_out=True):
    """Generate white noise for hits/splats."""
    sample_rate = 44100
    length = int(sample_rate * duration)
    samples = []
    for i in range(length):
        val = random.uniform(-1.0, 1.0)
        env = 1.0
        if fade_out:
            env = max(0.0, 1.0 - (i / length))
            # Exponential fade for punchier hits
            env = env * env 
        samples.append(int(val * env * volume * 32767))
    return create_wave_sound(samples, sample_rate)

def generate_sine_wave(freq, duration, volume=0.5, fade_out=True, freq_slide=0.0):
    """Generate a softer sine wave (for eerie or UI sounds)."""
    sample_rate = 44100
    length = int(sample_rate * duration)
    samples = []
    current_freq = freq
    for i in range(length):
        t = i / sample_rate
        current_freq += freq_slide * t
        val = math.sin(2 * math.pi * current_freq * t)
        
        env = 1.0
        if fade_out:
            env = max(0.0, 1.0 - (i / length))
            
        samples.append(int(val * env * volume * 32767))
    return create_wave_sound(samples, sample_rate)


def generate_ambient_drone(duration=5.0, volume=0.3):
    """Generate a low, detuned, creepy drone loop."""
    sample_rate = 44100
    length = int(sample_rate * duration)
    samples = []
    for i in range(length):
        t = i / sample_rate
        # Mix two low frequency sines with slight detune for eerie beating
        val1 = math.sin(2 * math.pi * 55 * t)
        val2 = math.sin(2 * math.pi * 58 * t)
        samples.append(int((val1 + val2) * 0.5 * volume * 32767))
    return create_wave_sound(samples, sample_rate)


class SoundManager:
    """Singleton-like manager to hold all procedural sound effects."""
    
    def __init__(self):
        # Master volume control
        self.master_vol = 0.4
        
        # Generation dictionary
        print("Generating procedural sounds...")
        self.sfx_hit = generate_noise(0.15, 0.4)
        self.sfx_eat = generate_square_wave(800, 0.08, 0.2)
        self.sfx_xp  = generate_sine_wave(1200, 0.1, 0.2, freq_slide=1000)
        self.sfx_shoot = generate_square_wave(400, 0.1, 0.3)
        self.sfx_death = generate_noise(0.4, 0.6)
        self.sfx_boss_spawn = generate_sine_wave(100, 2.0, 0.8, fade_out=False, freq_slide=-50)
        self.sfx_heartbeat = generate_sine_wave(80, 0.15, 0.9, fade_out=True)
        self.sfx_level_up = generate_square_wave(600, 0.5, 0.4)
        self.sfx_powerup = generate_sine_wave(400, 0.3, 0.3, freq_slide=800)
        self.sfx_drone = generate_ambient_drone(3.0, 0.5)

    def play(self, sound_name, loops=0):
        try:
            snd = getattr(self, f"sfx_{sound_name}")
            snd.set_volume(self.master_vol)
            snd.play(loops=loops)
        except AttributeError:
            print(f"Sound {sound_name} not found.")

# Global instance (initialized later in main/game)
audio = None
