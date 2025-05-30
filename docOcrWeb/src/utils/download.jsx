import { jsPDF } from "jspdf";
import "jspdf-autotable";
import autoTable from "jspdf-autotable";

const headers = [
  "Sr. No.",
  "Agency",
  "Location",
  "State",
  "Category of Plastic Waste (I / II / III)",
  // Delivery Challan
  "Vehicle Number",
  "Date",
  "No.",
  "Transporter Name",
  "Qty",
  "Consignor",
  "Consignee",
  "From State",
  "To State",
  // Invoice section
  "Invoice Date",
  "Invoice Number",
  "Quantity",
  "Material Name",
  // Loading Weigh Bill section
  "Available?",
  "Date",
  "No.",
  "Name",
  "State",
  "Vehicle Number",
  "Net Weight (kg)",
  // E-Way bill section
  "Available?",
  "Generated Date",
  "No.",
  "Qty",
  "Valid Upto",
  "From State",
  "To State",
  "Categorisation of Plastic Waste",
  // LR section
  "Available?",
  "Date",
  "No.",
  "Transporter Name",
  "Qty",
  "Consignor",
  "Consignee",
  "From State",
  "To State",
  // Unloading Weigh Bill section
  "Available?",
  "Date",
  "No.",
  "Name",
  "State",
  "Vehicle Number",
  "Net Weight (kg)",
  // Final section
  "Co Processor Name",
  "Remark",
  "Pending PO Qty (MT)",
  "Total PO Qty (MT)",
];

const preHeaders = [
  "",
  "",
  "Basic Information",
  "",
  "",
  // Delivery Challan
  "",
  "",
  "",
  "",
  "Delivery Challan",
  "",
  "",
  "",
  "",
  // Invoice section
  "",
  "Invoice",
  "",
  "",
  // Loading Weigh Bill section
  "",
  "",
  "",
  "Loading Weigh Bill",
  "",
  "",
  "",
  // E-Way bill section
  "",
  "",
  "",
  "E Way Bill",
  "",
  "",
  "",
  "",
  // LR section
  "",
  "",
  "",
  "",
  "LR",
  "",
  "",
  "",
  "",
  // Unloading Weigh Bill section
  "",
  "",
  "",
  "Unloading Weigh Bill",
  "",
  "",
  "",
  // Final section
  "",
  "Final",
  "",
  "",
];

const categoryColors = {
  "Basic Information": [246, 178, 107],
  Invoice: [204, 65, 37],
  "Loading Weigh Bill": [47, 84, 150],
  "E Way Bill": [197, 90, 17],
  LR: [123, 123, 123],
  "Delivery Challan": [197, 90, 17],
  "Unloading Weigh Bill": [46, 117, 181],
  Final: [56, 118, 29],
};

const removeConfidenceValue = (ans) => {
  let ans2 = `${ans}`;

  const regex = /<<\((.*?)\)>>/;
  const match = ans2.match(regex);
  if (match != null) {
    return ans2.replace(match[0], "");
  }
  return ans2;
};

export const downloadCSV = (data) => {
  // Prepare CSV content with headers
  let csvContent = preHeaders.join(", ") + "\n" + headers.join(", ") + "\n";

  // Group files by transaction (assuming files with same vehicle number are part of same transaction)
  const transaction = { weighbridgeCount: 0, documents: [] };
  data.files.forEach((file) => {
    const pages = file.pages || [file.data ? { data: file.data } : {}];
    pages.forEach((page) => {
      const fileData = page.data || {};

      transaction.documents.push(fileData);

      if (fileData["Category"] === "Weighbridge") {
        transaction.weighbridgeCount++;
      }
    });
  });

  // Process each transaction to create rows

  let rowData = new Array(headers.length).fill(""); // Initialize empty row

  // Set basic info
  rowData[0] = 1; // Sr. No.
  rowData[1] = ""; // Agency (to be filled)
  rowData[2] = ""; // Location (to be filled)
  rowData[3] = ""; // State (to be filled)
  rowData[4] = ""; // Category of Plastic Waste (to be filled)

  // Process each document in the transaction
  transaction.documents.forEach((fileData) => {
    switch (fileData["Category"]) {
      case "Delivery Challan":
        rowData[5] = fileData["Vehicle Number"] || "";
        rowData[6] = fileData["Date"] || "";
        rowData[7] = fileData["No."] || "";
        rowData[8] = fileData["Transporter Name"] || "";
        rowData[9] = fileData["Qty"] ? fileData["Qty"].replace(" MT", "") : "";
        rowData[10] = fileData["Consignor"] || "";
        rowData[11] = fileData["Consignee"] || "";
        rowData[12] = fileData["From State"] || "";
        rowData[3] = fileData["From State"] || "";
        rowData[13] = fileData["To State"] || "";
      case "Tax Invoice":
        rowData[14] = fileData["Invoice Date"] || "";
        rowData[15] = fileData["Invoice Number"] || "";
        rowData[16] = fileData["Quantity"]
          ? fileData["Quantity"].replace(" MT", "")
          : "";
        rowData[17] = fileData["Material Name"] || "";
        break;
      case "Weighbridge":
        // First weighbridge is loading, second is unloading
        if (transaction.weighbridgeCount === 2) {
          if (!rowData[19]) {
            // Loading weigh bill not filled yet
            rowData[18] = "Yes"; // Available?
            rowData[19] = fileData["Date"] || "";
            rowData[20] = fileData["No."] || "";
            rowData[21] = fileData["Name"] || "";
            rowData[22] = fileData["State"] || "";
            rowData[3] = fileData["State"] || "";
            rowData[23] = fileData["Vehicle Number"] || "";
            rowData[24] = fileData["Net Weight (Tons)"] || "";
          } else {
            // Unloading weigh bill
            rowData[42] = "Yes"; // Available?
            rowData[43] = fileData["Date"] || "";
            rowData[44] = fileData["No."] || "";
            rowData[45] = fileData["Name"] || "";
            rowData[46] = fileData["State"] || "";
            rowData[47] = fileData["Vehicle Number"] || "";
            rowData[48] = fileData["Net Weight (Tons)"] || "";
          }
        } else {
          // If only one weighbridge, assume it's loading
          rowData[18] = "Yes"; // Available?
          rowData[19] = fileData["Date"] || "";
          rowData[20] = fileData["No."] || "";
          rowData[21] = fileData["Name"] || "";
          rowData[22] = fileData["State"] || "";
          rowData[3] = fileData["State"] || "";
          rowData[23] = fileData["Vehicle Number"] || "";
          rowData[24] = fileData["Net Weight (Tons)"] || "";
        }
        break;
      case "E Way Bill":
        rowData[25] = "Yes"; // Available?
        rowData[26] = fileData["Generated Date"] || "";
        rowData[27] = fileData["No."] || "";
        rowData[28] = fileData["Qty"] ? fileData["Qty"].replace(" MT", "") : "";
        rowData[29] = fileData["Valid Upto"] || "";
        rowData[30] = fileData["From State"] || "";
        rowData[3] = fileData["From State"] || "";
        rowData[31] = fileData["To State"] || "";
        rowData[32] = fileData["Categorisation of Plastic Waste"] || "";
        break;
      case "LR Copy":
        rowData[33] = "Yes"; // Available?
        rowData[34] = fileData["Date"] || "";
        rowData[35] = fileData["No."] || "";
        rowData[36] = fileData["Transporter Name"] || "";
        rowData[37] = fileData["Qty"] ? fileData["Qty"].replace(" MT", "") : "";
        rowData[38] = fileData["Consignor"] || "";
        rowData[39] = fileData["Consignee"] || "";
        rowData[40] = fileData["From State"] || "";
        rowData[3] = fileData["From State"] || "";
        rowData[41] = fileData["To State"] || "";
        break;
    }
  });

  rowData = rowData.map((value) => removeConfidenceValue(value));

  // Escape values and create CSV row
  const escapedRow = rowData.map((value) => {
    if (value === null || value === undefined) return "";
    return `"${value.toString().replace(/"/g, '""')}"`;
  });

  csvContent += escapedRow.join(",") + "\n";

  // Create download link
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `${data.name || "export"}.csv`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const downloadPDF = (data) => {
  // Create a new jsPDF instance
  const doc = new jsPDF({
    orientation: "landscape",
  });

  // Prepare data for the table
  const tableData = [];

  // Add pre-headers as first row with background colors
  const coloredPreHeaders = preHeaders.map((header, index) => {
    let fillColor = null;

    // Find which category this column belongs to
    if (index <= 4) {
      fillColor = categoryColors["Basic Information"];
    } else if (index <= 13) {
      fillColor = categoryColors["Delivery Challan"];
    } else if (index <= 17) {
      fillColor = categoryColors["Invoice"];
    } else if (index <= 24) {
      fillColor = categoryColors["Loading Weigh Bill"];
    } else if (index <= 32) {
      fillColor = categoryColors["E Way Bill"];
    } else if (index <= 41) {
      fillColor = categoryColors["LR"];
    } else if (index <= 48) {
      fillColor = categoryColors["Unloading Weigh Bill"];
    } else {
      fillColor = categoryColors["Final"];
    }

    return {
      content: header,
      styles: {
        fontStyle: "bold",
        fillColor: fillColor,
        textColor: index <= 4 ? [0, 0, 0] : [255, 255, 255],
      },
    };
  });

  // Add headers as second row with matching background colors
  const coloredHeaders = headers.map((header, index) => {
    let fillColor = null;

    // Find which category this column belongs to
    if (index <= 4) {
      fillColor = categoryColors["Basic Information"];
    } else if (index <= 13) {
      fillColor = categoryColors["Delivery Challan"];
    } else if (index <= 17) {
      fillColor = categoryColors["Invoice"];
    } else if (index <= 24) {
      fillColor = categoryColors["Loading Weigh Bill"];
    } else if (index <= 32) {
      fillColor = categoryColors["E Way Bill"];
    } else if (index <= 41) {
      fillColor = categoryColors["LR"];
    } else if (index <= 48) {
      fillColor = categoryColors["Unloading Weigh Bill"];
    } else {
      fillColor = categoryColors["Final"];
    }

    return {
      content: header,
      styles: {
        fontStyle: "bold",
        fillColor: fillColor,
        textColor: index <= 4 ? [0, 0, 0] : [255, 255, 255],
      },
    };
  });

  tableData.push(coloredPreHeaders);
  tableData.push(coloredHeaders);

  // Group files by transaction (assuming files with same vehicle number are part of same transaction)
  const transaction = { weighbridgeCount: 0, documents: [] };
  data.files.forEach((file) => {
    const pages = file.pages || [file.data ? { data: file.data } : {}];
    pages.forEach((page) => {
      const fileData = page.data || {};

      transaction.documents.push(fileData);

      if (fileData["Category"] === "Weighbridge") {
        transaction.weighbridgeCount++;
      }
    });
  });

  // Process each transaction to create rows

  let rowData = new Array(headers.length).fill(""); // Initialize empty row

  // Set basic info
  rowData[0] = 1; // Sr. No.
  rowData[1] = ""; // Agency (to be filled)
  rowData[2] = ""; // Location (to be filled)
  rowData[3] = ""; // State (to be filled)
  rowData[4] = ""; // Category of Plastic Waste (to be filled)

  // Process each document in the transaction
  transaction.documents.forEach((fileData) => {
    switch (fileData["Category"]) {
      case "Delivery Challan":
        rowData[5] = fileData["Vehicle Number"] || "";
        rowData[6] = fileData["Date"] || "";
        rowData[7] = fileData["No."] || "";
        rowData[8] = fileData["Transporter Name"] || "";
        rowData[9] = fileData["Qty"] ? fileData["Qty"].replace(" MT", "") : "";
        rowData[10] = fileData["Consignor"] || "";
        rowData[11] = fileData["Consignee"] || "";
        rowData[12] = fileData["From State"] || "";
        rowData[3] = fileData["From State"] || "";
        rowData[13] = fileData["To State"] || "";
      case "Tax Invoice":
        rowData[14] = fileData["Invoice Date"] || "";
        rowData[15] = fileData["Invoice Number"] || "";
        rowData[16] = fileData["Quantity"]
          ? fileData["Quantity"].replace(" MT", "")
          : "";
        rowData[17] = fileData["Material Name"] || "";
        break;
      case "Weighbridge":
        // First weighbridge is loading, second is unloading
        if (transaction.weighbridgeCount === 2) {
          if (!rowData[19]) {
            // Loading weigh bill not filled yet
            rowData[18] = "Yes"; // Available?
            rowData[19] = fileData["Date"] || "";
            rowData[20] = fileData["No."] || "";
            rowData[21] = fileData["Name"] || "";
            rowData[22] = fileData["State"] || "";
            rowData[3] = fileData["State"] || "";
            rowData[23] = fileData["Vehicle Number"] || "";
            rowData[24] = fileData["Net Weight (Tons)"] || "";
          } else {
            // Unloading weigh bill
            rowData[42] = "Yes"; // Available?
            rowData[43] = fileData["Date"] || "";
            rowData[44] = fileData["No."] || "";
            rowData[45] = fileData["Name"] || "";
            rowData[46] = fileData["State"] || "";
            rowData[47] = fileData["Vehicle Number"] || "";
            rowData[48] = fileData["Net Weight (Tons)"] || "";
          }
        } else {
          // If only one weighbridge, assume it's loading
          rowData[18] = "Yes"; // Available?
          rowData[19] = fileData["Date"] || "";
          rowData[20] = fileData["No."] || "";
          rowData[21] = fileData["Name"] || "";
          rowData[22] = fileData["State"] || "";
          rowData[3] = fileData["State"] || "";
          rowData[23] = fileData["Vehicle Number"] || "";
          rowData[24] = fileData["Net Weight (Tons)"] || "";
        }
        break;
      case "E Way Bill":
        rowData[25] = "Yes"; // Available?
        rowData[26] = fileData["Generated Date"] || "";
        rowData[27] = fileData["No."] || "";
        rowData[28] = fileData["Qty"] ? fileData["Qty"].replace(" MT", "") : "";
        rowData[29] = fileData["Valid Upto"] || "";
        rowData[30] = fileData["From State"] || "";
        rowData[3] = fileData["From State"] || "";
        rowData[31] = fileData["To State"] || "";
        rowData[32] = fileData["Categorisation of Plastic Waste"] || "";
        break;
      case "LR Copy":
        rowData[33] = "Yes"; // Available?
        rowData[34] = fileData["Date"] || "";
        rowData[35] = fileData["No."] || "";
        rowData[36] = fileData["Transporter Name"] || "";
        rowData[37] = fileData["Qty"] ? fileData["Qty"].replace(" MT", "") : "";
        rowData[38] = fileData["Consignor"] || "";
        rowData[39] = fileData["Consignee"] || "";
        rowData[40] = fileData["From State"] || "";
        rowData[3] = fileData["From State"] || "";
        rowData[41] = fileData["To State"] || "";
        break;
    }
  });

  // Remove confidence values
  rowData = rowData.map((value) => removeConfidenceValue(value));

  // Add to table data
  tableData.push(rowData);

  // Generate the table
  autoTable(doc, {
    head: [tableData[0], tableData[1]], // First row is pre-headers, second is headers
    body: tableData.slice(2), // Rest are data rows
    startY: 10,
    margin: { left: 5, right: 5 },
    styles: {
      fontSize: 8,
      cellPadding: 1,
      overflow: "linebreak",
      cellWidth: "wrap",
      textColor: [0, 0, 0],
      lineWidth: 0.1,
      lineColor: [70, 70, 70],
    },
    horizontalPageBreak: true,
  });

  // Save the PDF
  doc.save(`${data.name || "export"}.pdf`);
};

export const downloadCompleteCSV = (data) => {
  // Prepare CSV content with headers
  let csvContent = preHeaders.join(", ") + "\n" + headers.join(", ") + "\n";

  // Process each transaction in the data array
  data.forEach((transactionData, index) => {
    // Group files by transaction (assuming files with same vehicle number are part of same transaction)
    const transaction = { weighbridgeCount: 0, documents: [] };

    transactionData.files.forEach((file) => {
      const pages = file.pages || [file.data ? { data: file.data } : {}];
      pages.forEach((page) => {
        const fileData = page.data || {};
        transaction.documents.push(fileData);

        if (fileData["Category"] === "Weighbridge") {
          transaction.weighbridgeCount++;
        }
      });
    });

    // Initialize empty row
    let rowData = new Array(headers.length).fill("");

    // Set basic info
    rowData[0] = index + 1; // Sr. No.
    rowData[1] = ""; // Agency (to be filled)
    rowData[2] = ""; // Location (to be filled)
    rowData[3] = ""; // State (to be filled)
    rowData[4] = ""; // Category of Plastic Waste (to be filled)

    // Process each document in the transaction
    transaction.documents.forEach((fileData) => {
      switch (fileData["Category"]) {
        case "Delivery Challan":
          rowData[5] = fileData["Vehicle Number"] || "";
          rowData[6] = fileData["Date"] || "";
          rowData[7] = fileData["No."] || "";
          rowData[8] = fileData["Transporter Name"] || "";
          rowData[9] = fileData["Qty"]
            ? fileData["Qty"].replace(" MT", "")
            : "";
          rowData[10] = fileData["Consignor"] || "";
          rowData[11] = fileData["Consignee"] || "";
          rowData[12] = fileData["From State"] || "";
          rowData[3] = fileData["From State"] || "";
          rowData[13] = fileData["To State"] || "";
        case "Tax Invoice":
          rowData[14] = fileData["Invoice Date"] || "";
          rowData[15] = fileData["Invoice Number"] || "";
          rowData[16] = fileData["Quantity"]
            ? fileData["Quantity"].replace(" MT", "")
            : "";
          rowData[17] = fileData["Material Name"] || "";
          break;
        case "Weighbridge":
          // First weighbridge is loading, second is unloading
          if (transaction.weighbridgeCount === 2) {
            if (!rowData[19]) {
              // Loading weigh bill not filled yet
              rowData[18] = "Yes"; // Available?
              rowData[19] = fileData["Date"] || "";
              rowData[20] = fileData["No."] || "";
              rowData[21] = fileData["Name"] || "";
              rowData[22] = fileData["State"] || "";
              rowData[3] = fileData["State"] || "";
              rowData[23] = fileData["Vehicle Number"] || "";
              rowData[24] = fileData["Net Weight (Tons)"] || "";
            } else {
              // Unloading weigh bill
              rowData[42] = "Yes"; // Available?
              rowData[43] = fileData["Date"] || "";
              rowData[44] = fileData["No."] || "";
              rowData[45] = fileData["Name"] || "";
              rowData[46] = fileData["State"] || "";
              rowData[47] = fileData["Vehicle Number"] || "";
              rowData[48] = fileData["Net Weight (Tons)"] || "";
            }
          } else {
            // If only one weighbridge, assume it's loading
            rowData[18] = "Yes"; // Available?
            rowData[19] = fileData["Date"] || "";
            rowData[20] = fileData["No."] || "";
            rowData[21] = fileData["Name"] || "";
            rowData[22] = fileData["State"] || "";
            rowData[3] = fileData["State"] || "";
            rowData[23] = fileData["Vehicle Number"] || "";
            rowData[24] = fileData["Net Weight (Tons)"] || "";
          }
          break;
        case "E Way Bill":
          rowData[25] = "Yes"; // Available?
          rowData[26] = fileData["Generated Date"] || "";
          rowData[27] = fileData["No."] || "";
          rowData[28] = fileData["Qty"]
            ? fileData["Qty"].replace(" MT", "")
            : "";
          rowData[29] = fileData["Valid Upto"] || "";
          rowData[30] = fileData["From State"] || "";
          rowData[3] = fileData["From State"] || "";
          rowData[31] = fileData["To State"] || "";
          rowData[32] = fileData["Categorisation of Plastic Waste"] || "";
          break;
        case "LR Copy":
          rowData[33] = "Yes"; // Available?
          rowData[34] = fileData["Date"] || "";
          rowData[35] = fileData["No."] || "";
          rowData[36] = fileData["Transporter Name"] || "";
          rowData[37] = fileData["Qty"]
            ? fileData["Qty"].replace(" MT", "")
            : "";
          rowData[38] = fileData["Consignor"] || "";
          rowData[39] = fileData["Consignee"] || "";
          rowData[40] = fileData["From State"] || "";
          rowData[3] = fileData["From State"] || "";
          rowData[41] = fileData["To State"] || "";
          break;
      }
    });

    rowData = rowData.map((value) => removeConfidenceValue(value));

    // Escape values and create CSV row
    const escapedRow = rowData.map((value) => {
      if (value === null || value === undefined) return "";
      return `"${value.toString().replace(/"/g, '""')}"`;
    });

    csvContent += escapedRow.join(",") + "\n";
  });

  // Create download link
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute(
    "download",
    `complete_export_${new Date().toISOString().split("T")[0]}.csv`
  );
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const downloadCompletePDF = (data) => {
  // Create a new jsPDF instance
  const doc = new jsPDF({
    orientation: "landscape",
  });

  // Prepare data for the table
  const tableData = [];

  // Add pre-headers as first row with background colors
  const coloredPreHeaders = preHeaders.map((header, index) => {
    let fillColor = null;

    // Find which category this column belongs to
    if (index <= 4) {
      fillColor = categoryColors["Basic Information"];
    } else if (index <= 13) {
      fillColor = categoryColors["Delivery Challan"];
    } else if (index <= 17) {
      fillColor = categoryColors["Invoice"];
    } else if (index <= 24) {
      fillColor = categoryColors["Loading Weigh Bill"];
    } else if (index <= 32) {
      fillColor = categoryColors["E Way Bill"];
    } else if (index <= 41) {
      fillColor = categoryColors["LR"];
    } else if (index <= 48) {
      fillColor = categoryColors["Unloading Weigh Bill"];
    } else {
      fillColor = categoryColors["Final"];
    }

    return {
      content: header,
      styles: {
        fontStyle: "bold",
        fillColor: fillColor,
        textColor: index <= 4 ? [0, 0, 0] : [255, 255, 255],
      },
    };
  });

  // Add headers as second row with matching background colors
  const coloredHeaders = headers.map((header, index) => {
    let fillColor = null;

    // Find which category this column belongs to
    if (index <= 4) {
      fillColor = categoryColors["Basic Information"];
    } else if (index <= 13) {
      fillColor = categoryColors["Delivery Challan"];
    } else if (index <= 17) {
      fillColor = categoryColors["Invoice"];
    } else if (index <= 24) {
      fillColor = categoryColors["Loading Weigh Bill"];
    } else if (index <= 32) {
      fillColor = categoryColors["E Way Bill"];
    } else if (index <= 41) {
      fillColor = categoryColors["LR"];
    } else if (index <= 48) {
      fillColor = categoryColors["Unloading Weigh Bill"];
    } else {
      fillColor = categoryColors["Final"];
    }

    return {
      content: header,
      styles: {
        fontStyle: "bold",
        fillColor: fillColor,
        textColor: index <= 4 ? [0, 0, 0] : [255, 255, 255],
      },
    };
  });

  tableData.push(coloredPreHeaders);
  tableData.push(coloredHeaders);

  // Process each transaction in the data array
  data.forEach((transactionData, index) => {
    // Group files by transaction
    const transaction = { weighbridgeCount: 0, documents: [] };

    transactionData.files.forEach((file) => {
      const pages = file.pages || [file.data ? { data: file.data } : {}];
      pages.forEach((page) => {
        const fileData = page.data || {};
        transaction.documents.push(fileData);

        if (fileData["Category"] === "Weighbridge") {
          transaction.weighbridgeCount++;
        }
      });
    });

    // Initialize empty row
    let rowData = new Array(headers.length).fill("");

    // Set basic info
    rowData[0] = index + 1; // Sr. No.
    rowData[1] = ""; // Agency (to be filled)
    rowData[2] = ""; // Location (to be filled)
    rowData[3] = ""; // State (to be filled)
    rowData[4] = ""; // Category of Plastic Waste (to be filled)

    // Process each document in the transaction
    transaction.documents.forEach((fileData) => {
      switch (fileData["Category"]) {
        case "Delivery Challan":
          rowData[5] = fileData["Vehicle Number"] || "";
          rowData[6] = fileData["Date"] || "";
          rowData[7] = fileData["No."] || "";
          rowData[8] = fileData["Transporter Name"] || "";
          rowData[9] = fileData["Qty"]
            ? fileData["Qty"].replace(" MT", "")
            : "";
          rowData[10] = fileData["Consignor"] || "";
          rowData[11] = fileData["Consignee"] || "";
          rowData[12] = fileData["From State"] || "";
          rowData[3] = fileData["From State"] || "";
          rowData[13] = fileData["To State"] || "";
        case "Tax Invoice":
          rowData[14] = fileData["Invoice Date"] || "";
          rowData[15] = fileData["Invoice Number"] || "";
          rowData[16] = fileData["Quantity"]
            ? fileData["Quantity"].replace(" MT", "")
            : "";
          rowData[17] = fileData["Material Name"] || "";
          break;
        case "Weighbridge":
          // First weighbridge is loading, second is unloading
          if (transaction.weighbridgeCount === 2) {
            if (!rowData[19]) {
              // Loading weigh bill not filled yet
              rowData[18] = "Yes"; // Available?
              rowData[19] = fileData["Date"] || "";
              rowData[20] = fileData["No."] || "";
              rowData[21] = fileData["Name"] || "";
              rowData[22] = fileData["State"] || "";
              rowData[3] = fileData["State"] || "";
              rowData[23] = fileData["Vehicle Number"] || "";
              rowData[24] = fileData["Net Weight (Tons)"] || "";
            } else {
              // Unloading weigh bill
              rowData[42] = "Yes"; // Available?
              rowData[43] = fileData["Date"] || "";
              rowData[44] = fileData["No."] || "";
              rowData[45] = fileData["Name"] || "";
              rowData[46] = fileData["State"] || "";
              rowData[47] = fileData["Vehicle Number"] || "";
              rowData[48] = fileData["Net Weight (Tons)"] || "";
            }
          } else {
            // If only one weighbridge, assume it's loading
            rowData[18] = "Yes"; // Available?
            rowData[19] = fileData["Date"] || "";
            rowData[20] = fileData["No."] || "";
            rowData[21] = fileData["Name"] || "";
            rowData[22] = fileData["State"] || "";
            rowData[3] = fileData["State"] || "";
            rowData[23] = fileData["Vehicle Number"] || "";
            rowData[24] = fileData["Net Weight (Tons)"] || "";
          }
          break;
        case "E Way Bill":
          rowData[25] = "Yes"; // Available?
          rowData[26] = fileData["Generated Date"] || "";
          rowData[27] = fileData["No."] || "";
          rowData[28] = fileData["Qty"]
            ? fileData["Qty"].replace(" MT", "")
            : "";
          rowData[29] = fileData["Valid Upto"] || "";
          rowData[30] = fileData["From State"] || "";
          rowData[3] = fileData["From State"] || "";
          rowData[31] = fileData["To State"] || "";
          rowData[32] = fileData["Categorisation of Plastic Waste"] || "";
          break;
        case "LR Copy":
          rowData[33] = "Yes"; // Available?
          rowData[34] = fileData["Date"] || "";
          rowData[35] = fileData["No."] || "";
          rowData[36] = fileData["Transporter Name"] || "";
          rowData[37] = fileData["Qty"]
            ? fileData["Qty"].replace(" MT", "")
            : "";
          rowData[38] = fileData["Consignor"] || "";
          rowData[39] = fileData["Consignee"] || "";
          rowData[40] = fileData["From State"] || "";
          rowData[3] = fileData["From State"] || "";
          rowData[41] = fileData["To State"] || "";
          break;
      }
    });

    // Remove confidence values
    rowData = rowData.map((value) => removeConfidenceValue(value));

    // Add to table data
    tableData.push(rowData);
  });

  // Generate the table
  autoTable(doc, {
    head: [tableData[0], tableData[1]], // First row is pre-headers, second is headers
    body: tableData.slice(2), // Rest are data rows
    startY: 10,
    margin: { left: 5, right: 5 },
    styles: {
      fontSize: 8,
      cellPadding: 1,
      overflow: "linebreak",
      cellWidth: "wrap",
      textColor: [0, 0, 0],
      lineWidth: 0.1,
      lineColor: [70, 70, 70],
    },
    horizontalPageBreak: true,
    didDrawPage: function (data) {
      // Add footer with page number
      const pageCount = doc.internal.getNumberOfPages();
      const currentPage = data.pageNumber;

      doc.setFontSize(8);
      doc.setTextColor(100);
      doc.text(
        `Page ${currentPage} of ${pageCount}`,
        data.settings.margin.left,
        doc.internal.pageSize.height - 10
      );
    },
  });

  // Save the PDF
  doc.save(`complete_export_${new Date().toISOString().split("T")[0]}.pdf`);
};
