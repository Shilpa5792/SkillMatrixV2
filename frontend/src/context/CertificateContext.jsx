import React, {
  createContext,
  useContext,
  useState,
  useRef,
  useEffect,
} from "react";
import axios from "axios";
import toast from "react-hot-toast";

const CertificateContext = createContext();
const BASE_URL = import.meta.env.VITE_BASE_URL;

export const CertificateProvider = ({ children }) => {
  const [masterCertificates, setMasterCertificates] = useState([]);
  const [otherCertificate, setOtherCertificate] = useState(null);
  const [customCertificates, setCustomCertificates] = useState([]);
  const [employeeCertificates, setEmployeeCertificates] = useState([]);
  const [isMasterLoading, setIsMasterLoading] = useState(false);
  const [isEmployeeLoading, setIsEmployeeLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [requestData, setRequestData] = useState(null);
  const [isRequestLoading, setIsRequestLoading] = useState(false);

  const fetchToastId = useRef(null);
  const saveToastId = useRef(null);

  // 🔹 Fetch master certificates once
  useEffect(() => {
    const fetchMasterCertificates = async () => {
      try {
        setIsMasterLoading(true);
        const response = await axios.get(`${BASE_URL}get_master_certificates`);
        const certificates = response.data || [];

        const otherCert = certificates.find(
          (cert) => cert.certName?.toLowerCase() === "other"
        );

        setOtherCertificate(otherCert || null);
        console.log(otherCert);

        // const filteredCertificates = certificates.filter(
        //   (cert) => cert.certName?.toLowerCase() !== "other"
        // );

        setMasterCertificates(certificates);
      } catch (err) {
        console.error("Failed to fetch master certificates:", err);
        toast.error("Failed to fetch master certificates");
      } finally {
        setIsMasterLoading(false);
      }
    };
    fetchMasterCertificates();
  }, []);

  // 🔹 Fetch employee certificates
  const fetchEmployeeCertificates = async (email) => {
    if (!email) return;

    if (!fetchToastId.current) {
      fetchToastId.current = toast.loading("Loading employee certificates...", {
        duration: Infinity,
      });
    }

    try {
      setIsEmployeeLoading(true);

      const response = await axios.post(
        `${BASE_URL}get_employee_certificates`,
        { email }
      );

      const fetched = response.data.certificates || [];

      if (!otherCertificate?.hashId) {
        console.error("Other certificate hashId not found!");
      }

      // 🔍 Custom certificates = same hashId but NOT named "Other"
      const custom = fetched.filter(
        (c) =>
          c.hashId === otherCertificate?.hashId && c.certificateName !== "Other"
      );

      const original = fetched.filter(
        (c) =>
          c.hashId !== otherCertificate?.hashId || c.certificateName === "Other"
      );

      setEmployeeCertificates(original);
      setCustomCertificates(custom);

      toast.success("Employee certificates loaded successfully!", {
        id: fetchToastId.current,
        duration: 5000,
      });
    } catch (err) {
      if (err.response && err.response.status === 404) {
        toast.error("Previous certificates not found", {
          id: fetchToastId.current,
          duration: 8000,
        });
      } else {
        console.error("Failed to fetch employee certificates:", err);
        setEmployeeCertificates([]);
        setCustomCertificates([]);
        toast.error("Failed to load employee certificates", {
          id: fetchToastId.current,
          duration: 8000,
        });
      }
    } finally {
      setIsEmployeeLoading(false);
      fetchToastId.current = null;
    }
  };

  // 🔹 Save employee certificates
  const saveEmployeeCertificates = async (
    employeeInfo,
    selectedCertificates,
    managerEmail = ""
  ) => {
    if (!employeeInfo?.email) {
      toast.error("Employee Email is required", { duration: 8000 });
      return;
    }

    if (!saveToastId.current) {
      saveToastId.current = toast.loading("Saving employee certificates...", {
        duration: Infinity,
      });
    }

    try {
      setIsSaving(true);

      // ✅ Send the selected certificates directly
      await axios.post(
        `${BASE_URL}save_employee_certificate`,
        {
          email: employeeInfo.email.toLowerCase(),
          managerEmail:
            employeeInfo.managerEmail?.toLowerCase() ||
            managerEmail?.toLowerCase() ||
            "",
          certificates: selectedCertificates.map((cert) => ({
            certHashId: cert.hashId,
            certProvider: cert.certProvider,
            certName: cert.certName,
            certLevel: cert.certLevel,
            validYears: cert.validYears,
            yearAchieved: cert.yearAchieved || null,
            expiryDate: cert.expiryDate || null,
            verified: cert.verified ?? false,
            certIdExternal: cert.certIdExternal || null,
          })),
        },
        { headers: { "Content-Type": "application/json" } }
      );

      // ✅ Refresh employee certificate list
      await fetchEmployeeCertificates(employeeInfo.email);

      toast.success("Employee certificates saved successfully!", {
        id: saveToastId.current,
        duration: 5000,
      });
    } catch (error) {
      console.error("Failed to save employee certificates:", error);
      toast.error(
        error.response?.data?.error ||
          "Failed to save employee certificates. Please try again.",
        { id: saveToastId.current, duration: 8000 }
      );
    } finally {
      setIsSaving(false);
      saveToastId.current = null;
    }
  };

  const clearEmployeeCertificates = () => {
    setEmployeeCertificates([]);
  };

  // 🔹 Fetch pending certificate requests (for review)
  const fetchCertificateRequests = async (userEmail) => {
    const toastId = toast.loading("Fetching certificate requests...", {
      duration: Infinity,
    });

    setIsRequestLoading(true);
    try {
      if (!userEmail) {
        toast.error("User email is required", { id: toastId, duration: 5000 });
        setIsRequestLoading(false);
        return;
      }

      const res = await axios.get(`${BASE_URL}get_certificate_requests`, {
        params: { email: userEmail },
      });

      if (res.status === 200) {
        setRequestData(res.data);
        toast.success("Certificate requests fetched successfully!", {
          id: toastId,
          duration: 3000,
        });
      } else {
        toast.error("Failed to fetch certificate requests.", {
          id: toastId,
          duration: 5000,
        });
      }
    } catch (error) {
      console.error("Error fetching certificate requests:", error);
      toast.error(
        error?.response?.data?.error ||
          "An unexpected error occurred while fetching certificate requests.",
        { id: toastId, duration: 5000 }
      );
    } finally {
      setIsRequestLoading(false);
    }
  };

  // 🔹 Review (Approve / Reject) certificates
  const reviewCertificates = async (
    certIds,
    approvedByEmail,
    action,
    reason
  ) => {
    const toastId = toast.loading(
      action === "approve"
        ? "Approving certificates..."
        : "Rejecting certificates..."
    );

    try {
      if (!certIds?.length || !approvedByEmail || !action) {
        toast.error("Missing required fields.", { id: toastId });
        return;
      }

      const payload = {
        approvedByEmail,
        action,
        reason: action === "reject" ? reason || "No reason provided" : null,
        certificates: certIds.map((id) => ({ empCertId: id })),
      };

      const res = await axios.post(`${BASE_URL}review_certificate`, payload);

      if (res.status === 200) {
        // ✅ Optimistic UI update
        setRequestData((prev) =>
          prev.map((emp) => ({
            ...emp,
            certificates: emp.certificates?.map((c) =>
              certIds.includes(c.certId)
                ? {
                    ...c,
                    Status: action === "approve" ? "Approved" : "Rejected",
                    RejectReason: action === "reject" ? reason : null,
                    verified: action === "approve",
                  }
                : c
            ),
          }))
        );

        toast.success(
          res.data.message || "Certificates reviewed successfully!",
          {
            id: toastId,
          }
        );
      } else {
        toast.error("Failed to review certificates.", { id: toastId });
      }
    } catch (err) {
      console.error("❌ Error reviewing certificates:", err);
      toast.error("Unexpected error", { id: toastId });
    }
  };

  const downloadCertificateMatrix = async () => {
    const toastId = toast.loading("Preparing Certificates master file...", {
      duration: Infinity,
    });

    try {
      const response = await axios.get(`${BASE_URL}get_master_file`, {
        params: { type: "certificates" }, // always certificates
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

      const filename = `Master_Certificates${ext}`;

      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.success("Certificates master file downloading!", {
        id: toastId,
        duration: 5000,
      });
    } catch (error) {
      console.error(error);
      toast.error("Failed to download Certificates master file", {
        id: toastId,
        duration: 8000,
      });
    }
  };

  return (
    <CertificateContext.Provider
      value={{
        masterCertificates,
        employeeCertificates,
        requestData,
        otherCertificate,
        customCertificates,
        setCustomCertificates,
        reviewCertificates,
        setRequestData,
        fetchEmployeeCertificates,
        saveEmployeeCertificates,
        clearEmployeeCertificates,
        fetchCertificateRequests,
        downloadCertificateMatrix,
        isMasterLoading,
        isEmployeeLoading,
        isSaving,
        isRequestLoading,
      }}
    >
      {children}
    </CertificateContext.Provider>
  );
};

export const useCertificates = () => useContext(CertificateContext);
