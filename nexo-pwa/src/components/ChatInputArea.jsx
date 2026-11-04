import React, { useState, useRef } from "react";

function ChatInputArea({ onEnviar, loading, onIniciarGravacao }) {
  const [texto, setTexto] = useState("");
  const inputRef = useRef(null);

  const handleEnviar = () => {
    const limpo = texto.trim();
    if (!limpo || loading) return;
    onEnviar(limpo);
    setTexto("");
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleEnviar();
    }
  };

  const handleChange = (e) => {
    const val = e.target.value;
    setTexto(val);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
  };

  return (
    <>
      <textarea
        ref={inputRef}
        className="chat-input"
        rows={2}
        placeholder="Pergunte ao CONEXO… (Enter para enviar)"
        value={texto}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
      />
      <button
        type="button"
        className="btn-icon btn-record"
        onClick={onIniciarGravacao}
        title="Gravar áudio (estilo WhatsApp)"
        aria-label="Gravar áudio"
      >
        <span className="chatgpt-voice-icon" aria-hidden="true">
          <span className="wave-bar bar-1" />
          <span className="wave-bar bar-2" />
          <span className="wave-bar bar-3" />
          <span className="wave-bar bar-4" />
        </span>
      </button>
      <button
        className="btn-icon btn-send"
        onClick={handleEnviar}
        disabled={loading || !texto.trim()}
        title="Enviar"
      >
        ➤
      </button>
    </>
  );
}

export default React.memo(ChatInputArea);
