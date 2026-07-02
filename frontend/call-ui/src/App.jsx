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

  const pollForResults = async (callSid) => {
    const interval = setInterval(async () => {
      try {
        const result = await getCallResult(callSid);

        setResultJson(result);
        setStatus("Evaluation completed");

        clearInterval(interval);
      } catch (err) {
        console.log("Waiting for results...");
      }
    }, 5000);
  };

  const handleCall = async () => {
    try {
      setLoading(true);
      setError("");
      setResultJson(null);

      const response = await triggerCall(phoneNumber);

      setCallResponse(response);

      setStatus("Call initiated. Waiting for evaluation to finish...");

      await pollForResults(response.call_sid);
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