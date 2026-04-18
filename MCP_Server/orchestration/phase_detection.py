"""Shared constants for phase-detection heuristics used by checkpoint and next_actions."""

# Track name substrings -> phase association
_DRUM_NAMES = {
    "drum", "kick", "snare", "percussion", "beat",
    "808", "tom", "clap", "hat", "hh", "hihat", "hi-hat",
    "cymbal", "rim", "shaker", "perc", "groove", "trap", "break",
}
_BASS_NAMES = {
    "bass", "sub",
    "low end", "bottom", "808 bass", "reese",
}
_HARMONY_NAMES = {
    "chord", "pad", "harm", "keys", "piano", "strings", "organ",
    "rhodes", "stab", "comp", "voicing", "epiano", "e-piano",
    "wurli", "clav", "synth pad",
}
_MELODY_NAMES = {
    "lead", "melody", "mel", "synth", "arp",
    "hook", "riff", "pluck", "solo", "top", "topline",
}

# Device class names from get_device_classes RS output
_COMPRESSOR = "Compressor2"
_GLUE_COMPRESSOR = "GlueCompressor"
_LIMITER = "Limiter"
