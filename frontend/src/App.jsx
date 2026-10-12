import { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState("Đang kiểm tra backend...");
  const [error, setError] = useState(false);

  useEffect(() => {
    async function checkHealth() {
      try {
        const response = await fetch("/health");

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.status === "ok") {
          setStatus("OK");
          setError(false);
        } else {
          setStatus("Backend chưa sẵn sàng");
          setError(true);
        }
      } catch (err) {
        setStatus("Không thể kết nối backend");
        setError(true);
        console.error("Health check failed:", err);
      }
    }

    checkHealth();
  }, []);

  return (
    <main style={{ padding: "2rem", fontFamily: "Arial, sans-serif" }}>
      <h1>AutomaticDubbing</h1>
      <p>
        Trạng thái backend:{" "}
        <strong style={{ color: error ? "red" : "green" }}>{status}</strong>
      </p>
    </main>
  );
}

export default App;
