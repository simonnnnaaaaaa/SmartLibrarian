import { useState } from "react";
import "./styles.css";
import { recommend } from "./lib/api";

export default function App() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function onSubmit(e) {
    e.preventDefault();
    setError(""); setResult(null);
    const query = q.trim();
    if (!query) { setError("Scrie ce te interesează. Ex.: „Vreau o carte despre prietenie și magie”."); return; }
    setLoading(true);
    try {
      const data = await recommend(query); // k=3 fix pe backend
      setResult(data);
    } catch (err) {
      setError(String(err?.message || err));
    } finally {
      setLoading(false);
    }
  }

  function onReset() { setQ(""); setResult(null); setError(""); }

  const picked = result?.picked_title;
  const answer = result?.answer || "";

  return (
    <div className="container">
      <h1 className="title">Smart Librarian UI</h1>
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
