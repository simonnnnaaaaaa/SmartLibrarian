import { useState, useRef, useEffect } from "react";
import "./styles.css";
import { recommend, generateImage } from "./lib/api";


export default function App() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const [imgLoading, setImgLoading] = useState(false);
  const [imgUrl, setImgUrl] = useState("");
  const imgRef = useRef(null);

  const [voices, setVoices] = useState([]);
  const [voiceName, setVoiceName] = useState("");
  const [speaking, setSpeaking] = useState(false);
  const [paused, setPaused] = useState(false);

  const extractTitleFromAnswer = (answer = "") => {
    const m = /^Titlu:\s*(.+)$/mi.exec(answer);
    return m ? m[1].trim() : null;
  };

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setResult(null);

    const query = q.trim();
    if (!query) {
      setError('Scrie ce te interesează. Ex.: „Vreau o carte despre prietenie și magie”.');
      return;
    }

    setLoading(true);
    try {
      const data = await recommend(query);

      const extractTitle = (answer = "") => {
        const m = /^Titlu:\s*(.+)$/mi.exec(answer);
        return m ? m[1].trim() : null;
      };

      let normalized =
        typeof data === "string"
          ? { answer: data, picked_title: extractTitle(data) }
          : { ...data };

      if (!normalized.picked_title) {
        const maybe = extractTitle(normalized.answer || "");
        if (maybe) normalized.picked_title = maybe;
      }

      setResult(normalized);
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  async function onGenerateImage() {
    const title =
      result?.picked_title || extractTitleFromAnswer(result?.answer || "");
    if (!title) {
      setError("Nu am putut deduce titlul recomandat din răspuns.");
      return;
    }
    setImgLoading(true);
    try {
      const hint = (result?.answer || q).slice(0, 400);
      const url = await generateImage(title, hint, "cinematic cover");
      if (imgUrl) URL.revokeObjectURL(imgUrl);
      setImgUrl(url);
      setTimeout(() => imgRef.current?.scrollIntoView({ behavior: "smooth" }), 0);
    } catch (e) {
      console.error(e);
      setError("Nu am reușit să generez imaginea.");
    } finally {
      setImgLoading(false);
    }
  }


  function onReset() {
    setQ(""); setResult(null); setError("");
    if (imgUrl) URL.revokeObjectURL(imgUrl);
    setImgUrl("");
  }

  const picked = result?.picked_title;
  const answer = result?.answer || "";


  const getAnswerText = () => (result?.answer || "").replace(/•/g, "• ").trim();

  useEffect(() => {
    if (!("speechSynthesis" in window)) return;

    const loadVoices = () => {
      const list = window.speechSynthesis.getVoices();
      setVoices(list);
      const ro = list.find(v => (v.lang || "").toLowerCase().startsWith("ro"));
      setVoiceName(ro?.name || list[0]?.name || "");
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;

    return () => { window.speechSynthesis.onvoiceschanged = null; };
  }, []);

  function speak() {
    if (!("speechSynthesis" in window)) {
      alert("Text-to-Speech nu este suportat de acest browser.");
      return;
    }
    const text = getAnswerText();
    if (!text) return;

    window.speechSynthesis.cancel();

    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 1;
    utter.pitch = 1;
    const selected = voices.find(v => v.name === voiceName);
    if (selected) utter.voice = selected;

    utter.onstart = () => { setSpeaking(true); setPaused(false); };
    utter.onend = () => { setSpeaking(false); setPaused(false); };
    utter.onerror = () => { setSpeaking(false); setPaused(false); };

    window.speechSynthesis.speak(utter);
  }

  function pauseTTS() {
    if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
      setPaused(true);
    }
  }

  function resumeTTS() {
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      setPaused(false);
    }
  }

  function stopTTS() {
    window.speechSynthesis.cancel();
    setSpeaking(false);
    setPaused(false);
  }


  return (
    <div className="container" >
      <h1 className="title">Smart Librarian </h1>
      <p className="subtitle">Vrei să citești ceva? noi îți recomandăm o carte și îți arătăm rezumatul detaliat.</p>

      <div className="card">
        <form onSubmit={onSubmit} style={{ display: "grid", gap: 12 }}>
          <label style={{ fontWeight: 600 }}>Despre ce ai vrea să fie cartea</label>
          <textarea
            className="input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder='Exemplu: "Vreau o carte despre prietenie și magie"'
          />

          <div className="row">
            <button className="button" type="submit" disabled={loading}>
              {loading ? <span className="row"><span className="spinner"></span> <span>Se caută...</span></span> : "Recomandă"}
            </button>
            <button className="button secondary" type="button" onClick={onReset} disabled={loading}>Reset</button>
          </div>

          {error && <div className="error">{error}</div>}
        </form>

        {result && (
          <div className="result">
            {picked && <h2 style={{ margin: "14px 0 6px" }}>{picked}</h2>}
            <div>{answer || "(Nu am primit răspuns de la server.)"}</div>
          </div>
        )}

        {result && (
          <div style={{
            marginTop: 12, padding: 12, borderRadius: 12,
            border: "1px solid #1f2937", background: "#0f172a"
          }}>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
              <select
                value={voiceName}
                onChange={(e) => setVoiceName(e.target.value)}
                style={{
                  flex: "1 1 200px", padding: "10px 12px", borderRadius: 12,
                  background: "#0b1220", color: "#e5e7eb", border: "1px solid #334155"
                }}
              >
                {voices.length === 0 ? (
                  <option value="">(Se încarcă vocile…)</option>
                ) : voices.map(v => (
                  <option key={v.name} value={v.name}>
                    {v.name} {v.lang ? `(${v.lang})` : ""}
                  </option>
                ))}
              </select>

              <button
                type="button"
                onClick={speak}
                disabled={!getAnswerText()}
                style={{
                  padding: "10px 16px", borderRadius: 12, border: "1px solid #111827",
                  background: "#0d9488", color: "#fff", fontWeight: 600, cursor: "pointer",
                  flex: "1 1 160px"
                }}
              >
                🔊 Ascultă
              </button>

              <button
                type="button"
                onClick={paused ? resumeTTS : pauseTTS}
                disabled={!speaking}
                style={{
                  padding: "10px 16px", borderRadius: 12, border: "1px solid #334155",
                  background: "#1f2937", color: "#e5e7eb", fontWeight: 600, cursor: speaking ? "pointer" : "not-allowed",
                  flex: "1 1 140px"
                }}
              >
                {paused ? "Continuă" : "Pauză"}
              </button>

              <button
                type="button"
                onClick={stopTTS}
                disabled={!speaking}
                style={{
                  padding: "10px 16px", borderRadius: 12, border: "1px solid #7f1d1d",
                  background: "#991b1b", color: "#fff", fontWeight: 600, cursor: speaking ? "pointer" : "not-allowed",
                  flex: "1 1 120px"
                }}
              >
                Oprește
              </button>
            </div>
          </div>
        )}


        {result && (
          <div style={{ marginTop: 12, display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={onGenerateImage}
              disabled={imgLoading}
              style={{
                padding: "10px 16px",
                borderRadius: 12,
                border: "1px solid #111827",
                background: "#3b82f6",
                color: "#fff",
                fontWeight: 600,
                cursor: "pointer",
                flex: "1 1 200px",
              }}
            >
              {imgLoading ? "Se generează imaginea…" : "Generează imagine"}
            </button>
            {imgUrl && (
              <div ref={imgRef} style={{ marginTop: 12 }}>
                <img
                  src={imgUrl}
                  alt={`Copertă generată${result?.picked_title ? ` – ${result.picked_title}` : ""}`}
                  style={{ width: "100%", height: "auto", borderRadius: 16, border: "1px solid #1f2937" }}
                />
              </div>
            )}

          </div>
        )}

        {!result && !error && (
          <div className="helper">
            Exemple: 
            <em>„Vreau o carte despre libertate și control social.”</em>,
            <em> „Ce-mi recomanzi dacă iubesc poveștile fantastice?”</em>,
            <em> „Ce este 1984?”</em>
          </div>
        )}
      </div>
    </div>
  );
}
