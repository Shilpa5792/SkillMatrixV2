import { useEffect, useState } from "react";
import Layout from "./layout";
import "./App.css";
import LandingPage from "./pages/LandingPage";
import MicrosoftLoginModal from "./component/MicrosoftLoginModal";
import { useAuth } from "./context/AuthContext";
import { useTheme } from "./context/ThemeContext";
import jktechLogo from "./assets/JK_Tech_Logo.svg";
import JKtechLogo from "./assets/JK_Tech_Logo.jpg";
import MainComponent from "./component/MainComponent";

function App() {
  const { user } = useAuth();
  const { dark } = useTheme();
  const [showLanding, setShowLanding] = useState(false);
  const [showSplash, setShowSplash] = useState(true); // 🔹 Splash state

  // Load landing state from localStorage on app start
  useEffect(() => {
    const hasSeenLanding = localStorage.getItem("hasSeenLanding");
    setShowLanding(!(hasSeenLanding === "true"));
  }, []);

  // Hide splash after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowSplash(false);
    }, 3000);
    return () => clearTimeout(timer);
  }, []);

  // When user continues, mark landing as seen
  const handleContinue = () => {
    localStorage.setItem("hasSeenLanding", "true");
    setShowLanding(false);
  };

  // 🔹 Show splash first
  if (showSplash) {
    return (
      <div className=" h-screen flex items-center justify-center bg-gradient-to-r dark:to-gray-900 dark:via-gray-800 dark:from-gray-600">
        <img
          src={dark ? jktechLogo : JKtechLogo}
          className="animate-splash"
          width={350}
          alt="JK Tech Logo"
        />
        <style>{`
          @keyframes grow-fade {
            0% {
              transform: scale(1);
              opacity: 0;
            }
            20% {
              transform: scale(1);
              opacity: 1;
            }
            100% {
              transform: scale(8);
              opacity: 0;
            }
          }
          .animate-splash {
            animation: grow-fade 3s cubic-bezier(0.77, 0, 0.175, 1) forwards;
          }
        `}</style>
      </div>
    );
  }

  // 🔹 Show login modal if not authenticated
  if (!user) {
    return <MicrosoftLoginModal />;
  }

  // Main portal (after login)
  return (
    <div className="max-w-[100vw] max-h-[100vh]">
      <Layout>
        {showLanding ? (
          <LandingPage onContinue={handleContinue} />
        ) : (
          <MainComponent />
        )}
      </Layout>
    </div>
  );
}

export default App;
