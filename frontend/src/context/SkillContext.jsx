import React, {
  createContext,
  useContext,
  useState,
  useRef,
  useEffect,
} from "react";

import axios from "axios";
import toast from "react-hot-toast";

const SkillContext = createContext();
const BASE_URL = import.meta.env.VITE_BASE_URL;

export const SkillProvider = ({ children }) => {
  const [masterSkills, setMasterSkills] = useState([]);
  const [employeeSkills, setEmployeeSkills] = useState([]);
  const [isMasterLoading, setIsMasterLoading] = useState(false);
  const [isEmployeeLoading, setIsEmployeeLoading] = useState(false);
  const [isRequestLoading, setIsRequestLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [requestData, setRequestData] = useState(null);
  const fetchToastId = useRef(null);
  const saveToastId = useRef(null);

  // 🔹 Fetch master skills once
  useEffect(() => {
    const fetchMasterSkills = async () => {
      try {
        setIsMasterLoading(true);
        const response = await axios.get(`${BASE_URL}get_master_skills`);
        setMasterSkills(response.data);
      } catch (err) {
        console.error("Failed to fetch master skills:", err);
        toast.error("Failed to fetch master skills");
      } finally {
        setIsMasterLoading(false);
      }
    };
    fetchMasterSkills();
  }, []);

  // 🔹 Fetch employee skills
  const fetchEmployeeSkills = async (email) => {
    if (!email) return;

    if (!fetchToastId.current) {
      fetchToastId.current = toast.loading("Loading employee skills...", {
        duration: Infinity,
      });
    }

    try {
      setIsEmployeeLoading(true);
      const response = await axios.post(`${BASE_URL}get_employee_skills`, {
        email,
      });
      setEmployeeSkills(response.data.skills || []);

      toast.success("Employee skills loaded successfully!", {
        id: fetchToastId.current,
        duration: 5000,
      });
    } catch (err) {
      if (err.response && err.response.status === 404) {
        toast.error("Previous skills not found ", {
          id: fetchToastId.current,
          duration: 8000,
        });
      } else {
        console.error("Failed to fetch employee skills:", err);
        setEmployeeSkills([]);
        toast.error("Failed to load employee skills", {
          id: fetchToastId.current,
          duration: 8000,
        });
      }
    } finally {
      setIsEmployeeLoading(false);
      fetchToastId.current = null; // reset
    }
  };

  // 🔹 Save employee skills
  const saveEmployeeSkills = async (
    employeeInfo,
    processedData,
    selectedRadios,
    managerEmail = ""
  ) => {
    if (!employeeInfo?.email) {
      toast.error("Employee Email is required", { duration: 8000 });
      return;
    }

    if (!saveToastId.current) {
      saveToastId.current = toast.loading("Saving employee skills...", {
        duration: Infinity,
      });
    }

    try {
      setIsSaving(true);
      await axios.post(
        `${BASE_URL}save_employee_skills`,
        {
          email: employeeInfo.email.toLowerCase(),
          managerEmail:
            employeeInfo.managerEmail.toLowerCase() ||
            managerEmail.toLowerCase(),
          skills: processedData
            .filter((row) => selectedRadios[row.hashId])
            .map((row) => ({
              Level: selectedRadios[row.hashId].Level,
              hashId: row.hashId,
            })),
        },
        { headers: { "Content-Type": "application/json" } }
      );
      await fetchEmployeeSkills(employeeInfo?.email);
      toast.success("Employee skills saved successfully!", {
        id: saveToastId.current,
        duration: 5000,
      });
    } catch (error) {
      console.error("Failed to save employee details:", error);
      toast.error(
        error.response?.data?.error ||
          "Failed to save employee details. Please try again.",
        { id: saveToastId.current, duration: 8000 }
      );
    } finally {
      setIsSaving(false);
      saveToastId.current = null; // reset
    }
  };

  const clearEmployeeSkills = () => {
    setEmployeeSkills([]);
  };

  const fetchEmployeeRequests = async (userEmail) => {
    const toastId = toast.loading("Fetching user data...", {
      duration: Infinity,
    });

    setIsRequestLoading(true); // ✅ start loading

    try {
      if (!userEmail) {
        toast.error("User email is required", { id: toastId, duration: 5000 });
        setIsRequestLoading(false);
        return;
      }

      const res = await axios.get(`${BASE_URL}get_expert_skill_request`, {
        params: { email: userEmail },
      });

      if (res.status === 200) {
        setRequestData(res.data);
        toast.success("User data fetched successfully!", {
          id: toastId,
          duration: 3000,
        });
      } else {
        toast.error("Failed to fetch user data. Please try again.", {
          id: toastId,
          duration: 5000,
        });
      }
    } catch (error) {
      console.error("Error fetching user data:", error);
      toast.error(
        error?.response?.data?.error ||
          "An unexpected error occurred while fetching user data.",
        { id: toastId, duration: 5000 }
      );
    } finally {
      setIsRequestLoading(false); // ✅ stop loading
    }
  };
  // 🔹 Download Skill Matrix
  const downloadSkillMatrix = async () => {
    const toastId = toast.loading("Preparing Skills master file...", {
      duration: Infinity,
    });

    try {
      const response = await axios.get(`${BASE_URL}get_master_file`, {
        params: { type: "skills" }, // always skills
        responseType: "blob", // important for file download
      });

      const blob = new Blob([response.data], { type: response.data.type });

      // Determine file extension
      let ext = ".csv"; // default
      if (
        blob.type ===
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ) {
        ext = ".xlsx";
      } else if (blob.type === "application/vnd.ms-excel") {
        ext = ".xls";
      }

      const filename = `Master_Skills${ext}`;

      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.success("Skills master file downloading!", {
        id: toastId,
        duration: 5000,
      });
    } catch (error) {
      console.error(error);
      toast.error("Failed to download Skills master file", {
        id: toastId,
        duration: 8000,
      });
    }
  };

  const reviewSkill = async (skillIds, approvedByEmail, action, reason) => {
    const toastId = toast.loading(
      action === "approve" ? "Approving skills..." : "Rejecting skills..."
    );

    try {
      if (!skillIds?.length || !approvedByEmail || !action) {
        toast.error("Missing required fields.", { id: toastId });
        return;
      }

      const payload = {
        approvedByEmail,
        action,
        reason: action === "reject" ? reason || "No reason provided" : null,
        skills: skillIds.map((id) => ({ empSkillId: id })),
      };

      const res = await axios.post(`${BASE_URL}review_skill`, payload);

      if (res.status === 200) {
        // ✅ Optimistic UI update for all reviewed skills
        setRequestData((prev) =>
          prev.map((emp) => ({
            ...emp,
            skills: emp.skills?.map((sk) =>
              skillIds.includes(sk.skillId)
                ? {
                    ...sk,
                    Status: action === "approve" ? "Approved" : "Rejected",
                    RejectReason: action === "reject" ? reason : null,
                    Level: action === "approve" ? "L3" : "L2",
                  }
                : sk
            ),
          }))
        );

        toast.success(res.data.message || "Skills reviewed successfully!", {
          id: toastId,
        });
      } else {
        toast.error("Failed to review skills.", { id: toastId });
      }
    } catch (err) {
      console.error("❌ Error reviewing skills:", err);
      toast.error("Unexpected error", { id: toastId });
    }
  };

  return (
    <SkillContext.Provider
      value={{
        masterSkills,
        employeeSkills,
        requestData,
        reviewSkill,
        setRequestData,
        fetchEmployeeSkills,
        saveEmployeeSkills,
        clearEmployeeSkills,
        downloadSkillMatrix,
        fetchEmployeeRequests,
        isMasterLoading,
        isEmployeeLoading,
        isSaving,
        isRequestLoading,
      }}
    >
      {children}
    </SkillContext.Provider>
  );
};

export const useSkills = () => useContext(SkillContext);
