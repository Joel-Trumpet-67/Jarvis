const VOICE_PREF_KEY = "jarvis-voice-name";
const VOICE_MUTED_KEY = "jarvis-voice-muted";

const Voice = {
  recognition: null,
  supported: false,
  muted: localStorage.getItem(VOICE_MUTED_KEY) === "true",

  init(onResult) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.supported = !!SpeechRecognition;
    if (this.supported) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = "en-US";
      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        onResult(transcript);
      };
    }

    this._populateVoiceList();
    if (window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = () => this._populateVoiceList();
    }
  },

  start() {
    if (this.supported) this.recognition.start();
  },

  _pickDefaultVoice(voices) {
    const preferredNames = [
      "Google US English",
      "Samantha",
      "Microsoft Aria Online (Natural) - English (United States)",
      "Microsoft Guy Online (Natural) - English (United States)",
    ];
    for (const name of preferredNames) {
      const match = voices.find((v) => v.name === name);
      if (match) return match;
    }
    return voices.find((v) => v.lang === "en-US") || voices[0] || null;
  },

  _populateVoiceList() {
    if (!window.speechSynthesis) return;
    const select = document.getElementById("voice-select");
    if (!select) return;

    const voices = window.speechSynthesis.getVoices();
    if (voices.length === 0) return;

    const savedName = localStorage.getItem(VOICE_PREF_KEY);
    const current = voices.find((v) => v.name === savedName) || this._pickDefaultVoice(voices);

    select.innerHTML = "";
    for (const voice of voices) {
      const option = document.createElement("option");
      option.value = voice.name;
      option.textContent = `${voice.name} (${voice.lang})`;
      if (current && voice.name === current.name) option.selected = true;
      select.appendChild(option);
    }

    if (current) localStorage.setItem(VOICE_PREF_KEY, current.name);

    select.onchange = () => {
      localStorage.setItem(VOICE_PREF_KEY, select.value);
    };
  },

  toggleMute() {
    this.muted = !this.muted;
    localStorage.setItem(VOICE_MUTED_KEY, String(this.muted));
    if (this.muted && window.speechSynthesis) window.speechSynthesis.cancel();
    return this.muted;
  },

  speak(text) {
    if (!window.speechSynthesis || !text || this.muted) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);

    const voices = window.speechSynthesis.getVoices();
    const savedName = localStorage.getItem(VOICE_PREF_KEY);
    const voice = voices.find((v) => v.name === savedName) || this._pickDefaultVoice(voices);
    if (voice) utterance.voice = voice;

    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  },
};
