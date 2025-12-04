import React, { useState, useEffect, useRef, useMemo } from "react";
import {
  FaTimesCircle,
  FaFilter,
  FaSave,
  FaDownload,
  FaSearch,
} from "react-icons/fa";
import { SiTarget } from "react-icons/si";
import { getHeaderName } from "../helper/utility";
import { FaQuestion } from "react-icons/fa6";
import LevelDetailModal from "./LevelDetailModal";
import { useAuth } from "../context/AuthContext";
import { useSkills } from "../context/SkillContext";

const SkillDataTable = ({ data, headers, employeeInfo, preselectedSkills }) => {
  const { setUser } = useAuth();
  const [filters, setFilters] = useState({});
  const [selectedRadios, setSelectedRadios] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(20);
  const [activeFilterHeader, setActiveFilterHeader] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [open, setOpen] = useState(false);
  const [modalLevels, setModalLevels] = useState(null);
  const [emailError, setEmailError] = useState("");

  const [managerModalOpen, setManagerModalOpen] = useState(false);
  const [managerEmail, setManagerEmail] = useState("");
  const [pendingExpertSkills, setPendingExpertSkills] = useState([]);
  const [showUnselectedOnly, setShowUnselectedOnly] = useState(false);

  const tableRef = useRef(null);
  const filterDropdownRef = useRef(null);

  const preserveScroll = (callback) => {
    const container = tableRef.current;
    const scrollTop = container ? container.scrollTop : 0;

    callback(); // this triggers sorting/re-render

    requestAnimationFrame(() => {
      if (container) container.scrollTop = scrollTop;
    });
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        filterDropdownRef.current &&
        !filterDropdownRef.current.contains(event.target)
      ) {
        setActiveFilterHeader(null);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [setActiveFilterHeader]);

  const handleSaveClick = () => {
    const newExpertSkills = processedData.filter((row) => {
      const selected = selectedRadios[row.hashId];
      return (
        selected && // a selection exists
        selected.Level === "L3" && // Expert level selected
        (!preselectedSkills || // check if it's newly selected
          !preselectedSkills[row.hashId] ||
          preselectedSkills[row.hashId].Level !== "L3")
      );
    });

    if (newExpertSkills.length > 0 && employeeInfo.managerEmail === "") {
      setPendingExpertSkills(newExpertSkills);
      setManagerModalOpen(true);
    } else {
      saveEmployeeSkills(employeeInfo, processedData, selectedRadios);
    }
  };

  const confirmSaveWithManager = () => {
    if (!managerEmail) {
      setEmailError("Manager email is required");
      return;
    }
    if (managerEmail === employeeInfo.email) {
      setEmailError("Manager email cannot be your own email");
      return;
    }
    // Optionally, you can attach the manager email to the payload
    setUser((prev) => ({ ...prev, managerEmail: managerEmail }));
    saveEmployeeSkills(
      employeeInfo,
      processedData,
      selectedRadios,
      managerEmail
    );

    setManagerModalOpen(false);
    setManagerEmail("");
    setPendingExpertSkills([]);
  };

  const { saveEmployeeSkills, isSaving, downloadSkillMatrix } = useSkills();

  const cleanedData = data.filter((row) =>
    Object.values(row).some((val) => val && val.toString().trim() !== "")
  );

  const fixedHeaderOrder = [
    "Category",
    "Sub-Category",
    "Sub-Sub-Category",
    "Tools",
    "L1",
    "L2",
    "L3",
  ];

  const columnWidths = {
    Category: "w-[15%]",
    "Sub-Category": "w-[20%]",
    "Sub-Sub-Category": "w-[20%]",
    Tools: "w-[25%]",
    L1: "w-[6%]",
    L2: "w-[6%]",
    L3: "w-[6%]",
  };

  useEffect(() => {
    const initialFilters = {};
    headers.forEach((header) => {
      initialFilters[header] = [];
    });
    setFilters(initialFilters);
  }, [headers, data]);

  useEffect(() => {
    if (
      data.length > 0 &&
      preselectedSkills &&
      Object.keys(preselectedSkills).length > 0
    ) {
      // Ensure we keep full skill info: Level, Status, RejectReason
      const updatedSelections = {};

      data.forEach((item) => {
        const skill = preselectedSkills[item.hashId];
        if (skill) {
          updatedSelections[item.hashId] = {
            Level: skill.Level || null,
            Status: skill.Status || null,
            RejectReason: skill.RejectReason || null,
          };
        }
      });

      setSelectedRadios(updatedSelections);
    }
  }, [data, preselectedSkills]);

  // Helper to find actual data key from display header
  const findDataKey = (displayHeader, dataKeys) => {
    // Try exact match first
    if (dataKeys.includes(displayHeader)) {
      return displayHeader;
    }
    // Try common variations
    if (displayHeader === "Sub-Category") {
      return (
        dataKeys.find(
          (key) =>
            key === "Sub Category" ||
            key === "Sub-Category" ||
            key.toLowerCase() === "sub category" ||
            key.toLowerCase() === "sub-category"
        ) || displayHeader
      );
    } else if (displayHeader === "Sub-Sub-Category") {
      return (
        dataKeys.find(
          (key) =>
            key === "Sub Sub Category" ||
            key === "Sub-Sub-Category" ||
            key.toLowerCase() === "sub sub category" ||
            key.toLowerCase() === "sub-sub-category"
        ) || displayHeader
      );
    }
    return displayHeader;
  };

  // Build mapping from display headers to actual data keys
  const headerToDataKeyMap = useMemo(() => {
    const map = {};
    if (cleanedData.length > 0) {
      const firstRow = cleanedData[0];
      const dataKeys = Object.keys(firstRow);

      // Map display headers to actual data keys
      fixedHeaderOrder.forEach((displayHeader) => {
        map[displayHeader] = findDataKey(displayHeader, dataKeys);
      });
    }
    return map;
  }, [cleanedData]);

  // Helper to normalize header names for data access
  const getDataKey = (header) => {
    return headerToDataKeyMap[header] || header;
  };

  // Get actual data keys for search
  const searchDataKeys = useMemo(() => {
    if (cleanedData.length === 0)
      return ["Category", "Sub Category", "Sub Sub Category", "Tools"];
    const firstRow = cleanedData[0];
    const dataKeys = Object.keys(firstRow);
    return [
      findDataKey("Category", dataKeys),
      findDataKey("Sub-Category", dataKeys),
      findDataKey("Sub-Sub-Category", dataKeys),
      findDataKey("Tools", dataKeys),
    ];
  }, [cleanedData]);

  // Get actual data keys for sorting
  const sortDataKeys = useMemo(() => {
    if (cleanedData.length === 0)
      return ["Category", "Sub Category", "Sub Sub Category", "Tools"];
    const firstRow = cleanedData[0];
    const dataKeys = Object.keys(firstRow);
    return [
      findDataKey("Category", dataKeys),
      findDataKey("Sub-Category", dataKeys),
      findDataKey("Sub-Sub-Category", dataKeys),
      findDataKey("Tools", dataKeys),
    ];
  }, [cleanedData]);

  // Sorting order (Category → Sub Category → Sub Sub Category → Tools)
  const sortByCategory = (a, b) => {
    for (let field of sortDataKeys) {
      const valA = (a[field] || "").toString().toLowerCase();
      const valB = (b[field] || "").toString().toLowerCase();
      if (valA < valB) return -1;
      if (valA > valB) return 1;
    }
    return 0;
  };

  useEffect(() => {
    if (searchTerm) {
      setFilters({});
    }
  }, [searchTerm]);

  const processedData = useMemo(() => {
    let enriched = cleanedData.map((row) => {
      const selected = selectedRadios[row.hashId] || {};
      return {
        ...row,
        selectedLevel: selected.Level || null,
        RejectReason: selected.RejectReason || null,
        Status: selected.Status || null,
      };
    });

    // ✅ Always include selected skills
    const selected = enriched.filter((row) => row.selectedLevel);

    // ✅ Apply filters (only if NOT searching)
    let filtered = [];
    const hasActiveFilters = Object.values(filters).some(
      (vals) => vals && vals.length > 0
    );

    if (!searchTerm && hasActiveFilters) {
      filtered = enriched.filter((row) => {
        return Object.entries(filters).every(([header, selectedVals]) => {
          if (!selectedVals || selectedVals.length === 0) return true;
          const dataKey = getDataKey(header);
          return selectedVals.includes(row[dataKey]);
        });
      });
    }

    // ✅ Apply search (skips filters)
    let searched = [];
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      searched = enriched.filter((row) => {
        const fields = searchDataKeys
          .map((key) => row[key])
          .map((f) => (f ? f.toString().toLowerCase() : ""))
          .join(" ");
        return fields.includes(searchLower);
      });
    }

    // ✅ Decide what to include
    let rest = [];
    if (searchTerm) {
      rest = searched; // 🚫 skip filters completely during search
    } else if (hasActiveFilters) {
      rest = filtered;
    } else {
      // ❌ No search & no filters → nothing
      rest = [];
    }

    // ✅ Combine: always include selected
    const combined = [...selected, ...rest].filter(
      (row, index, self) =>
        index === self.findIndex((r) => r.hashId === row.hashId)
    );

    // ✅ Sort: selected first, then rest
    const selectedSorted = selected.sort(sortByCategory);
    const restSorted = rest
      .filter((row) => !selected.find((s) => s.hashId === row.hashId))
      .sort(sortByCategory);

    let finalData = [...selectedSorted, ...restSorted];

    // ✅ Filter to show only unselected skills if toggle is active
    if (showUnselectedOnly) {
      finalData = finalData.filter((row) => !row.selectedLevel);
    }

    return finalData;
  }, [
    cleanedData,
    selectedRadios,
    searchTerm,
    filters,
    sortDataKeys,
    searchDataKeys,
    getDataKey,
    showUnselectedOnly,
  ]);

  // Pagination
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedData = processedData.slice(
    startIndex,
    startIndex + itemsPerPage
  );
  const totalPages = Math.max(
    1,
    Math.ceil(processedData.length / itemsPerPage)
  );

  // Build nested map once using actual data keys
  const categoryMap = useMemo(() => {
    const map = {};
    if (cleanedData.length === 0) return map;

    // Get actual data keys from first row
    const firstRow = cleanedData[0];
    const categoryKey =
      Object.keys(firstRow).find(
        (key) => key === "Category" || key.toLowerCase() === "category"
      ) || "Category";
    const subCategoryKey =
      Object.keys(firstRow).find(
        (key) =>
          key === "Sub Category" ||
          key === "Sub-Category" ||
          key.toLowerCase() === "sub category" ||
          key.toLowerCase() === "sub-category"
      ) || "Sub Category";
    const subSubCategoryKey =
      Object.keys(firstRow).find(
        (key) =>
          key === "Sub Sub Category" ||
          key === "Sub-Sub-Category" ||
          key.toLowerCase() === "sub sub category" ||
          key.toLowerCase() === "sub-sub-category"
      ) || "Sub Sub Category";
    const toolsKey =
      Object.keys(firstRow).find(
        (key) => key === "Tools" || key.toLowerCase() === "tools"
      ) || "Tools";

    cleanedData.forEach((row) => {
      const cat = row[categoryKey] || "Other";
      const subCat = row[subCategoryKey] || "Other";
      const subSubCat = row[subSubCategoryKey] || "Other";
      const tool = row[toolsKey] || "Other";

      if (!map[cat]) map[cat] = {};
      if (!map[cat][subCat]) map[cat][subCat] = {};
      if (!map[cat][subCat][subSubCat]) map[cat][subCat][subSubCat] = [];
      if (!map[cat][subCat][subSubCat].includes(tool)) {
        map[cat][subCat][subSubCat].push(tool);
      }
    });
    return map;
  }, [cleanedData]);

  // Modified getUniqueValues: context aware
  const getUniqueValues = (header) => {
    // Normalize header name: convert "Sub-Category" -> "Sub Category", etc.
    const normalizeHeader = (h) => {
      if (h === "Sub-Category") return "Sub Category";
      if (h === "Sub-Sub-Category") return "Sub Sub Category";
      return h;
    };

    const normalizedHeader = normalizeHeader(header);

    if (header === "Category") {
      return Object.keys(categoryMap);
    }

    if (normalizedHeader === "Sub Category") {
      // Get selected categories from filter (stored as "Category")
      const selectedCats = filters["Category"]?.length
        ? filters["Category"]
        : Object.keys(categoryMap);

      const subCats = new Set();
      selectedCats.forEach((cat) => {
        Object.keys(categoryMap[cat] || {}).forEach((sub) => subCats.add(sub));
      });
      return Array.from(subCats).sort((a, b) =>
        a.toLowerCase().localeCompare(b.toLowerCase())
      );
    }

    if (normalizedHeader === "Sub Sub Category") {
      const selectedCats = filters["Category"]?.length
        ? filters["Category"]
        : Object.keys(categoryMap);

      // Filter key is "Sub-Category" (from fixedHeaderOrder)
      const selectedSubs = filters["Sub-Category"]?.length
        ? filters["Sub-Category"]
        : [];

      const subSubs = new Set();
      selectedCats.forEach((cat) => {
        Object.keys(categoryMap[cat] || {}).forEach((sub) => {
          if (!selectedSubs.length || selectedSubs.includes(sub)) {
            Object.keys(categoryMap[cat][sub] || {}).forEach((ss) =>
              subSubs.add(ss)
            );
          }
        });
      });
      return Array.from(subSubs).sort((a, b) =>
        a.toLowerCase().localeCompare(b.toLowerCase())
      );
    }

    if (header === "Tools") {
      const selectedCats = filters["Category"]?.length
        ? filters["Category"]
        : Object.keys(categoryMap);

      // Filter keys are from fixedHeaderOrder (with hyphens)
      const selectedSubs = filters["Sub-Category"]?.length
        ? filters["Sub-Category"]
        : [];

      const selectedSubSubs = filters["Sub-Sub-Category"]?.length
        ? filters["Sub-Sub-Category"]
        : [];

      const tools = new Set();
      selectedCats.forEach((cat) => {
        Object.keys(categoryMap[cat] || {}).forEach((sub) => {
          if (!selectedSubs.length || selectedSubs.includes(sub)) {
            Object.keys(categoryMap[cat][sub] || {}).forEach((ss) => {
              if (!selectedSubSubs.length || selectedSubSubs.includes(ss)) {
                (categoryMap[cat][sub][ss] || []).forEach((tool) =>
                  tools.add(tool)
                );
              }
            });
          }
        });
      });
      return Array.from(tools).sort((a, b) =>
        a.toLowerCase().localeCompare(b.toLowerCase())
      );
    }

    // fallback
    const values = cleanedData
      .map((row) => row[normalizedHeader])
      .filter(Boolean);
    return [...new Set(values)].sort((a, b) =>
      a.toString().toLowerCase().localeCompare(b.toString().toLowerCase())
    );
  };

  const isRadioHeader = (header) => ["L1", "L2", "L3"].includes(header);

  const toggleFilterValue = (header, value) => {
    setFilters((prev) => {
      const current = prev[header] || [];
      let updated;
      if (current.includes(value)) {
        updated = current.filter((v) => v !== value);
      } else {
        updated = [...current, value];
      }

      const newFilters = { ...prev, [header]: updated };

      // Clear dependent filters when parent filter changes
      if (header === "Category") {
        // Clear Sub-Category, Sub-Sub-Category, and Tools filters
        newFilters["Sub-Category"] = [];
        newFilters["Sub-Sub-Category"] = [];
        newFilters["Tools"] = [];
      } else if (header === "Sub-Category") {
        // Clear Sub-Sub-Category and Tools filters
        newFilters["Sub-Sub-Category"] = [];
        newFilters["Tools"] = [];
      } else if (header === "Sub-Sub-Category") {
        // Clear Tools filter
        newFilters["Tools"] = [];
      }

      return newFilters;
    });

    setCurrentPage(1);
  };

  const toggleSelectAll = (header, allValues) => {
    setFilters((prev) => {
      const current = prev[header] || [];
      const allSelected = current.length === allValues.length;
      return { ...prev, [header]: allSelected ? [] : allValues };
    });
  };

  const getIconColor = (row) => {
    if (!selectedRadios[row.hashId]) return "text-transparent"; // no icon

    switch (selectedRadios[row.hashId]?.Status) {
      case "Pending":
        return "text-yellow-400 dark:text-yellow-300";
      case "Approved":
        return "text-green-500 dark:text-green-400";
      case "Pre-Approved":
        return "text-green-500 dark:text-green-400";
      case "Rejected":
        return "text-red-600 dark:text-red-400";
      default:
        return "text-gray-400 dark:text-gray-100"; // fallback for unknown status
    }
  };

  return (
    <div className="flex flex-col h-[80vh] p-2 bg-white dark:bg-gray-900 shadow rounded-lg border border-gray-200 dark:border-gray-700">
      {/* Header + Reset */}
      <div className="flex flex-col md:flex-row items-center mb-4 gap-2 w-full">
        <h2 className="text-lg font-bold md:flex-none text-gray-800 dark:text-slate-100">
          Employee Skills
        </h2>

        {/* Centered search bar */}
        <div className="flex flex-1 justify-center px-2 w-full md:w-auto">
          <div className="relative w-full max-w-lg">
            {/* Search Icon */}
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <FaSearch className="text-blue-500 w-4 h-4" />
            </div>

            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search skill to get started..."
              className="block w-full pl-10 pr-3 py-3 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 
            focus:ring-blue-400 focus:border-blue-400 hover:border-gray-400
            dark:bg-slate-800 dark:border-slate-600 dark:text-slate-100 dark:placeholder-slate-400 dark:focus:ring-blue-400 dark:focus:border-blue-400"
            />
          </div>
        </div>

        {/* Buttons aligned right */}
        <div className="flex flex-wrap md:flex-nowrap items-center gap-2 md:flex-none w-full md:w-auto justify-center md:justify-end">
          {/* Toggle Button to Hide Selected Skills */}
          <button
            type="button"
            onClick={() => {
              setShowUnselectedOnly(!showUnselectedOnly);
              setCurrentPage(1); // Reset to first page when toggling
            }}
            className={`flex items-center gap-2 px-3 py-1.5 border font-medium rounded-lg transition shadow-md w-full md:w-auto justify-center ${
              showUnselectedOnly
                ? "bg-blue-500 text-white hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700 border-blue-600 dark:border-blue-700"
                : "bg-white/20 backdrop-blur-md border-white/30 text-gray-700 hover:bg-white/30 hover:text-gray-900 dark:bg-slate-800 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            {showUnselectedOnly
              ? "Show selected skills"
              : "Hide selected skills"}
          </button>
          <button
            onClick={() => downloadSkillMatrix()}
            className="flex items-center gap-2 px-2 py-1 border font-medium rounded-lg transition shadow-md
          bg-white/20 backdrop-blur-md border-white/30 text-green-600 hover:bg-white/30 hover:text-green-700
          dark:bg-slate-800 dark:border-slate-600 dark:text-green-400 dark:hover:bg-slate-700 dark:hover:text-green-300 w-full md:w-auto justify-center"
          >
            <FaDownload className="w-4 h-4" />
            Skill Matrix
          </button>
          {/* <button
            onClick={() =>
              saveEmployeeSkills(employeeInfo, processedData, selectedRadios)
            }
            disabled={isSaving}
            className={`flex items-center gap-2 px-2 py-1 border font-medium rounded-lg transition shadow-md w-full md:w-auto justify-center ${
              isSaving
                ? "bg-gray-200 text-gray-500 cursor-not-allowed dark:bg-slate-700 dark:text-slate-400"
                : "bg-white/20 backdrop-blur-md border-white/30 text-blue-600 hover:bg-white/30 hover:text-blue-700 dark:bg-slate-800 dark:border-slate-600 dark:text-blue-400 dark:hover:bg-slate-700 dark:hover:text-blue-300"
            }`}
          >
            <FaSave className="w-4 h-4" />
            {isSaving ? "Saving..." : "Save"}
          </button> */}
          <button
            onClick={handleSaveClick}
            disabled={isSaving}
            className={`flex items-center gap-2 px-2 py-1 border font-medium rounded-lg transition shadow-md w-full md:w-auto justify-center ${
              isSaving
                ? "bg-gray-200 text-gray-500 cursor-not-allowed dark:bg-slate-700 dark:text-slate-400"
                : "bg-white/20 backdrop-blur-md border-white/30 text-blue-600 hover:bg-white/30 hover:text-blue-700 dark:bg-slate-800 dark:border-slate-600 dark:text-blue-400 dark:hover:bg-slate-700 dark:hover:text-blue-300"
            }`}
          >
            <FaSave className="w-4 h-4" />
            {isSaving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>

      {/* Data table */}
      <div ref={tableRef} className="flex-1 h-[370px] overflow-auto relative ">
        {" "}
        {/* Use "hide-scrollbar" here to remove the scrollbar */}
        <table className="w-full border border-gray-200 dark:border-slate-700 rounded-lg table-fixed">
          <thead className="bg-gray-100 dark:bg-slate-800 sticky top-0 z-10">
            <tr>
              {fixedHeaderOrder.map((header) => {
                const showFilterIcon = [
                  "Category",
                  "Sub-Category",
                  "Sub-Sub-Category",
                  "Tools",
                ].includes(header);

                return (
                  <th
                    key={header}
                    className={`relative px-4 py-2 text-center text-sm font-medium text-gray-700 dark:text-slate-200 h-12 cursor-pointer ${
                      columnWidths[header] || "w-auto"
                    }`}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (showFilterIcon) setActiveFilterHeader(header);
                    }}
                  >
                    {/* Center header and filter icon */}
                    <div className="flex justify-center items-center gap-1">
                      <span>{getHeaderName(header)}</span>
                      {showFilterIcon &&
                        (() => {
                          const selectedVals = filters[header] || [];
                          const uniqueVals = getUniqueValues(header);
                          const allSelected =
                            selectedVals.length === uniqueVals.length &&
                            uniqueVals.length > 0;
                          const hasActiveFilter =
                            selectedVals.length > 0 && !allSelected;
                          const isDropdownOpen = activeFilterHeader === header;

                          let iconColor = "text-gray-400 dark:text-slate-400"; // default gray
                          if (isDropdownOpen) {
                            iconColor = "text-blue-500"; // blue when dropdown is open
                          } else if (hasActiveFilter) {
                            iconColor = "text-green-500 dark:text-green-400"; // green when filter is active (not all selected)
                          }
                          // If allSelected, keep it gray (same as no filter)

                          return <FaFilter size={12} className={iconColor} />;
                        })()}
                    </div>

                    {activeFilterHeader === header && showFilterIcon && (
                      <div
                        ref={filterDropdownRef}
                        className="absolute z-10 truncate max-w-[200%] bg-white dark:bg-slate-900 border rounded shadow-lg px-2 max-h-64 overflow-y-auto border-gray-200 dark:border-slate-700"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="flex justify-between items-center text-center sticky top-0 bg-white dark:bg-slate-900 z-20 pt-2">
                          <span className="font-medium text-sm text-gray-700 dark:text-slate-200">
                            {header} Filter
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveFilterHeader(null);
                            }}
                            className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm"
                          >
                            ✕
                          </button>
                        </div>

                        {(() => {
                          const uniqueVals = getUniqueValues(header);
                          const selectedVals = filters[header] || [];
                          const allSelected =
                            selectedVals.length === uniqueVals.length;

                          return (
                            <div className="flex flex-col gap-1 text-sm text-gray-700 dark:text-slate-200 mt-2">
                              <label className="flex items-center gap-2">
                                <input
                                  type="checkbox"
                                  checked={allSelected}
                                  onChange={() =>
                                    toggleSelectAll(header, uniqueVals)
                                  }
                                />
                                Select All
                              </label>
                              {uniqueVals.map((val, idx) => (
                                <label
                                  key={idx}
                                  className="flex items-center gap-2"
                                >
                                  <input
                                    type="checkbox"
                                    checked={selectedVals.includes(val)}
                                    onChange={() =>
                                      toggleFilterValue(header, val)
                                    }
                                  />
                                  {val}
                                </label>
                              ))}
                            </div>
                          );
                        })()}
                      </div>
                    )}
                  </th>
                );
              })}

              <th className="w-[5%] px-4 py-2 text-sm font-medium text-gray-700 dark:text-slate-200 h-12 text-center">
                &nbsp;
              </th>
              <th className="w-[8%] px-4 py-2 text-sm font-medium text-gray-700 dark:text-slate-200 h-12 text-center">
                Action
              </th>
            </tr>
          </thead>

          <tbody>
            {paginatedData.length > 0 ? (
              paginatedData.map((row) => (
                <tr
                  key={row.hashId}
                  className="border-b border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 h-12 align-middle"
                >
                  {fixedHeaderOrder.map((header) => {
                    const dataKey = getDataKey(header);
                    return (
                      <td
                        key={header}
                        className={`px-4 py-2 text-gray-700 dark:text-slate-200 truncate text-ellipsis align-middle ${
                          columnWidths[header] || "w-auto"
                        }`}
                        title={row[dataKey]}
                      >
                        {isRadioHeader(header) ? (
                          <div className="flex items-center justify-center">
                            <input
                              type="radio"
                              name={`level-radio-${row.hashId}`}
                              value={header}
                              checked={
                                selectedRadios[row.hashId]?.Level === header
                              }
                              onChange={() =>
                                preserveScroll(() => {
                                  setSelectedRadios((prev) => ({
                                    ...prev,
                                    [row.hashId]: { Level: header },
                                  }));
                                })
                              }
                              className="cursor-pointer accent-blue-600 dark:accent-blue-400 focus:ring-2 focus:ring-blue-400 dark:focus:ring-blue-500"
                            />
                          </div>
                        ) : (
                          row[dataKey]?.slice(0, 25) +
                          (row[dataKey]?.length > 25 ? "..." : "")
                        )}
                      </td>
                    );
                  })}

                  <td className="text-center">
                    <button
                      title="View Level Requirement"
                      onClick={() => {
                        setModalLevels({
                          L1: row["L1"] || "-",
                          L2: row["L2"] || "-",
                          L3: row["L3"] || "-",
                        });
                        setOpen(true);
                      }}
                      className="p-2 rounded-full text-blue-500 hover:bg-blue-100 dark:text-blue-400 dark:hover:bg-slate-700 transition-colors duration-200"
                    >
                      <FaQuestion className="h-4" />
                    </button>
                  </td>

                  <td className="px-4 py-2">
                    <div className="flex items-center justify-center gap-5">
                      <div className="h-5 w-5 flex items-center justify-center">
                        {selectedRadios[row.hashId] && (
                          <SiTarget
                            className={"h-4 w-4 " + getIconColor(row)}
                            title={
                              selectedRadios[row.hashId]?.Status === "Rejected"
                                ? "Rejection Reason:\n" +
                                  selectedRadios[row.hashId]?.RejectReason
                                : selectedRadios[row.hashId]?.Status ||
                                  "New Skill"
                            }
                          />
                        )}
                      </div>

                      {selectedRadios[row.hashId] ? (
                        <button
                          title="Clear selection"
                          onClick={() =>
                            preserveScroll(() => {
                              setSelectedRadios((prev) => {
                                const updated = { ...prev };
                                delete updated[row.hashId];
                                return updated;
                              });
                            })
                          }
                          className=" rounded-full text-red-600 hover:bg-red-100 dark:text-red-400 dark:hover:bg-slate-700 transition-colors duration-200"
                        >
                          <FaTimesCircle className="w-5 h-5 " />
                        </button>
                      ) : (
                        <span> </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr className="h-12">
                <td
                  colSpan={fixedHeaderOrder.length + 2}
                  className="text-center py-6 text-gray-500 dark:text-slate-400"
                >
                  {showUnselectedOnly
                    ? "No unselected skills found. All skills are selected or no skills match your filters."
                    : "Start by Searching the Tool, Category or Sub-Category"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <LevelDetailModal
        open={open}
        onClose={() => setOpen(false)}
        title="Level Details"
        levels={modalLevels || { L1: "-", L2: "-", L3: "-" }}
      />

      {managerModalOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-96 p-4 relative">
            <h3 className="text-lg font-semibold mb-3">
              Manager Approval Required
            </h3>
            <p className="mb-2 text-sm text-gray-700 dark:text-gray-300">
              The following newly selected Expert skills require manager
              approval:
            </p>
            <ul className="mb-2 list-disc list-inside text-sm text-gray-700 dark:text-gray-300 max-h-40 overflow-auto">
              {pendingExpertSkills.slice(0, 5).map((row, idx) => (
                <li key={row.hashId}>
                  {row.Tools}
                  {idx === 4 && pendingExpertSkills.length > 5 && (
                    <span className="ml-1 text-gray-500 dark:text-gray-400 italic">
                      +{pendingExpertSkills.length - 5} more
                    </span>
                  )}
                </li>
              ))}
            </ul>

            <input
              type="email"
              value={managerEmail}
              onChange={(e) => setManagerEmail(e.target.value)}
              placeholder="Manager Email"
              className={`w-full border rounded-lg p-2 text-sm mb-2 dark:bg-gray-700 dark:text-gray-200 ${
                emailError
                  ? "border-red-500 focus:ring-red-500"
                  : "border-gray-300 focus:ring-blue-500 dark:border-gray-600"
              }`}
            />
            {emailError && (
              <p className="text-red-500 text-xs mb-2">{emailError}</p>
            )}

            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setManagerModalOpen(false);
                  setEmailError("");
                }}
                className="px-4 py-2 rounded bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                  if (!managerEmail || !emailRegex.test(managerEmail)) {
                    setEmailError("Please enter a valid email");
                    return;
                  }
                  setEmailError("");
                  confirmSaveWithManager();
                }}
                className="px-4 py-2 rounded bg-blue-500 hover:bg-blue-600 text-white text-sm"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pagination */}
      <div className="flex flex-col md:flex-row justify-between items-center gap-4 mt-4">
        <div className="flex items-center gap-2">
          <label
            htmlFor="itemsPerPage"
            className="text-sm text-gray-700 dark:text-slate-200"
          >
            Items per page:
          </label>
          <select
            id="itemsPerPage"
            value={itemsPerPage}
            onChange={(e) => {
              setItemsPerPage(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="border rounded px-2 py-1 text-sm text-gray-700 dark:text-slate-200 bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600"
          >
            {[5, 10, 20, 50, 100].map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-4">
          <button
            disabled={currentPage === 1}
            onClick={() => setCurrentPage((p) => p - 1)}
            className="px-3 py-1 bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-slate-200 rounded disabled:opacity-50"
          >
            Prev
          </button>
          <span className="text-sm text-gray-700 dark:text-slate-200">
            Page {currentPage} of {totalPages}
          </span>
          <button
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage((p) => p + 1)}
            className="px-3 py-1 bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-slate-200 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default SkillDataTable;
