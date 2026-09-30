import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  Database,
  Dna,
  FileText,
  FlaskConical,
  Layers3,
  LockKeyhole,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Waves,
} from "lucide-react";
import "./styles.css";

const stages = [
  {
    number: "01",
    title: "Input",
    short: "DATA",
    icon: FileText,
    color: "mint",
    description:
      "The original digital information enters the Molecular Address pipeline.",
    detail:
      "A file or data stream becomes the starting point of the storage process.",
  },
  {
    number: "02",
    title: "Fragmentation",
    short: "SPLIT",
    icon: Layers3,
    color: "green",
    description:
      "Large data is divided into smaller molecular-sized information fragments.",
    detail:
      "Fragmentation makes the information easier to encode, address, protect, and reconstruct.",
  },
  {
    number: "03",
    title: "DNA Encoding",
    short: "ENCODE",
    icon: Dna,
    color: "lime",
    description:
      "Digital information is represented using DNA-style nucleotide symbols.",
    detail:
      "Binary information is mapped into an A, C, G, T representation for the simulation.",
  },
  {
    number: "04",
    title: "Molecular Address",
    short: "ADDRESS",
    icon: LockKeyhole,
    color: "emerald",
    description:
      "Each fragment receives an identity so it can be located and reconstructed.",
    detail:
      "The molecular address connects each fragment to its position and recovery information.",
  },
  {
    number: "05",
    title: "Redundancy",
    short: "PROTECT",
    icon: ShieldCheck,
    color: "mint",
    description:
      "Additional information is introduced to improve recovery from damaged fragments.",
    detail:
      "Redundancy provides protection against simulated loss or corruption.",
  },
  {
    number: "06",
    title: "Storage",
    short: "STORE",
    icon: Database,
    color: "green",
    description:
      "The encoded molecular information enters the simulated storage layer.",
    detail:
      "This prototype represents how encoded fragments could be organized for molecular storage.",
  },
  {
    number: "07",
    title: "Error Simulation",
    short: "DAMAGE",
    icon: FlaskConical,
    color: "lime",
    description:
      "Controlled errors are introduced to simulate molecular storage damage.",
    detail:
      "The simulation tests whether the protection and addressing system can handle corrupted information.",
  },
  {
    number: "08",
    title: "Recovery",
    short: "RESTORE",
    icon: RotateCcw,
    color: "emerald",
    description:
      "The system uses addresses and redundancy to reconstruct the original information.",
    detail:
      "Damaged or missing fragments are identified and the recoverable information is rebuilt.",
  },
  {
    number: "09",
    title: "Verification",
    short: "VERIFY",
    icon: CheckCircle2,
    color: "mint",
    description:
      "The recovered result is compared against the original information.",
    detail:
      "Verification confirms whether the simulated recovery produced the expected result.",
  },
];

function DnaAnimation() {
  const bases = ["A", "T", "G", "C", "A", "G", "C", "T"];

  return (
    <div className="dna-scene">
      <div className="dna-glow" />

      <div className="dna-orbit orbit-one" />
      <div className="dna-orbit orbit-two" />

      <motion.div
        className="dna-helix"
        animate={{ rotateY: [0, 360] }}
        transition={{
          duration: 12,
          repeat: Infinity,
          ease: "linear",
        }}
      >
        <div className="dna-column">
          {bases.map((base, index) => (
            <motion.div
              className="base-pair"
              key={index}
              animate={{
                x: [0, 14, 0, -14, 0],
                opacity: [0.65, 1, 0.65],
              }}
              transition={{
                duration: 3,
                delay: index * 0.12,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              <span>{base}</span>
              <i />
              <span>{bases[(index + 3) % bases.length]}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>

      <motion.div
        className="floating-molecule molecule-one"
        animate={{ y: [0, -18, 0], x: [0, 8, 0] }}
        transition={{ duration: 4, repeat: Infinity }}
      >
        A
      </motion.div>

      <motion.div
        className="floating-molecule molecule-two"
        animate={{ y: [0, 16, 0], x: [0, -8, 0] }}
        transition={{ duration: 5, repeat: Infinity }}
      >
        G
      </motion.div>

      <motion.div
        className="floating-molecule molecule-three"
        animate={{ y: [0, -12, 0] }}
        transition={{ duration: 3.5, repeat: Infinity }}
      >
        C
      </motion.div>
    </div>
  );
}

function App() {
  const [activeStage, setActiveStage] = useState(0);
  const [online, setOnline] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/api/health")
      .then((response) => {
        if (response.ok) setOnline(true);
      })
      .catch(() => setOnline(false));
  }, []);

  const stage = stages[activeStage];
  const Icon = stage.icon;

  return (
    <main className="site">
      <header className="nav">
        <div className="brand">
          <div className="brand-mark">
            <Dna size={20} />
          </div>
          <div>
            <strong>Molecular Address</strong>
            <span>Digital DNA Storage Simulation</span>
          </div>
        </div>

        <div className="status">
          <span className={online ? "status-dot online" : "status-dot"} />
          {online ? "System connected" : "Simulation mode"}
        </div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <motion.div
            className="eyebrow"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            MOLECULAR DATA ARCHITECTURE
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            Giving digital data
            <br />
            a <span>molecular address.</span>
          </motion.h1>

          <motion.p
            className="hero-text"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            Molecular Address is a digital simulation of a DNA-inspired storage
            system that fragments, encodes, identifies, protects, stores,
            recovers, and verifies digital information.
          </motion.p>

          <motion.div
            className="hero-actions"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35 }}
          >
            <button
              className="primary-button"
              onClick={() =>
                document
                  .getElementById("process")
                  ?.scrollIntoView({ behavior: "smooth" })
              }
            >
              Explore the process
              <ArrowRight size={17} />
            </button>

            <div className="simulation-note">
              <Sparkles size={16} />
              <span>Digital simulation — no physical DNA synthesis</span>
            </div>
          </motion.div>
        </div>

        <motion.div
          className="hero-visual"
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7 }}
        >
          <DnaAnimation />
        </motion.div>
      </section>

      <section className="idea-section">
        <div className="section-intro">
          <span className="section-label">THE IDEA</span>
          <h2>From ordinary data to molecular information.</h2>
          <p>
            The important part is not simply storing information. The system
            needs to know where every fragment belongs, protect it against
            damage, recover it, and verify the result.
          </p>
        </div>

        <div className="mini-flow">
          {[
            ["DATA", FileText],
            ["FRAGMENTS", Layers3],
            ["MOLECULES", Dna],
            ["ADDRESSES", LockKeyhole],
            ["RECOVERY", RotateCcw],
          ].map(([label, FlowIcon], index) => (
            <div className="mini-flow-item" key={label}>
              <div className="mini-icon">
                <FlowIcon size={18} />
              </div>
              <span>{label}</span>
              {index !== 4 && <ArrowRight size={15} />}
            </div>
          ))}
        </div>
      </section>

      <section className="process-section" id="process">
        <div className="process-heading">
          <div>
            <span className="section-label">THE COMPLETE PIPELINE</span>
            <h2>How Molecular Address works</h2>
            <p>
              Follow the information from its original digital form through
              encoding, molecular addressing, protection, recovery, and final
              verification.
            </p>
          </div>

          <div className="progress">
            <span>{String(activeStage + 1).padStart(2, "0")}</span>
            <div>
              <div
                className="progress-fill"
                style={{
                  width: `${((activeStage + 1) / stages.length) * 100}%`,
                }}
              />
            </div>
            <span>09</span>
          </div>
        </div>

        <div className="process-line">
          <motion.div
            className="process-progress"
            animate={{
              width: `${(activeStage / (stages.length - 1)) * 100}%`,
            }}
          />

          {stages.map((item, index) => {
            const StageIcon = item.icon;

            return (
              <button
                key={item.number}
                className={`process-node ${
                  index === activeStage ? "active" : ""
                } ${index < activeStage ? "completed" : ""}`}
                onClick={() => setActiveStage(index)}
              >
                <motion.div
                  className="node-circle"
                  animate={
                    index === activeStage
                      ? {
                          scale: [1, 1.08, 1],
                        }
                      : { scale: 1 }
                  }
                  transition={{
                    duration: 1.8,
                    repeat: index === activeStage ? Infinity : 0,
                  }}
                >
                  <StageIcon size={18} />
                </motion.div>

                <span className="node-number">{item.number}</span>
                <strong>{item.title}</strong>
              </button>
            );
          })}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={stage.number}
            className="stage-detail"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.25 }}
          >
            <div className={`detail-icon ${stage.color}`}>
              <Icon size={30} />
            </div>

            <div className="detail-copy">
              <span>STAGE {stage.number}</span>
              <h3>{stage.title}</h3>
              <p className="detail-lead">{stage.description}</p>
              <p>{stage.detail}</p>
            </div>

            <div className="detail-side">
              <span>{stage.short}</span>
              <Waves size={22} />
            </div>
          </motion.div>
        </AnimatePresence>
      </section>

      <section className="recovery-section">
        <div>
          <span className="section-label">WHY ADDRESSING MATTERS</span>
          <h2>Storage is only half the problem.</h2>
          <p>
            A molecular storage system also needs a way to identify fragments,
            tolerate errors, reconstruct information, and verify what was
            recovered.
          </p>
        </div>

        <div className="recovery-flow">
          {[
            ["IDENTIFY", LockKeyhole],
            ["PROTECT", ShieldCheck],
            ["RECOVER", RotateCcw],
            ["VERIFY", CheckCircle2],
          ].map(([label, FlowIcon], index) => (
            <motion.div
              className="recovery-card"
              key={label}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
            >
              <FlowIcon size={20} />
              <strong>{label}</strong>
              <span>Step {index + 1}</span>
            </motion.div>
          ))}
        </div>
      </section>

      <footer>
        <div>
          <strong>Molecular Address</strong>
          <span>Digital DNA Storage Simulation</span>
        </div>

        <span>
          Prototype • No physical DNA synthesis claimed
        </span>
      </footer>
    </main>
  );
}

export default App;
