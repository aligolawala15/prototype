import React, { useEffect, useMemo, useState } from "react";

const STAGES = [
  {
    id: "input",
    number: "01",
    title: "Input File",
    short: "INPUT",
    description:
      "The selected digital file becomes the source data for the molecular storage simulation.",
  },
  {
    id: "fragmentation",
    number: "02",
    title: "Fragmentation",
    short: "SPLIT",
    description:
      "The file is divided into smaller fragments so the information can be addressed and reconstructed independently.",
  },
  {
    id: "dna_encoding",
    number: "03",
    title: "DNA Encoding",
    short: "ENCODE",
    description:
      "Binary data is represented using the four DNA bases A, C, G and T.",
  },
  {
    id: "molecular_address",
    number: "04",
    title: "Molecular Address",
    short: "ADDRESS",
    description:
      "Each molecular fragment receives an address so individual fragments can be located during recovery.",
  },
  {
    id: "redundancy",
    number: "05",
    title: "Redundancy",
    short: "PROTECT",
    description:
      "Additional information is simulated to improve recovery when some fragments are damaged or missing.",
  },
  {
    id: "storage",
    number: "06",
    title: "Storage",
    short: "STORE",
    description:
      "The encoded molecular representation is treated as the stored data layer of the simulation.",
  },
  {
    id: "error_simulation",
    number: "07",
    title: "Error Simulation",
    short: "DAMAGE",
    description:
      "A controlled amount of simulated damage is introduced to demonstrate why addressing and redundancy matter.",
  },
  {
    id: "recovery",
    number: "08",
    title: "Recovery",
    short: "RECOVER",
    description:
      "The system uses fragment addresses and redundancy to reconstruct the original information.",
  },
  {
    id: "verification",
    number: "09",
    title: "Verification",
    short: "VERIFY",
    description:
      "The recovered result is compared with the original file representation.",
  },
];

function bytesToBases(bytes, count = 72) {
  const bases = ["A", "C", "G", "T"];
  const output = [];

  for (let i = 0; i < Math.min(bytes.length, count); i++) {
    const value = bytes[i];
    output.push(bases[(value >> 6) & 3]);
    output.push(bases[(value >> 4) & 3]);
    output.push(bases[(value >> 2) & 3]);
    output.push(bases[value & 3]);
  }

  return output.join("");
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );

  return `${(bytes / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 2)} ${
    units[index]
  }`;
}

function hashPreview(bytes) {
  let hash = 2166136261;

  for (let i = 0; i < bytes.length; i++) {
    hash ^= bytes[i];
    hash = Math.imul(hash, 16777619);
  }

  return (hash >>> 0).toString(16).padStart(8, "0").toUpperCase();
}

function App() {
  const [file, setFile] = useState(null);
  const [bytes, setBytes] = useState(null);
  const [running, setRunning] = useState(false);
  const [activeStage, setActiveStage] = useState(0);
  const [completedStage, setCompletedStage] = useState(-1);
  const [finished, setFinished] = useState(false);
  const [errorRate, setErrorRate] = useState(8);

  const dnaPreview = useMemo(() => {
    if (!bytes) return "";
    return bytesToBases(bytes);
  }, [bytes]);

  const metrics = useMemo(() => {
    if (!file || !bytes) {
      return {
        fragments: 0,
        addresses: 0,
        redundancy: 0,
        damaged: 0,
      };
    }

    const fragments = Math.max(1, Math.ceil(file.size / 48));
    const redundancy = Math.max(1, Math.ceil(fragments * 0.15));
    const damaged = Math.max(1, Math.round(fragments * (errorRate / 100)));

    return {
      fragments,
      addresses: fragments,
      redundancy,
      damaged,
    };
  }, [file, bytes, errorRate]);

  useEffect(() => {
    if (!running) return;

    if (activeStage >= STAGES.length) {
      setRunning(false);
      setFinished(true);
      setCompletedStage(STAGES.length - 1);
      return;
    }

    const timer = setTimeout(() => {
      setCompletedStage(activeStage);
      setActiveStage((current) => current + 1);
    }, 850);

    return () => clearTimeout(timer);
  }, [running, activeStage]);

  const handleFile = async (event) => {
    const selected = event.target.files?.[0];

    if (!selected) return;

    const buffer = await selected.arrayBuffer();

    setFile(selected);
    setBytes(new Uint8Array(buffer));
    setRunning(false);
    setActiveStage(0);
    setCompletedStage(-1);
    setFinished(false);
  };

  const startDemo = () => {
    if (!file || !bytes) return;

    setRunning(true);
    setFinished(false);
    setActiveStage(0);
    setCompletedStage(-1);
  };

  const resetDemo = () => {
    setFile(null);
    setBytes(null);
    setRunning(false);
    setActiveStage(0);
    setCompletedStage(-1);
    setFinished(false);
  };

  const currentStage =
    activeStage < STAGES.length ? STAGES[activeStage] : STAGES[STAGES.length - 1];

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <div className="brand-row">
            <div className="brand-mark">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </div>

            <div>
              <div className="eyebrow">MOLECULAR ADDRESS</div>
              <div className="brand-subtitle">Digital DNA Storage Simulation</div>
            </div>
          </div>
        </div>

        <div className="simulation-status">
          <span className={`status-dot ${running ? "running" : ""}`}></span>
          {running ? "PROCESSING" : finished ? "COMPLETE" : "READY"}
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <span className="section-label">THE PROBLEM</span>

            <h1>
              Store digital information
              <br />
              as a <em>molecular representation.</em>
            </h1>

            <p>
              Molecular Address is a digital prototype demonstrating how a file
              can be fragmented, encoded, addressed, protected, stored,
              recovered and verified using a DNA-inspired storage workflow.
            </p>

            <div className="hero-note">
              <span className="note-icon">i</span>
              This prototype simulates the computational process. It does not
              synthesize or store physical DNA.
            </div>
          </div>

          <div className="dna-card">
            <div className="dna-label">DNA REPRESENTATION</div>

            <div className="dna-helix">
              <div className="helix-column">
                {["A", "C", "G", "T", "A", "G", "C"].map((base, i) => (
                  <span key={i}>{base}</span>
                ))}
              </div>

              <div className="helix-lines">
                {Array.from({ length: 7 }).map((_, i) => (
                  <i key={i}></i>
                ))}
              </div>

              <div className="helix-column second">
                {["T", "G", "C", "A", "T", "C", "G"].map((base, i) => (
                  <span key={i}>{base}</span>
                ))}
              </div>
            </div>

            <div className="dna-footer">
              <span>A · C · G · T</span>
              <span>4-state representation</span>
            </div>
          </div>
        </section>

        <section className="demo-section">
          <div className="section-heading">
            <div>
              <span className="section-label">LIVE PROTOTYPE</span>
              <h2>Try the complete process.</h2>
              <p>
                Upload one file and watch the information move through each
                stage of the Molecular Address workflow.
              </p>
            </div>

            <div className="demo-badge">
              <span></span>
              SINGLE FILE DEMO
            </div>
          </div>

          <div className="upload-panel">
            <div className="upload-icon">↑</div>

            <div className="upload-copy">
              <strong>
                {file ? file.name : "Choose a file to begin"}
              </strong>

              <span>
                {file
                  ? `${formatBytes(file.size)} · ${file.type || "Unknown file type"}`
                  : "Any small document, image, text file or sample data"}
              </span>
            </div>

            <label className="file-button">
              {file ? "Change File" : "Choose File"}
              <input type="file" onChange={handleFile} />
            </label>

            {file && (
              <button
                className="run-button"
                onClick={startDemo}
                disabled={running}
              >
                {running ? "Processing..." : finished ? "Run Again" : "Run Demo"}
                <span>→</span>
              </button>
            )}

            {file && (
              <button className="reset-button" onClick={resetDemo}>
                Reset
              </button>
            )}
          </div>
        </section>

        <section className="process-section">
          <div className="section-heading process-heading">
            <div>
              <span className="section-label">PROCESS ARCHITECTURE</span>
              <h2>From file to verified recovery.</h2>
            </div>

            <div className="stage-counter">
              {running
                ? `STEP ${String(Math.min(activeStage + 1, 9)).padStart(2, "0")} / 09`
                : finished
                ? "09 / 09 COMPLETE"
                : "09 STAGES"}
            </div>
          </div>

          <div className="process-line">
            <div
              className="process-progress"
              style={{
                width: `${Math.min((completedStage / 8) * 100, 100)}%`,
              }}
            ></div>
          </div>

          <div className="stage-grid">
            {STAGES.map((stage, index) => {
              const completed = index <= completedStage;
              const active = running && index === activeStage;

              return (
                <button
                  key={stage.id}
                  className={`stage-card ${
                    completed ? "completed" : ""
                  } ${active ? "active" : ""}`}
                  onClick={() => {
                    if (!running && file) {
                      setActiveStage(index);
                    }
                  }}
                >
                  <div className="stage-top">
                    <span>{stage.number}</span>

                    <div
                      className={`stage-indicator ${
                        completed ? "done" : ""
                      } ${active ? "pulse" : ""}`}
                    >
                      {completed ? "✓" : ""}
                    </div>
                  </div>

                  <strong>{stage.title}</strong>
                  <small>{stage.short}</small>

                  {active && <div className="active-bar"></div>}
                </button>
              );
            })}
          </div>

          <div className="stage-detail">
            <div className="detail-index">
              {currentStage.number}
            </div>

            <div className="detail-content">
              <span>{currentStage.short}</span>
              <h3>{currentStage.title}</h3>
              <p>{currentStage.description}</p>
            </div>

            <div className="detail-state">
              {finished
                ? "VERIFIED"
                : completedStage >= activeStage && file
                ? "READY"
                : running
                ? "PROCESSING"
                : "WAITING"}
            </div>
          </div>
        </section>

        {file && (
          <section className="results-section">
            <div className="section-heading">
              <div>
                <span className="section-label">SIMULATION OUTPUT</span>
                <h2>What happened to your file?</h2>
              </div>

              <div className={`result-state ${finished ? "verified" : ""}`}>
                <span></span>
                {finished ? "RECOVERY VERIFIED" : "AWAITING PROCESS"}
              </div>
            </div>

            <div className="metrics-grid">
              <div className="metric-card">
                <span>INPUT SIZE</span>
                <strong>{formatBytes(file.size)}</strong>
                <small>{file.name}</small>
              </div>

              <div className="metric-card">
                <span>FRAGMENTS</span>
                <strong>{metrics.fragments}</strong>
                <small>48-byte simulation blocks</small>
              </div>

              <div className="metric-card">
                <span>MOLECULAR ADDRESSES</span>
                <strong>{metrics.addresses}</strong>
                <small>one logical address per fragment</small>
              </div>

              <div className="metric-card">
                <span>REDUNDANCY</span>
                <strong>+{metrics.redundancy}</strong>
                <small>recovery fragments simulated</small>
              </div>
            </div>

            <div className="simulation-grid">
              <div className="data-panel">
                <div className="panel-heading">
                  <span>DNA ENCODING PREVIEW</span>
                  <span>{dnaPreview.length} bases shown</span>
                </div>

                <div className="sequence">
                  {dnaPreview
                    ? dnaPreview.split("").map((base, index) => (
                        <span key={index} className={`base-${base}`}>
                          {base}
                        </span>
                      ))
                    : "Select a file to generate a sequence preview."}
                </div>
              </div>

              <div className="data-panel">
                <div className="panel-heading">
                  <span>MOLECULAR ADDRESS TABLE</span>
                  <span>SIMULATED</span>
                </div>

                <div className="address-list">
                  {Array.from({
                    length: Math.min(metrics.fragments, 5),
                  }).map((_, index) => (
                    <div className="address-row" key={index}>
                      <span>
                        FRAG-{String(index + 1).padStart(3, "0")}
                      </span>

                      <code>
                        MA-{hashPreview(bytes)}-
                        {String(index).padStart(3, "0")}
                      </code>

                      <b>✓</b>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="error-panel">
              <div>
                <span className="section-label">CONTROLLED DAMAGE</span>
                <strong>
                  Simulate {errorRate}% fragment damage
                </strong>
                <p>
                  This demonstrates why molecular addressing and redundancy
                  are required for reliable recovery.
                </p>
              </div>

              <div className="error-control">
                <input
                  type="range"
                  min="0"
                  max="25"
                  value={errorRate}
                  onChange={(event) =>
                    setErrorRate(Number(event.target.value))
                  }
                />
                <span>{metrics.damaged} fragments affected</span>
              </div>
            </div>

            {finished && (
              <div className="verification-result">
                <div className="verification-icon">✓</div>

                <div>
                  <span>VERIFICATION COMPLETE</span>
                  <h3>Original information successfully reconstructed.</h3>
                  <p>
                    The prototype simulated fragmentation, molecular
                    addressing, redundancy, controlled damage and recovery for
                    the selected file.
                  </p>
                </div>

                <div className="verification-value">
                  <strong>100%</strong>
                  <span>SIMULATED MATCH</span>
                </div>
              </div>
            )}
          </section>
        )}

        <section className="core-section">
          <div>
            <span className="section-label">THE CORE IDEA</span>
            <h2>Storage is only half the problem.</h2>
            <p>
              Molecular Address focuses on the information layer around
              molecular storage: identifying fragments, giving them addresses,
              protecting them from simulated damage, reconstructing the data
              and verifying the recovered result.
            </p>
          </div>

          <div className="core-flow">
            <div>
              <span>01</span>
              <strong>IDENTIFY</strong>
            </div>

            <div>
              <span>02</span>
              <strong>ADDRESS</strong>
            </div>

            <div>
              <span>03</span>
              <strong>PROTECT</strong>
            </div>

            <div>
              <span>04</span>
              <strong>RECOVER</strong>
            </div>
          </div>
        </section>
      </main>

      <footer>
        <span>Molecular Address</span>
        <span>Digital DNA Storage Simulation</span>
        <span>Prototype · No physical DNA synthesis</span>
      </footer>
    </div>
  );
}

export default App;
