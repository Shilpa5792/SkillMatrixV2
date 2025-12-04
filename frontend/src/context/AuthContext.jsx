// src/AuthContext.js
import React, { createContext, useContext, useEffect, useState } from "react";
import { useMsal, useAccount } from "@azure/msal-react";
import { loginRequest } from "../authConfig";
import { useSkills } from "./SkillContext";
import toast from "react-hot-toast"; // import toast
import axios from "axios";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const { instance, accounts } = useMsal();
  const activeAccount = useAccount(instance.getActiveAccount() || accounts[0]);
  const [user, setUser] = useState(null);
  const [uploading, setUploading] = useState(false);
  const { clearEmployeeSkills } = useSkills();
  const BASE_URL = import.meta.env.VITE_BASE_URL;
  // useEffect(() => {
  //   setUser({
  //     "@odata.context":
  //       "https://graph.microsoft.com/v1.0/$metadata#users/$entity",
  //     businessPhones: [],
  //     displayName: "shrishti",
  //     givenName: null,
  //     jobTitle: "Tech Lead",
  //     mail: null,
  //     mobilePhone: null,
  //     officeLocation: null,
  //     preferredLanguage: null,
  //     surname: null,
  //     userPrincipalName: "shrishti@tspreethi77gmail.onmicrosoft.com",
  //     id: "5cc4b844-bb3b-4cd3-8fd3-979b87a867bf",
  //   });
  // }, []); // Testing purpose only, remove in production

  useEffect(() => {
    if (activeAccount && !user) {
      getUserProfile();
    }
  }, [activeAccount]);

  const login = async () => {
    try {
      const loginResponse = await instance.loginPopup({ ...loginRequest });

      // ✅ Set active account manually
      if (loginResponse?.account) {
        instance.setActiveAccount(loginResponse.account);
      }

      localStorage.removeItem("forceAccountPicker");
      toast.success("Logged in successfully!", { duration: 3000 });
    } catch (err) {
      console.error("Login failed", err);
      toast.error("Login failed. Please try again.", { duration: 5000 });
    }
  };

  const getUserProfile = async () => {
    // Show loading toast
    const toastId = toast.loading("Fetching user details...", {
      duration: Infinity,
    });

    try {
      const response = await instance.acquireTokenSilent({
        ...loginRequest,
        account: accounts[0],
      });

      const headers = { Authorization: `Bearer ${response.accessToken}` };

      // Fetch profile info
      const graphResponse = await fetch(
        "https://graph.microsoft.com/v1.0/me?$select=displayName,userPrincipalName,employeeId,department,manager,jobTitle",
        { headers }
      );
      const profile = await graphResponse.json();

      // Fetch profile picture
      const photoResponse = await fetch(
        "https://graph.microsoft.com/v1.0/me/photo/$value",
        { headers }
      );

      if (photoResponse.ok) {
        const blob = await photoResponse.blob();
        profile.photoUrl = URL.createObjectURL(blob);
      } else {
        const name = encodeURIComponent(profile.displayName || "User");
        profile.photoUrl = `https://ui-avatars.com/api/?name=${name}&rounded=true&bold=true&background=2563eb&color=fff`;
      }

      // Save employee data to backend
      const managerResponse = await axios.post(
        `${BASE_URL}save_employee`,
        profile,
        {
          headers: { "Content-Type": "application/json" },
        }
      );
      profile.managerEmail = managerResponse.data.managerEmail;
      profile.cvUrl = managerResponse.data.cvPublicUrl;

      setUser(profile);
      console.log("Profile:", profile);
      toast.success("User details fetched successfully!", {
        id: toastId,
        duration: 3000,
      });

      return profile;
    } catch (error) {
      console.error("Fetching profile failed", error);
      toast.error(
        error?.response?.data?.error || "Failed to fetch user details.",
        { id: toastId, duration: 5000 }
      );
    }
  };

  // 🔹 Sign out
  const logout = async () => {
    setUser(null);
    clearEmployeeSkills();
    localStorage.setItem("hasSeenLanding", "false");
    await instance.logout({
      account: instance.getActiveAccount(),
      onRedirectNavigate: () => false,
    });
    toast.success("Logged out successfully!", { duration: 3000 }); // optional logout toast
  };

  const updateManagerEmail = async (newManagerEmail) => {
    const toastId = toast.loading("Updating manager email...", {
      duration: Infinity,
    });

    try {
      if (
        newManagerEmail.trim().toLowerCase() ===
        user.userPrincipalName.toLowerCase()
      ) {
        toast.error("You cannot set yourself as your own manager.", {
          id: toastId,
          duration: 5000,
        });
        return;
      }

      setUser((prevUser) => ({
        ...prevUser,
        managerEmail: newManagerEmail,
      }));

      const res = await axios.post(`${BASE_URL}update_manager_email`, {
        email: user.mail || user.userPrincipalName,
        managerEmail: newManagerEmail,
      });

      if (res.status === 200) {
        toast.success("Manager email updated successfully!", {
          id: toastId,
          duration: 3000,
        });
      } else {
        toast.error("Failed to update manager email. Please try again.", {
          id: toastId,
          duration: 5000,
        });
      }
    } catch (error) {
      console.error("Error updating manager email:", error);
      toast.error(
        error?.response?.data?.error ||
          "An unexpected error occurred while updating manager email.",
        {
          id: toastId,
          duration: 5000,
        }
      );
    }
  };

  const uploadCV = async (cvFile) => {
    if (!cvFile) return toast.error("Please select a file first.");
    if (!user?.employeeId) return toast.error("Employee ID missing.");

    setUploading(true);

    // Show start processing toast
    const toastId = toast.loading("Uploading CV...");

    const formData = new FormData();
    formData.append("file", cvFile);
    formData.append("employeeEmail", user.userPrincipalName);

    try {
      const response = await axios.post(`${BASE_URL}upload_cv`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data?.cvUrl) {
        const updatedUser = { ...user, cvUrl: response.data.cvUrl };
        setUser(updatedUser);

        toast.success("CV uploaded successfully!", { id: toastId });
        return response.data.cvUrl;
      } else {
        toast.error("Upload failed. Please try again.", { id: toastId });
      }
    } catch (err) {
      console.error(err);
      toast.error("Error uploading CV.", { id: toastId });
    } finally {
      setUploading(false);
    }
  };

  // 🔹 Load profile if already logged in

  return (
    <AuthContext.Provider
      value={{ user, login, logout, setUser, updateManagerEmail, uploadCV }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
