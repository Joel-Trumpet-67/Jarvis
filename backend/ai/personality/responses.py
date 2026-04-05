"""
responses.py — Canned response strings for Rocky.
Boot messages, error quips, interrupt acknowledgements, etc.
Selected randomly to add variety. Written in Rocky's voice.
"""

import random
from backend.config import CONFIG


def _name():
    return CONFIG.get("user_name", "")


# --- Boot / startup ---
BOOT_MESSAGES = [
    "Systems online. Ready, {name}.",
    "All subsystems nominal. Is good.",
    "Online. Standing by, {name}.",
    "Initialised. What do you need?",
    "Ready. Let's go, {name}.",
    "Online. All clear.",
]

# --- AI model offline ---
MODEL_OFFLINE_MESSAGES = [
    "Neural link is offline, {name}. Working on it.",
    "Can't reach the AI core. Like losing comms near Tau Ceti. Reconnecting.",
    "Intelligence module unreachable. Retrying.",
    "Connection lost. Will reestablish.",
]

# --- AI model timeout ---
MODEL_TIMEOUT_MESSAGES = [
    "Taking too long. Like the Hail Mary at full burn. Try again, {name}.",
    "Response timeout. Retry?",
    "Model is slow. Try again.",
]

# --- Hard interrupt acknowledgements ---
INTERRUPT_MESSAGES = [
    "Stopping.",
    "Done.",
    "Understood, {name}.",
    "Halted.",
    "Stopped.",
]

# --- Unknown intent / can't help ---
UNKNOWN_INTENT_MESSAGES = [
    "Didn't catch that, {name}. Rephrase?",
    "Not sure what you need. Try again.",
    "Can you be more specific, {name}?",
    "Outside my current capabilities. What exactly do you need?",
]

# --- App not registered ---
APP_NOT_FOUND_TEMPLATE = (
    "Don't have {app_name!r} registered, {name}. "
    "Add it to the app registry."
)

# --- Generic error ---
GENERIC_ERROR_MESSAGES = [
    "Something went wrong. Apologies, {name}.",
    "Unexpected error. Shall we retry?",
    "Minor fault. Investigating.",
]


# --- Accessor functions ---

def get_boot_message() -> str:
    return random.choice(BOOT_MESSAGES).format(name=_name())

def get_offline_message() -> str:
    return random.choice(MODEL_OFFLINE_MESSAGES).format(name=_name())

def get_timeout_message() -> str:
    return random.choice(MODEL_TIMEOUT_MESSAGES).format(name=_name())

def get_interrupt_ack() -> str:
    return random.choice(INTERRUPT_MESSAGES).format(name=_name())

def get_unknown_intent() -> str:
    return random.choice(UNKNOWN_INTENT_MESSAGES).format(name=_name())

def get_app_not_found(app_name: str) -> str:
    return APP_NOT_FOUND_TEMPLATE.format(app_name=app_name, name=_name())

def get_generic_error() -> str:
    return random.choice(GENERIC_ERROR_MESSAGES).format(name=_name())
