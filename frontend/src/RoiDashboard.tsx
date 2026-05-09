import React, { useEffect, useState } from "react";
import { ROI, ROIResponse } from "./types";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

interface SessionsResponse {
  sessions: string[];
  count: number;
}

export default function RoiDashboard() {
  const [sessions, setSessions] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [roiHistory, setRoiHistory] = useState<ROI[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/roi`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data: SessionsResponse = await res.json();
      setSessions(data.sessions);
    } catch (err: any) {
      setError(err.message || "Failed to fetch sessions.");
    } finally {
      setLoading(false);
    }
  };

  const fetchROI = async (sessionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/roi?session_id=${sessionId}`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data: ROIResponse = await res.json();
      setRoiHistory(data.roi);
      setSelectedSession(sessionId);
    } catch (err: any) {
      setError(err.message || "Failed to fetch ROI data.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>ROI History Dashboard</h1>
      {error && <p style={styles.error}>{error}</p>}

      <div style={styles.grid}>
        <div style={styles.sidebar}>
          <h3>Available Sessions</h3>
          <input
            type="text"
            placeholder="Search session ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={styles.searchInput}
          />
          {loading && !selectedSession && <p>Loading sessions...</p>}
          {!loading && sessions.filter(sid => sid.toLowerCase().includes(searchTerm.toLowerCase())).length === 0 && <p>No sessions found.</p>}
          <ul style={styles.sessionList}>
            {sessions.filter(sid => sid.toLowerCase().includes(searchTerm.toLowerCase())).map((sid) => (
              <li
                key={sid}
                style={{
                  ...styles.sessionItem,
                  background: selectedSession === sid ? "#e0f7fa" : "#fff",
                }}
                onClick={() => fetchROI(sid)}
              >
                {sid}
              </li>
            ))}
          </ul>
        </div>

        <div style={styles.main}>
          {selectedSession ? (
            <>
              <h3>Session: {selectedSession}</h3>
              {loading ? (
                <p>Loading ROI data...</p>
              ) : (
                <div style={styles.tableContainer}>
                  <table style={styles.table}>
                    <thead>
                      <tr>
                        {["#", "x", "y", "width", "height", "confidence", "time"].map((h) => (
                          <th key={h} style={styles.th}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {roiHistory.map((r, i) => (
                        <tr key={r.id || i}>
                          <td style={styles.td}>{i + 1}</td>
                          <td style={styles.td}>{r.x}</td>
                          <td style={styles.td}>{r.y}</td>
                          <td style={styles.td}>{r.width}</td>
                          <td style={styles.td}>{r.height}</td>
                          <td style={styles.td}>{r.confidence?.toFixed(2) ?? "—"}</td>
                          <td style={styles.td}>{new Date(r.detected_at).toLocaleTimeString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          ) : (
            <div style={styles.emptyState}>Select a session to view its ROI history.</div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { maxWidth: 1200, margin: "0 auto", padding: 24, fontFamily: "sans-serif" },
  title: { fontSize: 24, marginBottom: 16 },
  error: { color: "#c0392b", margin: "8px 0" },
  grid: { display: "flex", gap: 24, alignItems: "flex-start" },
  sidebar: { width: 300, background: "#f8f8f8", borderRadius: 8, padding: 16, border: "1px solid #ddd", display: "flex", flexDirection: "column" },
  searchInput: { padding: "8px 12px", marginBottom: "12px", border: "1px solid #ccc", borderRadius: "4px", width: "100%", boxSizing: "border-box" },
  main: { flex: 1, background: "#fff", borderRadius: 8, padding: 16, border: "1px solid #ddd", minHeight: 400 },
  sessionList: { listStyle: "none", padding: 0, margin: 0, maxHeight: 400, overflowY: "auto" },
  sessionItem: { padding: "10px 12px", borderBottom: "1px solid #eee", cursor: "pointer", fontSize: 14, wordBreak: "break-all" },
  tableContainer: { overflowX: "auto", maxHeight: 500, overflowY: "auto" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 13 },
  th: { background: "#eee", padding: "8px 10px", textAlign: "left", border: "1px solid #ddd", position: "sticky", top: 0 },
  td: { padding: "6px 10px", border: "1px solid #eee" },
  emptyState: { display: "flex", justifyContent: "center", alignItems: "center", height: "100%", color: "#888", fontStyle: "italic" }
};
