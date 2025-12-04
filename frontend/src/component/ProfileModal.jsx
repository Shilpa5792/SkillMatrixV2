import React, { useState, useRef, useEffect } from "react";
import { FiUpload, FiEdit, FiCheck, FiX } from "react-icons/fi";
import { useAuth } from "../context/AuthContext";
import { FilePond, registerPlugin } from "react-filepond";
import "filepond/dist/filepond.min.css";
import FilePondPluginFileValidateType from "filepond-plugin-file-validate-type";
import FilePondPluginFileValidateSize from "filepond-plugin-file-validate-size";

registerPlugin(FilePondPluginFileValidateType, FilePondPluginFileValidateSize);

const ProfileModal = ({ open, onClose, user }) => {
  const { updateManagerEmail, uploadCV, uploading } = useAuth();
  const [editMode, setEditMode] = useState(false);
  const [managerEmail, setManagerEmail] = useState(user.managerEmail || "");
  const [cvFile, setCvFile] = useState(null);
  const [error, setError] = useState("");
  const [showUploadModal, setShowUploadModal] = useState(false);
  const profileRef = useRef(null);
  const uploadRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        profileRef.current &&
        !profileRef.current.contains(event.target) &&
        (!uploadRef.current || !uploadRef.current.contains(event.target))
      ) {
        onClose(); // close profile modal only if click is outside both modals
      }
    };

    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open, onClose]);

  useEffect(() => {
    setShowUploadModal(false);
  }, []);

  if (!open) return null;

  const handleSave = () => {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

    if (!emailRegex.test(managerEmail)) {
      setError("Please enter a valid manager email");
      return;
    }

    setError("");
    updateManagerEmail(managerEmail);
    setEditMode(false);
  };

  const fields = [
    { label: "Employee ID", value: user.employeeId },
    { label: "Name", value: user.displayName },
    { label: "Email", value: user.userPrincipalName },
    { label: "Job Title", value: user.jobTitle },
    { label: "Department", value: user.department },
  ];

  return (
    <div className="fixed inset-0 z-[99999] flex items-center justify-center px-2 md:px-0">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/50" />

      {/* Main Modal */}
      <div
        ref={profileRef}
        className="relative w-full max-w-2xl max-h-[90vh] p-5
        bg-white/30 dark:bg-gray-900/30 
        backdrop-blur-sm 
        rounded-2xl shadow-2xl 
        border border-white/20 dark:border-gray-700/40
        overflow-y-auto"
      >
        {/* Close */}
        <button
          className="absolute top-3 right-3 text-gray-400 hover:text-red-500 text-2xl transition"
          onClick={onClose}
        >
          &times;
        </button>

        <h2 className="text-2xl font-bold mb-4 text-center text-gray-800 dark:text-gray-100 tracking-wide">
          Profile Details
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {fields.map((field) => (
            <div key={field.label} className="flex flex-col">
              <label className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-0.5">
                {field.label}
              </label>
              <input
                type="text"
                value={field.value || ""}
                disabled
                className="p-2 border rounded-md bg-white/60 dark:bg-gray-800/60 
                border-gray-200 dark:border-gray-700 
                text-gray-800 dark:text-gray-100 
                focus:ring-1 focus:ring-blue-400 focus:outline-none 
                transition text-sm"
              />
            </div>
          ))}

          {/* Manager Email */}
          <div className="col-span-1 md:col-span-1 flex flex-col">
            <label className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-0.5">
              Manager Email
            </label>
            <div className="flex-1 relative flex items-center gap-2">
              <input
                type="email"
                value={managerEmail}
                disabled={!editMode}
                onChange={(e) => setManagerEmail(e.target.value)}
                className={`flex-1 p-2 border rounded-md text-gray-800 dark:text-gray-100 transition text-sm ${
                  editMode
                    ? "bg-white/80 dark:bg-gray-700/80 border-blue-400 focus:ring-1 focus:ring-blue-400"
                    : "bg-white/60 dark:bg-gray-800/60 border-gray-200 dark:border-gray-700"
                }`}
              />

              {!editMode ? (
                <FiEdit
                  className="text-blue-500 cursor-pointer hover:text-blue-600 transition"
                  size={20}
                  onClick={() => setEditMode(true)}
                />
              ) : (
                <>
                  <FiCheck
                    className="text-green-500 cursor-pointer hover:text-green-600 transition"
                    size={20}
                    onClick={handleSave}
                    title="Save"
                  />
                  <FiX
                    className="text-gray-500 cursor-pointer hover:text-red-500 transition"
                    size={20}
                    onClick={() => {
                      setError("");
                      setEditMode(false);
                      setManagerEmail(user.managerEmail || "");
                    }}
                    title="Cancel"
                  />
                </>
              )}
            </div>
            {error && (
              <span className="text-red-500 text-xs mt-1">{error}</span>
            )}
          </div>

          {/* CV Section */}
          <div className="col-span-2 flex items-center gap-3 overflow-x-auto whitespace-nowrap mt-2">
            <label className="text-sm font-medium text-gray-600 dark:text-gray-300 shrink-0">
              Curriculum Vitae (CV):
            </label>

            {user.cvUrl ? (
              <a
                href={user.cvUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-700 underline text-sm font-medium shrink-0"
              >
                View CV
              </a>
            ) : (
              <span className="text-xs text-gray-500 shrink-0">
                No CV uploaded
              </span>
            )}

            <FiUpload
              className="text-blue-500 cursor-pointer hover:text-blue-600 transition shrink-0"
              size={20}
              onClick={() => setShowUploadModal(true)}
              title="Upload CV"
            />
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div
          ref={uploadRef}
          className="fixed inset-0 z-[999999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
        >
          <div
            className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md p-6 border border-gray-200 dark:border-gray-700"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="absolute top-3 right-3 text-gray-400 hover:text-red-500 text-2xl transition"
              onClick={() => setShowUploadModal(false)}
            >
              &times;
            </button>

            <h3 className="text-xl font-bold mb-6 text-center text-gray-800 dark:text-gray-100">
              Upload Your Curriculum Vitae (CV)
            </h3>

            <FilePond
              allowMultiple={false}
              maxFileSize="10MB"
              acceptedFileTypes={[
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
              ]}
              labelIdle='📄 Drag & Drop your CV or <span class="filepond--label-action text-blue-500">Browse</span>'
              onupdatefiles={(fileItems) =>
                setCvFile(fileItems.length > 0 ? fileItems[0].file : null)
              }
              className="my-4"
            />

            {cvFile && (
              <div className="mt-2 text-center text-sm text-gray-700 dark:text-gray-300">
                <span className="font-medium text-blue-600 dark:text-blue-400">
                  {cvFile.name}
                </span>
              </div>
            )}

            <div className="flex justify-center gap-4 mt-6">
              <button
                onClick={() => {
                  if (!cvFile) return;

                  // Close modal immediately
                  setShowUploadModal(false);
                  setCvFile(null);

                  // Start upload asynchronously
                  (async () => {
                    try {
                      await uploadCV(cvFile); // your auth context handles toast notifications
                    } catch (err) {
                      console.error(err);
                    }
                  })();
                }}
                disabled={!cvFile || uploading}
                className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white font-medium text-sm px-5 py-2.5 rounded-md transition disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
              >
                <FiUpload />
                {uploading ? "Uploading..." : "Upload"}
              </button>

              <button
                onClick={() => {
                  setShowUploadModal(false);
                  setCvFile(null); // reset when cancelling
                }}
                className="bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-medium text-sm px-5 py-2.5 rounded-md transition shadow-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfileModal;
