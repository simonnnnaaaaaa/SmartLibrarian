import { useState, useRef } from "react";
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

      // helper local: încearcă să extragă "Titlu: <...>" din răspunsul text
      const extractTitle = (answer = "") => {
        const m = /^Titlu:\s*(.+)$/mi.exec(answer);
        return m ? m[1].trim() : null;
      };

      // normalizează răspunsul: string -> {answer, picked_title}
      let normalized =
        typeof data === "string"
          ? { answer: data, picked_title: extractTitle(data) }
          : { ...data };

      // fallback: dacă API nu a setat picked_title, încearcă din text
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

  return (
    <div className="container" >
      <h1 className="title">Smart Librarian </h1>
      <p className="subtitle">Pune o întrebare firească, iar noi îți recomandăm o carte și îți arătăm rezumatul detaliat.</p>

      <div className="card">
        <form onSubmit={onSubmit} style={{ display: "grid", gap: 12 }}>
          <label style={{ fontWeight: 600 }}>Întrebare</label>
          <textarea
            className="input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder='Ex.: "Vreau o carte despre prietenie și magie"'
          />

          <div className="row">
            <button className="button" type="submit" disabled={loading}>
              {loading ? <span className="row"><span className="spinner"></span> <span>Se caută...</span></span> : "Recomandă"}
            </button>
            <button className="button secondary" type="button" onClick={onReset} disabled={loading}>Reset</button>
            <span className="badge">Răspuns generat cu RAG</span>
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
            Exemple: <em>„Vreau o carte despre libertate și control social.”</em>,
            <em> „Ce-mi recomanzi dacă iubesc poveștile fantastice?”</em>,
            <em> „Ce este 1984?”</em>
          </div>
        )}
      </div>
    </div>
  );
}
