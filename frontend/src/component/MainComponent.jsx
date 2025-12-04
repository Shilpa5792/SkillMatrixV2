import React, { useEffect, useState } from "react";
import EmployeeSkillTable from "./EmployeeSkillTable";
import EmployeeCertTable from "./EmployeeCertTable";
import RequestList from "./RequestList";

function MainComponent() {
  const tabs = [
    { label: "Add Skills", component: <EmployeeSkillTable /> },
    { label: "Add Certification", component: <EmployeeCertTable /> },
    { label: "Approve", component: <RequestList /> },
  ];
  const [activeTab, setActiveTab] = useState(tabs[0].label);

  return (
    <div
      className="max-w-full max-h-full rounded-xl shadow-lg 
      bg-white text-gray-800 
      dark:bg-gray-900 dark:text-gray-200 
      p-1"
    >
      {/* Tabs */}
      <div className="flex space-x-6 border-b border-gray-300 dark:border-gray-700 px-4">
        {tabs.map((tab) => (
          <button
            key={tab.label}
            onClick={() => setActiveTab(tab.label)}
            className={`pb-1 text-sm font-medium relative transition-colors duration-150
              ${
                activeTab === tab.label
                  ? "text-gray-900 dark:text-blue-400"
                  : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              }`}
          >
            {tab.label}
            {activeTab === tab.label && (
              <span
                className="absolute left-0 right-0 -bottom-[1px] h-[2px] 
                  bg-gray-900 dark:bg-blue-400 rounded-full"
              ></span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="pt-2 max-w-full max-h-screen ">
        {tabs.find((tab) => tab.label === activeTab)?.component}
      </div>
    </div>
  );
}

export default MainComponent;
