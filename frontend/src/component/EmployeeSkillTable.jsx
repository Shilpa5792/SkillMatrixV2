import React, { useState, useEffect } from "react";
import SkillDataTable from "../component/skillDataTable";
import { useAuth } from "../context/AuthContext";
import { useSkills } from "../context/SkillContext";
import toast from "react-hot-toast";

const EmployeeSkillTable = () => {
  const { user } = useAuth();
  const { masterSkills, employeeSkills, fetchEmployeeSkills, isMasterLoading } =
    useSkills();

  const [employeeInfo, setEmployeeInfo] = useState({
    id: user?.employeeId || "",
    email: user?.mail || user?.userPrincipalName || "",
    name: user?.displayName || "",
    dept_name: user?.department || "IFS",
  });

  // ✅ Convert to state
  const [preselectedSkills, setPreselectedSkills] = useState({});

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
    if (employeeSkills.length === 0) {
      handleLoadEmployee();
    }
  }, [user]);

  useEffect(() => {
    const skillsFromBackend = {};

    employeeSkills.forEach((skill) => {
      if (skill.hashId) {
        skillsFromBackend[skill.hashId] = {
          Level: skill.Level || null,
          Status: skill.Status || null,
          RejectReason: skill.RejectReason || null,
        };
      }
    });

    setPreselectedSkills(skillsFromBackend);
  }, [employeeSkills]);

  const handleLoadEmployee = () => {
    if (!employeeInfo.email) {
      toast.error("Employee email is missing.");
      return;
    }
    fetchEmployeeSkills(employeeInfo.email.toLowerCase());
  };

  if (!user) return null;

  return (
    <div className="relative xl:px-0 sm:px-4">
      <div className="rounded-xl bg-white/30 backdrop-blur-md border border-white/40 shadow-lg min-h-[200px] flex items-center justify-center overflow-x-auto">
        {isMasterLoading ? (
          <p className="text-gray-600 text-center animate-pulse">
            Loading skills ...
          </p>
        ) : masterSkills.length > 0 ? (
          <div className="w-full overflow-x-auto">
            <SkillDataTable
              data={masterSkills}
              headers={Object.keys(masterSkills[0])}
              employeeInfo={employeeInfo}
              preselectedSkills={preselectedSkills}
            />
          </div>
        ) : (
          <p className="text-gray-600 text-center">
            No master skills available.
          </p>
        )}
      </div>
    </div>
  );
};

export default EmployeeSkillTable;
