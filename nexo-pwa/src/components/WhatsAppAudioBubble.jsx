import { useState, useRef, useEffect } from "react";

// Barras orgânicas com alturas fixas que simulam a trilha de forma de onda do WhatsApp
const WAVE_BARS = [
  8, 14, 22, 12, 16, 24, 18, 10, 14, 20, 26, 18, 12, 16, 22, 14,
  10, 16, 20, 14, 8, 12, 18, 14, 10, 16, 22, 16, 12, 8
];

function formatarTempo(segundos) {
  if (!segundos || isNaN(segundos) || segundos < 0) return "0:00";
  const m = Math.floor(segundos / 60);
  const s = Math.floor(segundos % 60);
  return `${m}:${s < 10 ? "0" : ""}${s}`;
}

export default function WhatsAppAudioBubble({ audioUrl, duracaoEstimada = 0 }) {
  const [tocando, setTocando] = useState(false);
  const [progresso, setProgresso] = useState(0); // 0 a 1
  const [tempoAtual, setTempoAtual] = useState(0);
  const [duracaoTotal, setDuracaoTotal] = useState(duracaoEstimada || 0);
  const [velocidade, setVelocidade] = useState(1);
  const audioRef = useRef(null);

  useEffect(() => {
    if (!audioUrl) return;
    const a = new Audio(audioUrl);
    audioRef.current = a;

    a.onloadedmetadata = () => {
      if (a.duration && isFinite(a.duration)) {
        setDuracaoTotal(a.duration);
      }
    };

    a.ontimeupdate = () => {
      setTempoAtual(a.currentTime);
      if (a.duration && isFinite(a.duration) && a.duration > 0) {
        setProgresso(a.currentTime / a.duration);
      }
    };

    a.onended = () => {
      setTocando(false);
      setProgresso(0);
      setTempoAtual(0);
    };

    return () => {
      a.pause();
      a.src = "";
    };
  }, [audioUrl]);

  const togglePlay = () => {
    const a = audioRef.current;
    if (!a) return;
    if (tocando) {
      a.pause();
      setTocando(false);
    } else {
      a.playbackRate = velocidade;
      a.play().catch((err) => console.warn("Erro ao tocar áudio WhatsApp:", err));
      setTocando(true);
    }
  };

  const mudarVelocidade = () => {
    const prox = velocidade === 1 ? 1.5 : velocidade === 1.5 ? 2 : 1;
    setVelocidade(prox);
    if (audioRef.current) {
      audioRef.current.playbackRate = prox;
    }
  };

  const handleSeek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    const a = audioRef.current;
    if (a && a.duration && isFinite(a.duration)) {
      a.currentTime = ratio * a.duration;
      setProgresso(ratio);
      setTempoAtual(a.currentTime);
    }
  };

  return (
    <div className="whatsapp-audio-bubble">
      {/* Botão Play / Pause Estilo WhatsApp */}
      <button
        type="button"
        className={`wa-play-btn ${tocando ? "playing" : ""}`}
        onClick={togglePlay}
        title={tocando ? "Pausar" : "Ouvir áudio"}
        aria-label={tocando ? "Pausar" : "Ouvir áudio"}
      >
        {tocando ? (
          <span className="wa-pause-icon">
            <span />
            <span />
          </span>
        ) : (
          <span className="wa-play-icon">▶</span>
        )}
      </button>

      {/* Trilha de Ondas e Tempo */}
      <div className="wa-track-container">
        {/* Forma de onda clicável */}
        <div
          className="wa-waveform"
          onClick={handleSeek}
          title="Clique para avançar/voltar"
        >
          {WAVE_BARS.map((altura, idx) => {
            const barRatio = idx / (WAVE_BARS.length - 1);
            const isPlayed = barRatio <= progresso;
            return (
              <span
                key={idx}
                className={`wa-bar ${isPlayed ? "played" : ""}`}
                style={{ height: `${altura}px` }}
              />
            );
          })}
        </div>

        {/* Rodapé: Tempo corrente e seletor de velocidade */}
        <div className="wa-track-footer">
          <span className="wa-timer">
            {tocando ? formatarTempo(tempoAtual) : formatarTempo(duracaoTotal)}
          </span>
          <button
            type="button"
            className="wa-speed-btn"
            onClick={mudarVelocidade}
            title="Alterar velocidade de reprodução"
          >
            {velocidade}x
          </button>
        </div>
      </div>
    </div>
  );
}
