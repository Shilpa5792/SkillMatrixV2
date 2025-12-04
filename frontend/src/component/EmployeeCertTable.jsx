import React, { useState, useEffect } from "react";
import CertDataTable from "./certDataTable";
import { useAuth } from "../context/AuthContext";
import { useCertificates } from "../context/CertificateContext";
import toast from "react-hot-toast";

const EmployeeCertTable = () => {
  const { user } = useAuth();
  const {
    masterCertificates,
    employeeCertificates,
    fetchEmployeeCertificates,
    isMasterLoading,
  } = useCertificates();

  // ✅ Employee info state
  const [employeeInfo, setEmployeeInfo] = useState({
    id: user?.employeeId || "",
    email: user?.mail || user?.userPrincipalName || "",
    name: user?.displayName || "",
    dept_name: user?.department || "IFS",
  });

  // ✅ Preselected certificates from backend
  const [preselectedCertificates, setPreselectedCertificates] = useState({});

  // ✅ On mount or user change
  useEffect(() => {
    if (user) {
      setEmployeeInfo({
        id: user.employeeId || "",
        email: user.mail || user.userPrincipalName || "",
        name: user.displayName || "",
        dept_name: user.department || "IFS",
        managerEmail: user.managerEmail || "",
      });
    }

    if (employeeCertificates.length === 0 && user) {
      handleLoadEmployeeCertificates();
    }
  }, [user]);

  // ✅ Build preselected map when employeeCertificates changes
  useEffect(() => {
    const certsFromBackend = {};

    employeeCertificates.forEach((cert) => {
      if (cert.certHashId) {
        certsFromBackend[cert.certHashId] = {
          approvalStatus: cert.approvalStatus || null,
          certLevel: cert.certLevel || null,
          certProvider: cert.certProvider || null,
          certName: cert.certName || null,
        };
      }
    });

    setPreselectedCertificates(certsFromBackend);
  }, [employeeCertificates]);

  // ✅ Fetch certificates for employee
  const handleLoadEmployeeCertificates = () => {
    if (!employeeInfo.email) {
      toast.error("Employee email is missing.");
      return;
    }
    fetchEmployeeCertificates(employeeInfo.email.toLowerCase());
  };

  if (!user) return null;

  return (
    <div className="relative xl:px-0 sm:px-4">
      <div className="rounded-xl bg-white/30 dark:bg-gray-800/40 backdrop-blur-md border border-white/40 dark:border-gray-700 shadow-lg min-h-[200px] flex items-center justify-center overflow-x-auto">
        {isMasterLoading ? (
          <p className="text-gray-600 text-center animate-pulse">
            Loading certificates ...
          </p>
        ) : masterCertificates.length > 0 ? (
          <div className="w-full overflow-x-auto">
            <CertDataTable
              data={masterCertificates}
              headers={Object.keys(masterCertificates[0])}
              employeeInfo={employeeInfo}
              preselectedCertificates={preselectedCertificates}
            />
          </div>
        ) : (
          <p className="text-gray-600 text-center">
            No master certificates available.
          </p>
        )}
      </div>
    </div>
  );
};

export default EmployeeCertTable;
