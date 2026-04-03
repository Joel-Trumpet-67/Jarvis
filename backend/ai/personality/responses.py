"""
responses.py — Canned response strings for Jarvis.
Boot messages, error quips, interrupt acknowledgements, etc.
These are selected randomly to add variety.
"""

import random


# --- Boot / startup ---
BOOT_MESSAGES = [
    "All systems online. Good to have you back, sir.",
    "EIGENFORM initialized. At your service.",
    "Ready when you are, sir.",
    "All subsystems nominal. How may I assist?",
    "Online and fully operational. Good evening, sir.",
    "Systems check complete. Standing by.",
]

# --- AI model offline ---
MODEL_OFFLINE_MESSAGES = [
    "My neural link appears to be offline, sir. Attempting reconnection.",
    "I seem to be experiencing a momentary lapse in connectivity, sir.",
    "The AI core is unreachable at the moment, sir. I'll keep trying.",
    "Connection to the intelligence module has been lost, sir. Reconnecting.",
]

# --- AI model timeout ---
MODEL_TIMEOUT_MESSAGES = [
    "The AI core is taking longer than expected, sir. Please try again.",
    "Response time exceeded acceptable limits, sir. Shall I retry?",
    "The model appears to be under heavy load, sir. Retrying momentarily.",
]

# --- Hard interrupt acknowledgements ---
INTERRUPT_MESSAGES = [
    "Of course, sir.",
    "Understood, sir.",
    "As you wish, sir.",
    "Stopping immediately, sir.",
    "Right away, sir.",
]

# --- Unknown intent / can't help ---
UNKNOWN_INTENT_MESSAGES = [
    "I'm not sure I follow, sir. Could you rephrase that?",
    "I'm afraid I didn't quite catch that, sir.",
    "Could you clarify what you'd like me to do, sir?",
    "That falls outside my current capabilities, sir. Could you be more specific?",
]

# --- App not registered ---
APP_NOT_FOUND_TEMPLATE = (
    "I don't have {app_name!r} registered, sir. "
    "You can add it to the app registry at any time."
)

# --- Generic error ---
GENERIC_ERROR_MESSAGES = [
    "Something went wrong on my end, sir. Apologies.",
    "I encountered an unexpected error, sir. Shall we try again?",
    "A minor fault has occurred, sir. I'm looking into it.",
]


# --- Accessor functions ---

def get_boot_message() -> str:
    return random.choice(BOOT_MESSAGES)

def get_offline_message() -> str:
    return random.choice(MODEL_OFFLINE_MESSAGES)

def get_timeout_message() -> str:
    return random.choice(MODEL_TIMEOUT_MESSAGES)

def get_interrupt_ack() -> str:
    return random.choice(INTERRUPT_MESSAGES)

def get_unknown_intent() -> str:
    return random.choice(UNKNOWN_INTENT_MESSAGES)

def get_app_not_found(app_name: str) -> str:
    return APP_NOT_FOUND_TEMPLATE.format(app_name=app_name)

def get_generic_error() -> str:
    return random.choice(GENERIC_ERROR_MESSAGES)
