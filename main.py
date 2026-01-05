    def generate_piano_wave_with_attack(self, frequency, duration_ms):
        """Piano sound with hammer attack noise"""
        duration_s = duration_ms / 1000.0
        num_samples = int(self.sample_rate * duration_s)
        
        # Harmonics with slightly different ratios for realism
        harmonics = [
            (1.00, 1.00), (2.00, 0.85), (3.00, 0.70), (4.00, 0.55),
            (5.00, 0.45), (6.00, 0.35), (7.00, 0.25), (8.00, 0.15),
            (9.00, 0.10), (10.00, 0.05)
        ]
        
        audio_array = array.array('h')
        
        for i in range(num_samples):
            t = i / self.sample_rate
            
            # Envelope with faster attack
            attack = min(t / 0.005, 1.0)  # 5ms attack
            decay = math.exp(-t * 3)      # Fast decay
            release = math.exp(-max(0, t - duration_s * 0.7) * 2)  # Release starts at 70%
            envelope = attack * decay * release
            
            # Add slight hammer noise at the very beginning
            hammer_noise = 0
            if t < 0.001:  # First 1ms
                hammer_noise = 0.3 * math.sin(t * 2000) * (1 - t/0.001)
            
            # Sum harmonics
            wave_value = hammer_noise
            for harmonic_ratio, amplitude in harmonics:
                # Real strings have slight inharmonicity
                inharmonicity = 1.0 + 0.0002 * harmonic_ratio * harmonic_ratio
                harmonic_freq = frequency * harmonic_ratio * inharmonicity
                
                # Each harmonic has slightly different envelope
                harmonic_env = envelope * math.exp(-t * harmonic_ratio * 0.5)
                wave_value += amplitude * harmonic_env * math.sin(2 * math.pi * harmonic_freq * t)
            
            # Normalize
            wave_value = wave_value / (len(harmonics) + 1)
            
            # Soft clipping for warmth
            if wave_value > 0.9:
                wave_value = 0.9 + (wave_value - 0.9) * 0.5
            elif wave_value < -0.9:
                wave_value = -0.9 + (wave_value + 0.9) * 0.5
            
            int_value = int(wave_value * 32767 * 0.8)
            audio_array.append(int_value)
            audio_array.append(int_value)
        
        return audio_array