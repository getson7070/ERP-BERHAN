(function () {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;
  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  const socket = window.io ? io() : null;
  recognition.onresult = (e) => {
    const text = e.results[0][0].transcript;
    if (socket) {
      socket.emit('voice_command', { command: text });
    }
  };
  document.addEventListener('keydown', (e) => {
    if (e.key === 'v') {
      recognition.start();
    }
  });
})();
