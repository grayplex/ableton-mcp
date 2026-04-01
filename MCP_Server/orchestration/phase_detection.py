"""Shared constants for phase-detection heuristics used by checkpoint and next_actions."""

# Track name substrings -> phase association
_DRUM_NAMES = {"drum", "kick", "snare", "percussion", "beat"}
_BASS_NAMES = {"bass", "sub"}
_HARMONY_NAMES = {"chord", "pad", "harm", "keys", "piano", "strings", "organ"}
_MELODY_NAMES = {"lead", "melody", "mel", "synth", "arp"}

# Device class names from get_mix_state RS output
_COMPRESSOR = "Compressor2"
_GLUE_COMPRESSOR = "GlueCompressor"
_LIMITER = "Limiter2"
