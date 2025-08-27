import { useEffect, useState } from "react";
import { fetchHealth } from "./lib/api";

function StatusBadge({ ok }) {
  return (
    <span
      style={{
        padding: "4px 10px",
        borderRadius: 999,
        background: ok ? "#e6ffed" : "#ffecec",
        border: `1px solid ${ok ? "#27ae60" : "#c0392b"}`,
        fontSize: 14,
      }}
    >
      Backend: {ok ? "✅ alive" : "❌ down"}
    </span>
  );
}

export default function App() {
  const [ok, setOk] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchHealth()
      .then(() => setOk(true))
      .catch((e) => {
        setOk(false);
        setError(String(e?.message || e));
      });
  }, []);

  return (
    <div style={{ maxWidth: 760, margin: "40px auto", padding: 16 }}>
      <h1>Smart Librarian UI</h1>
      <StatusBadge ok={!!ok} />
      {ok === false && (
        <p style={{ color: "#c0392b", marginTop: 8 }}>Detaliu: {error}</p>
      )}
      <hr style={{ margin: "24px 0" }} />
      <p style={{ opacity: 0.8 }}>
        Următorul pas: formular de recomandare care apelează <code>/recommand</code>.
      </p>
    </div>
  );
}
