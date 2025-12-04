import React, { useState, useRef, useEffect } from "react";
import jkLogo from "./assets/JK_Tech_Logo.svg";
import { useAuth } from "./context/AuthContext";
import ThemeToggle from "./component/ThemeToggle";
import { getChar } from "./helper/utility";
import ProfileModal from "./component/ProfileModal";
import { FiHelpCircle } from "react-icons/fi";

function Layout({ children }) {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const menuRef = useRef(null);

  // Close dropdown if clicked outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="h-screen flex flex-col relative bg-gray-50 dark:bg-gray-900 dark:text-gray-100 transition-colors duration-300">
      {/* Header */}
      <header className="px-2 sm:px-4 bg-gradient-to-r from-blue-800 via-blue-700 to-blue-500 dark:to-gray-900 dark:via-gray-800 dark:from-gray-600 text-white shadow-md border-b border-blue-500/40 dark:border-gray-700 backdrop-blur-sm z-[100] relative transition-colors duration-300">
        <div className="flex flex-wrap items-center justify-between gap-3 relative">
          {/* Left: Logo + Skill Matrix */}
          <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
            <img
              src={jkLogo}
              alt="JK Tech logo"
              className="h-12 sm:h-14 md:h-16 w-auto drop-shadow-lg"
            />
            <div className="hidden sm:block w-px h-10 sm:h-12 bg-white/40 dark:bg-gray-600"></div>
            <div className="text-left">
              <h1 className="text-[18px] sm:text-[20px] md:text-[24px] font-extrabold tracking-tight leading-tight text-white dark:text-gray-100 drop-shadow-sm">
                Skill Matrix
              </h1>
              <p className="hidden sm:block text-[10px] sm:text-[11px] md:text-[12px] text-blue-100/90 dark:text-gray-400 leading-snug">
                A structured way to record and showcase skills
              </p>
            </div>
          </div>

          {/* Right: Theme toggle + User Info */}
          <div className="flex items-center gap-3 sm:gap-4" ref={menuRef}>
            {/* Help Button */}
            <div className="relative group">
              <a
                href="https://skill-matrix-manuals.netlify.app/"
                target="_blank"
                rel="noopener noreferrer"
                title="Help"
                className="flex items-center justify-center h-9 w-9 sm:h-10 sm:w-10 rounded-full 
                    bg-white/10 dark:bg-gray-700/40 
                    hover:bg-white/20 dark:hover:bg-gray-600/60 
                    shadow-md hover:shadow-lg 
                     border-white/30 dark:border-gray-600 
                    transition-all duration-300 
                    hover:scale-110 cursor-pointer"
              >
                <FiHelpCircle className="h-5 w-5 sm:h-6 sm:w-6 text-white dark:text-gray-100" />
              </a>
            </div>

            {/* 🌙 Theme Toggle */}
            <ThemeToggle />

            {/* User Info + Avatar */}
            {user?.displayName && (
              <div className="relative flex items-center gap-2 sm:gap-3">
                {/* Hide text on xs for space */}
                <div className="hidden sm:flex flex-col items-end text-right">
                  <span className="text-[13px] sm:text-[14px] md:text-[16px] font-semibold text-white dark:text-gray-100 drop-shadow-sm truncate max-w-[160px]">
                    {`Welcome, ${user.displayName.toUpperCase()}`}
                  </span>
                  <span
                    className="text-[10px] sm:text-[11px] md:text-[12px] text-blue-100 dark:text-gray-400 truncate max-w-[160px]"
                    title={user.mail || user.userPrincipalName}
                  >
                    {user.mail || user.userPrincipalName}
                  </span>
                </div>

                {/* Profile Avatar */}
                <div className="relative">
                  <img
                    src={user.photoUrl}
                    alt="Profile"
                    className="h-8 w-8 sm:h-9 sm:w-9 md:h-10 md:w-10 rounded-full border-2 border-white dark:border-gray-600 cursor-pointer shadow-md hover:scale-105 transition"
                    onClick={() => setMenuOpen((prev) => !prev)}
                  />

                  {/* Dropdown */}
                  {menuOpen && (
                    <div className="absolute right-0 mt-2 w-44 sm:w-48 rounded-xl bg-white dark:bg-gray-800 shadow-xl border border-gray-100 dark:border-gray-700 z-[9999] overflow-hidden transition-colors duration-300">
                      {/* User details */}
                      <div className="flex flex-col items-center justify-center text-sm text-gray-700 dark:text-gray-200 space-y-1 py-3 px-4 bg-gray-50 dark:bg-gray-900">
                        <p className="font-semibold text-gray-800 dark:text-white text-center capitalize truncate">
                          {user.displayName + " " + getChar() || "NA"}
                        </p>
                        <p
                          className="truncate text-gray-500 dark:text-gray-300 text-center"
                          title={user.mail || user.userPrincipalName}
                        >
                          {(user.mail || user.userPrincipalName || "NA")
                            .length > 22
                            ? (user.mail || user.userPrincipalName).slice(
                                0,
                                19
                              ) + "..."
                            : user.mail || user.userPrincipalName || "NA"}
                        </p>
                        <p className="text-gray-500 dark:text-gray-400 text-center uppercase">
                          {user.department || "NA"}
                        </p>
                      </div>

                      {/* Logout */}
                      <button
                        className="w-full py-2 text-center text-sm text-gray-700 dark:text-gray-200 
                        border-t border-b border-gray-200 dark:border-gray-700
             bg-white hover:bg-blue-600
             dark:bg-gray-900 dark:hover:bg-blue-900
             transition font-medium"
                        onClick={() => {
                          setShowProfileModal(true);
                          setMenuOpen(false);
                        }}
                      >
                        Profile
                      </button>
                      <button
                        onClick={logout}
                        className="w-full py-2 text-center text-sm text-white bg-red-500 hover:bg-red-600 transition font-medium"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Profile Modal */}
      <ProfileModal
        open={showProfileModal}
        onClose={() => setShowProfileModal(false)}
        user={user}
      />

      {/* Content */}
      <div className="flex-1 flex">
        <main className="flex-1 p-1 sm:p-3 md:p-2 bg-gray-50 dark:bg-gray-900 dark:text-gray-100 overflow-auto transition-colors duration-300">
          {children}
        </main>
      </div>
    </div>
  );
}

export default Layout;
