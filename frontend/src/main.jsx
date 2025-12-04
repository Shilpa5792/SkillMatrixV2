import { createRoot } from "react-dom/client";
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { Toaster } from "react-hot-toast";

import App from "./App.jsx";
import { msalConfig } from "./authConfig";
import { AuthProvider } from "./context/AuthContext.jsx";
import { SkillProvider } from "./context/SkillContext.jsx";
import { CertificateProvider } from "./context/CertificateContext.jsx";
import { ThemeProvider } from "./context/ThemeContext.jsx";
import "./index.css";

// ✅ Create MSAL instance
const msalInstance = new PublicClientApplication(msalConfig);

// ✅ Initialize MSAL before rendering the app
msalInstance.initialize().then(() => {
  createRoot(document.getElementById("root")).render(
    <MsalProvider instance={msalInstance}>
      <ThemeProvider>
        <CertificateProvider>
          <SkillProvider>
            <AuthProvider>
              <App />
              <Toaster
                position="top-center"
                reverseOrder={false}
                toastOptions={{
                  className:
                    "bg-white text-black dark:bg-gray-800 dark:text-white shadow-lg",
                  duration: 3000,
                }}
              />
            </AuthProvider>
          </SkillProvider>
        </CertificateProvider>
      </ThemeProvider>
    </MsalProvider>
  );
});
