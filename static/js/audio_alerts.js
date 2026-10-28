/**
 * Web Audio API Acoustic Alert Synthesizer.
 * Generates procedural warning tones without requiring external audio files.
 */

class AudioAlertSystem {
    constructor() {
        this.ctx = null;
        this.isMuted = false;
        this.initialized = false;
    }

    _initContext() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) {
                this.ctx = new AudioCtx();
            }
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    playCritical() {
        if (this.isMuted) return;
        this._initContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        
        // Triple urgent pulses
        [0, 0.22, 0.44].forEach(offset => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(880, now + offset);
            osc.frequency.exponentialRampToValueAtTime(580, now + offset + 0.18);

            gain.gain.setValueAtTime(0.2, now + offset);
            gain.gain.exponentialRampToValueAtTime(0.001, now + offset + 0.18);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now + offset);
            osc.stop(now + offset + 0.2);
        });
    }

    playWarning() {
        if (this.isMuted) return;
        this._initContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(660, now + 0.25);

        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.32);
    }

    playSafe() {
        if (this.isMuted) return;
        this._initContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, now); // C5
        osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.2); // E5

        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.28);
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        return this.isMuted;
    }
}

// Global alert system instance
window.soundAlerts = new AudioAlertSystem();
