import React, { useEffect } from "react";
import { getHeaderName } from "../helper/utility";

export default function LevelDetailModal({
  open,
  onClose,
  levels = {},
  title = "Level Details",
}) {
  const values = {
    L1: levels.L1 || "-",
    L2: levels.L2 || "-",
    L3: levels.L3 || "-",
  };

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      {/* backdrop */}
      <div
        className="fixed inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* modal panel */}
      <div className="relative w-[85%] max-h-[85vh] bg-white/90 dark:bg-gray-900/95 backdrop-blur-md border border-white/50 dark:border-gray-700 rounded-lg shadow-2xl flex flex-col overflow-y-auto">
        {/* header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white/90 dark:bg-gray-900/95 backdrop-blur-md z-10">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
            {title}
          </h3>
          <button
            onClick={onClose}
            aria-label="Close"
            className="inline-flex items-center justify-center rounded-md p-1 hover:bg-gray-200/60 dark:hover:bg-gray-700/60 transition"
          >
            <svg
              className="w-5 h-5 text-gray-700 dark:text-gray-300"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 8.586L15.293 3.293a1 1 0 111.414 1.414L11.414 10l5.293 5.293a1 1 0 01-1.414 1.414L10 11.414l-5.293 5.293a1 1 0 01-1.414-1.414L8.586 10 3.293 4.707A1 1 0 114.707 3.293L10 8.586z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>

        {/* body - responsive grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-5 flex-1">
          {/* L1 */}
          <div className="border rounded-lg p-4 bg-white/70 dark:bg-gray-800 flex flex-col">
            <p className="font-semibold text-gray-700 dark:text-gray-200 mb-2">
              {getHeaderName("L1")}:
            </p>
            <div className="pl-2 text-gray-600 dark:text-gray-300 text-sm space-y-1 overflow-y-auto flex-1">
              {values.L1.toString()
                .split("\n")
                .map((line, idx) => (
                  <p key={idx}>{line || "-"}</p>
                ))}
            </div>
          </div>

          {/* L2 */}
          <div className="border rounded-lg p-4 bg-white/70 dark:bg-gray-800 flex flex-col">
            <p className="font-semibold text-gray-700 dark:text-gray-200 mb-2">
              {getHeaderName("L2")}:
            </p>
            <div className="pl-2 text-gray-600 dark:text-gray-300 text-sm space-y-1 overflow-y-auto flex-1">
              {values.L2.toString()
                .split("\n")
                .map((line, idx) => (
                  <p key={idx}>{line || "-"}</p>
                ))}
            </div>
          </div>

          {/* L3 (full width) */}
          <div className="border rounded-lg p-4 bg-white/70 dark:bg-gray-800 flex flex-col md:col-span-2">
            <p className="font-semibold text-gray-700 dark:text-gray-200 mb-2">
              {getHeaderName("L3")}:
            </p>
            <div className="pl-2 text-gray-600 dark:text-gray-300 text-sm space-y-1 overflow-y-auto flex-1">
              {values.L3.toString()
                .split("\n")
                .map((line, idx) => (
                  <p key={idx}>{line || "-"}</p>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
