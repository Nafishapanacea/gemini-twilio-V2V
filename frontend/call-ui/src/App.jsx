import { useState } from "react";
import { triggerCall, getCallResult } from "./api";
import "./App.css";

function App() {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [callResponse, setCallResponse] = useState(null);
  const [resultJson, setResultJson] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const handleCall = async () => {
    try {
      setLoading(true);
      setError("");
      setResultJson(null);

      const response = await triggerCall(phoneNumber);

      setCallResponse(response);

      setStatus("Call initiated. Waiting for evaluation to finish...");

      try {
        // Wait for the conversation to complete using a long-polling request
        const result = await getCallResult(response.call_sid, true);
        setResultJson(result);
        setStatus("Evaluation completed");
      } catch (err) {
        setStatus("Call ended");
        setError(
          err.response?.data?.detail ||
          "Call ended before completion or failed to retrieve results"
        );
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Failed to initiate call"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="card">

        <h1>AI OPD Caller</h1>

        <input
          type="text"
          placeholder="+00000000000"
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
        />

        <button
          disabled={loading}
          onClick={handleCall}
        >
          {loading ? "Calling..." : "Start Call"}
        </button>

        {status && (
          <p>{status}</p>
        )}

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {callResponse && (
          <>
            <h3>Call Response</h3>

            <pre>
              {JSON.stringify(callResponse, null, 2)}
            </pre>
          </>
        )}

        {resultJson && (
          <>
            <h3>Evaluation Summary</h3>

            <pre>
              {JSON.stringify(resultJson, null, 2)}
            </pre>
          </>
        )}

      </div>
    </div>
  );
}

export default App;