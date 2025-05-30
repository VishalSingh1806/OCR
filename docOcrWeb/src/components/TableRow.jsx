import React from "react";
import download from "../assets/icons/download.png";
import { downloadCSV, downloadPDF } from "../utils/download.jsx";
import { toast } from "react-toastify";

const formatDate = (isoString) => {
  if (!isoString) return "N/A";
  const date = new Date(isoString);
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });
};

const TableRow = ({ type, file, index, isSelected, onRowClick }) => {
  if (type === "files") {
    return (
      <tr
        onClick={onRowClick}
        className={`cursor-pointer ${
          isSelected ? "bg-primaryL" : index % 2 == 0 ? "bg-[#e8f0ff]" : ""
        }`}
      >
        <td className="p-2 text-sm md:text-base">{index + 1}</td>
        <td className="p-2 text-sm md:text-base">{file.name}</td>
        <td className="p-2 text-sm md:text-base">
          {(file.size / (1024 * 1024)).toFixed(2)} MB
        </td>
        <td className="p-2 text-sm md:text-base">{file.type || "Unknown"}</td>
        <td
          className={`p-2 text-sm md:text-base ${
            file.status === "Processing" && "text-[#ffa722]"
          } ${file.status === "Success" && "text-[#3c991d]"}`}
        >
          {file.status || "Pending"}
        </td>
      </tr>
    );
  } else {
    return (
      <tr
        onClick={onRowClick}
        className={`cursor-pointer ${
          isSelected ? "bg-primaryL" : index % 2 == 0 ? "bg-[#e8f0ff]" : ""
        }`}
      >
        <td className="p-2 text-sm md:text-base">{index + 1}</td>
        <td className="p-2 text-sm md:text-base">{file.name}</td>
        <td className="p-2 text-sm md:text-base">{file.files.length}</td>
        <td
          className={`p-2 text-sm md:text-base ${
            file.status === "Processing" && "text-[#ffa722]"
          } ${file.status === "Success" && "text-[#3c991d]"}`}
        >
          {file.status}
        </td>
        <td>
          <div className="flex flex-row gap-4 w-fit">
            <button
              className={`${
                file.status === "Success"
                  ? "hover:bg-primaryD-dark"
                  : "opacity-50 cursor-not-allowed"
              }`}
              disabled={file.status !== "Success"}
              onClick={() => {
                if (file.status === "Success") {
                  downloadCSV(file);
                } else {
                  toast.error("Item not ready for download");
                }
              }}
            >
              <div className="flex flex-row gap-1 bg-primaryD rounded items-center px-2 py-1">
                <img src={download} alt="Download" className="w-5 h-5" />
                <div className="text-white text-sm">CSV</div>
              </div>
            </button>
            <button
              className={`${
                file.status === "Success"
                  ? "hover:bg-primaryD-dark"
                  : "opacity-50 cursor-not-allowed"
              }`}
              disabled={file.status !== "Success"}
              onClick={() => {
                if (file.status === "Success") {
                  downloadPDF(file);
                } else {
                  toast.error("Item not ready for download");
                }
              }}
            >
              <div className="flex flex-row gap-1 bg-primaryD rounded items-center px-2 py-1">
                <img src={download} alt="Download" className="w-5 h-5" />
                <div className="text-white text-sm">PDF</div>
              </div>
            </button>
          </div>
        </td>
      </tr>
    );
  }
};

export default TableRow;
