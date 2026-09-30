import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./styles.css";

const scenes = [
  {
    number: "01",
    kicker: "THE INFORMATION AGE",
    title: "DATA IS\nEVERYWHERE.",
    body: "Every file begins as digital information.",
    visual: "data"
  },
  {
    number: "02",
    kicker: "A DIFFERENT MEDIUM",
    title: "WHAT IF DATA\nCOULD BECOME DNA?",
    body: "A digital sequence can be translated into the language of four bases.",
    visual: "dna"
  },
  {
    number: "03",
    kicker: "ENCODING",
    title: "BINARY\nBECOMES DNA.",
    body: "Digital information is mapped into A, C, G and T.",
    visual: "binary"
  },
  {
    number: "04",
    kicker: "FRAGMENTATION",
    title: "ONE FILE.\nMANY FRAGMENTS.",
    body: "The encoded sequence is divided into manageable fragments.",
    visual: "fragments"
  },
  {
    number: "05",
    kicker: "MOLECULAR ADDRESSING",
    title: "EVERY FRAGMENT\nGETS AN ADDRESS.",
    body: "Addresses allow fragments to be identified and reconstructed.",
    visual: "address"
  },
  {
    number: "06",
    kicker: "REDUNDANCY",
    title: "PROTECT\nTHE INFORMATION.",
    body: "Additional information provides a path to recovery.",
    visual: "redundancy"
  },
  {
    number: "07",
    kicker: "DIGITAL STORAGE",
    title: "THE ARCHIVE\nIS PRESERVED.",
    body: "The complete molecular archive exists here as a computational simulation.",
    visual: "storage"
  },
  {
    number: "08",
    kicker: "ERROR SIMULATION",
    title: "WHAT IF\nDATA IS LOST?",
    body: "Fragments can be damaged, corrupted or become unavailable.",
    visual: "error"
  },
  {
    number: "09",
    kicker: "RECOVERY",
    title: "THE ARCHIVE\nREBUILDS ITSELF.",
    body: "Redundancy and addressing guide the reconstruction process.",
    visual: "recovery"
  },
  {
    number: "10",
    kicker: "VERIFICATION",
    title: "THE DATA\nRETURNS.",
    body: "Recovered information is compared against the original.",
    visual: "verify"
  },
  {
    number: "11",
    kicker: "MOLECULAR ADDRESS",
    title: "FROM DATA\nTO DNA.\nAND BACK.",
    body: "A computational journey through digital DNA storage.",
    visual: "final"
  }
];

const bases = ["A","C","G","T"];

function DNA({ damaged=false }) {
  return (
    <div className={`dna ${damaged ? "damagedDna" : ""}`}>
      {Array.from({length:18}, (_,i) => (
        <motion.div
          className="pair"
          key={i}
          animate={{ x:[-8,8,-8], opacity:[.35,1,.35] }}
          transition={{
            duration:3+i*.08,
            repeat:Infinity,
            ease:"easeInOut"
          }}
        >
          <span>{bases[i%4]}</span>
          <i />
          <span>{bases[(i+2)%4]}</span>
        </motion.div>
      ))}
    </div>
  );
}

function Visual({type}) {
  if(type === "dna" || type === "storage")
    return <DNA />;

  if(type === "error")
    return <DNA damaged />;

  if(type === "recovery")
    return (
      <div className="recoveryVisual">
        <DNA />
        <div className="recoveryParticles">
          {Array.from({length:18},(_,i)=>
            <motionspan
              key={i}
              style={{
                "--x": `${(Math.random()-.5)*500}px`,
                "--y": `${(Math.random()-.5)*500}px`
              }}
            />
          )}
        </div>
      </div>
    );

  if(type === "binary")
    return (
      <div className="binary">
        {Array.from({length:8},(_,i)=>(
          <motion.div
            key={i}
            animate={{opacity:[.15,1,.15],y:[10,-10,10]}}
            transition={{duration:2+i*.2,repeat:Infinity}}
          >
            01001011&nbsp; 01100100&nbsp; 01000111
          </motion.div>
        ))}
        <strong>A&nbsp;&nbsp; C&nbsp;&nbsp; G&nbsp;&nbsp; T</strong>
      </div>
    );

  if(type === "data")
    return (
      <div className="dataStream">
        {Array.from({length:35},(_,i)=>(
          <motionspan
            key={i}
            animate={{x:["-10vw","110vw"],opacity:[0,.8,0]}}
            transition={{
              duration:4+Math.random()*5,
              repeat:Infinity,
              delay:Math.random()*5,
              ease:"linear"
            }}
          >
            {Math.random().toString(36).substring(2,12)}
          </motionspan>
        ))}
      </div>
    );

  if(type === "fragments")
    return (
      <div className="fragmentVisual">
        {Array.from({length:9},(_,i)=>(
          <motion.div
            key={i}
            animate={{y:[0,-18,0],rotate:[0,i%2?2:-2,0]}}
            transition={{duration:3+i*.1,repeat:Infinity}}
          >
            <small>F-{String(i+1).padStart(3,"0")}</small>
            <b>{Array.from({length:10},(_,j)=>bases[(i+j)%4]).join("")}</b>
          </motion.div>
        ))}
      </div>
    );

  if(type === "address")
    return (
      <div className="addressVisual">
        <DNA />
        <div className="addressLines">
          <span>F-001 · ADDR-A70001</span>
          <span>F-002 · ADDR-A70002</span>
          <span>F-003 · ADDR-A70003</span>
        </div>
      </div>
    );

  if(type === "redundancy")
    return (
      <div className="redundancy">
        <DNA />
        <motion.div
          className="ring ring1"
          animate={{scale:[1,1.15,1],opacity:[.3,.8,.3]}}
          transition={{duration:3,repeat:Infinity}}
        />
        <motion.div
          className="ring ring2"
          animate={{scale:[1.15,1,1.15],opacity:[.2,.7,.2]}}
          transition={{duration:4,repeat:Infinity}}
        />
      </div>
    );

  if(type === "verify")
    return (
      <div className="verifyVisual">
        <DNA />
        <motion.div
          className="check"
          initial={{scale:.5,opacity:.2}}
          animate={{scale:[.8,1.05,1],opacity:[.3,1,1]}}
          transition={{duration:3,repeat:Infinity}}
        >
          ✓
        </motion.div>
      </div>
    );

  return <DNA />;
}

export default function App() {
  const [index,setIndex] = useState(0);
  const scene = scenes[index];

  useEffect(() => {
    const timer = setTimeout(() => {
      setIndex((index+1)%scenes.length);
    }, 6500);

    return () => clearTimeout(timer);
  }, [index]);

  return (
    <div className="cinema">

      <div className="ambient ambientOne" />
      <div className="ambient ambientTwo" />
      <div className="grain" />

      <header className="nav">
        <div className="logo">
          <span>MA</span>
          <div>
            <b>MOLECULAR ADDRESS</b>
            <small>DIGITAL DNA ARCHIVE</small>
          </div>
        </div>

        <div className="navCenter">
          DNA DATA STORAGE
        </div>

        <div className="sceneNo">
          {scene.number} / {String(scenes.length).padStart(2,"0")}
        </div>
      </header>

      <main>

        <AnimatePresence mode="wait">

          <motion.section
            key={scene.number}
            className={`scene scene-${scene.visual}`}
            initial={{opacity:0}}
            animate={{opacity:1}}
            exit={{opacity:0}}
            transition={{duration:1.1}}
          >

            <div className="copy">

              <motion.div
                className="kicker"
                initial={{opacity:0,y:20}}
                animate={{opacity:1,y:0}}
                transition={{delay:.35}}
              >
                {scene.kicker}
              </motion.div>

              <motion.h1
                initial={{opacity:0,y:35}}
                animate={{opacity:1,y:0}}
                transition={{delay:.55,duration:1}}
              >
                {scene.title.split("\n").map((line,i)=>
                  <span key={i}>{line}</span>
                )}
              </motion.h1>

              <motion.p
                initial={{opacity:0,y:20}}
                animate={{opacity:1,y:0}}
                transition={{delay:.9}}
              >
                {scene.body}
              </motion.p>

            </div>

            <div className="visual">
              <Visual type={scene.visual}/>
            </div>

          </motion.section>

        </AnimatePresence>

      </main>

      <div className="progress">
        <motion.div
          key={index}
          initial={{width:"0%"}}
          animate={{width:"100%"}}
          transition={{duration:6.5,ease:"linear"}}
        />
      </div>

      <footer>
        <span>COMPUTATIONAL SIMULATION</span>
        <span>FRAGMENTATION · ENCODING · ADDRESSING · RECOVERY</span>
      </footer>

    </div>
  );
}
