import React, { useState, useMemo } from 'react';
import './App.css';

function App() {
  const [ledStatus, setLedStatus] = useState("")
  const espWS = useMemo(() => {
    const esp = new WebSocket("ws://192.168.0.22:8080");
    esp.onmessage = ({ data: statusLed }) => setLedStatus(statusLed);
    esp.onopen = () => esp.send("is-led-on");
    return esp;
  }
    ,[])

  function toggleLedStatus() {
    espWS.send("toggle-led");
  }

  window.onbeforeunload = function(){
    espWS.close()
 }

  return (
    <div className="App">
      <h1>Teste LED ESP8266</h1>
      <p>Led status:</p>
      <div className={`status ${ledStatus.toLowerCase()}`}>{ledStatus}</div>
      <button onClick={toggleLedStatus}>Toggle LED</button>
    </div>
  );
}

export default App;
