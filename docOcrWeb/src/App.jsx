import Navbar from "./components/Navbar";
import plus from "./assets/icons/plus.png";
import { createRef, useState, useEffect } from "react";
import TableRow from "./components/TableRow";
import { io } from "socket.io-client";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import ExtractedDataDisplay from "./components/ExtractedDataDisplay";
import { ClipLoader } from "react-spinners";
import NestedPDFDataDisplay from "./components/NestedPDFDataDisplay";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";
import downloadIcon from "./assets/icons/download.png";
import { downloadCompleteCSV, downloadCompletePDF } from "./utils/download";
// formData.append("socket_id", socket.id);

pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.js";

function App() {
  const inputRef = createRef();

  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [progress, setProgress] = useState(0);

  const [extractedData, setExtractedData] = useState({});

  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  const [selectedRow, setSelectedRow] = useState(null);

  const [socket, setSocket] = useState(null);

  const [uploadType, setUploadType] = useState("files");
  const [subfolders, setSubfolders] = useState([]);

  const [viewer, setViewer] = useState(null);
  const [viewerPageNumber, setViewerPageNumber] = useState(1);
  const [displayFiles, setDisplayFiles] = useState([]);

  // const backendURL = "https://ocr.recircle.in/api";
  const backendURL = "http://localhost:3000";

  useEffect(() => {
    // const newSocket = io("https://ocr.recircle.in");
    const newSocket = io("http://localhost:3000");
    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
      setSocket(null);
    };
  }, []);

  useEffect(() => {
    if (socket) {
      socket.on("fileStatus", (data) => {
        if (data.status === "processing") {
          if (data.pdf && data.parent === null) {
            setUploadedFiles((prevUploadedFiles) => {
              return prevUploadedFiles.map((prevUploadedFile) => {
                if (prevUploadedFile.name === data.fileName) {
                  const newPages =
                    prevUploadedFile.pages.length > 0
                      ? !prevUploadedFile.pages.some(
                          (page) =>
                            page.name ===
                            `${prevUploadedFile.name}_Page_${data.page}`
                        )
                        ? [
                            ...prevUploadedFile.pages,
                            {
                              name: `${prevUploadedFile.name}_Page_${data.page}`,
                              data: null,
                            },
                          ]
                        : prevUploadedFile.pages
                      : [
                          {
                            name: `${prevUploadedFile.name}_Page_${data.page}`,
                            data: null,
                          },
                        ];

                  return {
                    ...prevUploadedFile,
                    status: "Processing",
                    pages: newPages,
                  };
                } else {
                  return prevUploadedFile;
                }
              });
            });
          } else if (data.parent !== null) {
            // Image File
            setUploadedFiles((prevUploadedFiles) => {
              return prevUploadedFiles.map((prevUploadedFile) => {
                if (prevUploadedFile.name === data.parent) {
                  const newFiles = prevUploadedFile.files.map((file) => {
                    if (file.name === `${data.parent}/${data.fileName}`) {
                      const extension = file.name
                        .split(".")
                        .pop()
                        .toLowerCase();
                      if (extension === "pdf") {
                        let newPages = [...file.pages];

                        if (
                          !file.pages.some(
                            (page) =>
                              page.name === `${file.name}_Page_${data.page}`
                          )
                        ) {
                          newPages.push({
                            name: `${file.name}_Page_${data.page}`,
                            data: null,
                          });
                        }

                        return {
                          name: file.name,
                          pages: newPages,
                          status: "Processing",
                        };
                      } else {
                        return {
                          name: file.name,
                          data: null,
                          status: "Processing",
                        };
                      }
                    } else {
                      return file;
                    }
                  });

                  return {
                    ...prevUploadedFile,
                    status: "Processing",
                    files: newFiles,
                  };
                } else {
                  return prevUploadedFile;
                }
              });
            });
          }
        } else if (data.status === "completed") {
          // File has been processed and returned a valid result
          if (data.pdf && data.parent === null) {
            // PDF File
            setUploadedFiles((prevUploadedFiles) => {
              return prevUploadedFiles.map((prevUploadedFile) => {
                if (prevUploadedFile.name === data.fileName) {
                  const newPages =
                    prevUploadedFile.pages.length > 0
                      ? prevUploadedFile.pages.map((page) => {
                          if (
                            page.name ===
                            `${prevUploadedFile.name}_Page_${data.page}`
                          ) {
                            return { name: page.name, data: data.result };
                          } else {
                            return page;
                          }
                        })
                      : prevUploadedFile.pages;

                  return {
                    ...prevUploadedFile,
                    status: "Success",
                    pages: newPages,
                  };
                } else {
                  return prevUploadedFile;
                }
              });
            });
          } else if (data.parent !== null) {
            // Image File
            setUploadedFiles((prevUploadedFiles) => {
              return prevUploadedFiles.map((prevUploadedFile) => {
                if (prevUploadedFile.name === data.parent) {
                  const newFiles = prevUploadedFile.files.map((file) => {
                    if (file.name === `${data.parent}/${data.fileName}`) {
                      const extension = file.name
                        .split(".")
                        .pop()
                        .toLowerCase();
                      if (extension === "pdf") {
                        const newPages = file.pages.map((page) => {
                          if (page.name == `${file.name}_Page_${data.page}`) {
                            return { name: page.name, data: data.result };
                          } else {
                            return page;
                          }
                        });

                        return {
                          name: file.name,
                          pages: newPages,
                          status: "Success",
                        };
                      } else {
                        return {
                          name: file.name,
                          data: data.result,
                          status: "Success",
                        };
                      }
                    } else {
                      return file;
                    }
                  });

                  return {
                    ...prevUploadedFile,
                    status: "Success",
                    files: newFiles,
                  };
                } else {
                  return prevUploadedFile;
                }
              });
            });
          }
        } else if (data.status === "failed") {
          // There was an error during processing
          if (data.pdf && data.parent === null) {
            // PDF File
            setUploadedFiles((prevUploadedFiles) => {
              return prevUploadedFiles.map((prevUploadedFile) => {
                if (prevUploadedFile.name === data.fileName) {
                  const newPages =
                    prevUploadedFile.pages.length > 0
                      ? prevUploadedFile.pages.map((page) => {
                          if (
                            page.name ===
                            `${prevUploadedFile.name}_Page_${data.page}`
                          ) {
                            return { name: page.name, data: "Failed" };
                          } else {
                            return page;
                          }
                        })
                      : prevUploadedFile.pages;

                  return {
                    ...prevUploadedFile,
                    status: "Success",
                    pages: newPages,
                  };
                } else {
                  return prevUploadedFile;
                }
              });
            });
          } else if (data.parent !== null) {
            // Image File
            setUploadedFiles((prevUploadedFiles) => {
              return prevUploadedFiles.map((prevUploadedFile) => {
                if (prevUploadedFile.name === data.parent) {
                  const newFiles = prevUploadedFile.files.map((file) => {
                    if (file.name === `${data.parent}/${data.fileName}`) {
                      const extension = file.name
                        .split(".")
                        .pop()
                        .toLowerCase();
                      if (extension === "pdf") {
                        const newPages = file.pages.map((page) => {
                          if (page.name == `${file.name}_Page_${data.page}`) {
                            return { name: page.name, data: "Failed" };
                          } else {
                            return page;
                          }
                        });

                        return {
                          name: file.name,
                          pages: newPages,
                          status: "Failed",
                        };
                      } else {
                        return {
                          name: file.name,
                          data: data.result,
                          status: "Failed",
                        };
                      }
                    } else {
                      return file;
                    }
                  });

                  return {
                    ...prevUploadedFile,
                    status: "Success",
                    files: newFiles,
                  };
                } else {
                  return prevUploadedFile;
                }
              });
            });
          }
        }
      });
    }

    console.log(uploadedFiles);

    // Progress Bar Calculation
    const completedDocs = uploadedFiles.filter(
      (file) => file.status != "Processing" && file.status != "Pending"
    ).length;
    setProgress((completedDocs * 100) / uploadedFiles.length);
  }, [uploadedFiles]);

  // Helper function for folder upload
  const handleClick = () => {
    inputRef.current.click();
  };

  // Upload folder
  const handleFileChange = (event) => {
    const files = Array.from(event.target.files);

    files.forEach((file) => {
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = () => {
          setDisplayFiles((prevFiles) => [
            ...prevFiles,
            { name: file.name, type: "image", src: reader.result },
          ]);
        };
        reader.readAsDataURL(file);
      } else if (file.type === "application/pdf") {
        setDisplayFiles((prevFiles) => [
          ...prevFiles,
          { name: file.name, type: "pdf", src: URL.createObjectURL(file) },
        ]);
      }
    });

    if (files.length > 0) {
      const fileStructure = files.reduce(
        (acc, file) => {
          const pathParts = file.webkitRelativePath.split("/");
          if (pathParts.length === 2) {
            acc.mainFolderFiles.push(file);
          } else if (pathParts.length === 3) {
            const subfolderName = pathParts[1];
            let subfolder = acc.subfolders.find(
              (sf) => sf.name === subfolderName
            );
            if (!subfolder) {
              subfolder = { name: subfolderName, files: [] };
              acc.subfolders.push(subfolder);
            }
            subfolder.files.push(file);
          }
          return acc;
        },
        { mainFolderFiles: [], subfolders: [] }
      );

      const hasSubfolders = fileStructure.subfolders.length > 0;
      const hasMainFolderFiles = fileStructure.mainFolderFiles.length > 0;

      let validSubfolderFormat = false;
      let validPdfFormat = false;

      if (hasSubfolders && hasMainFolderFiles) {
        toast.error("Invalid format: Both PDFs and subfolders detected.");
        return;
      }

      if (hasSubfolders) {
        const validTypes = ["png", "jpg", "jpeg", "pdf"];
        const allValidTypes = fileStructure.subfolders
          .flatMap((subfolder) => subfolder.files)
          .every((file) => {
            const extension = file.name.split(".").pop().toLowerCase();
            return validTypes.includes(extension);
          });

        if (!allValidTypes) {
          toast.error(
            "Invalid format: Subfolders must contain only images (PNG, JPG, JPEG, PDF).",
            { theme: "dark" }
          );
          return;
        }

        validSubfolderFormat = true;
        setUploadType("subfolders");
        setSubfolders(fileStructure.subfolders);
      } else if (hasMainFolderFiles) {
        // Validate main folder contains only PDFs
        const allPdfs = fileStructure.mainFolderFiles.every(
          (file) => file.type === "application/pdf"
        );

        if (!allPdfs) {
          toast.error(
            "Invalid format: Main folder must contain only PDFs or subfolders.",
            { theme: "dark" }
          );
          return;
        }

        validPdfFormat = true;
        setUploadType("files");
      } else {
        toast.error("Invalid format: Folder structure not recognized.", {
          theme: "dark",
        });
        return;
      }

      // Initial File Data
      if (validPdfFormat) {
        // PDFs Format
        const initialFileInfo = files.map((file) => {
          return {
            name: file.name,
            size: file.size,
            type: file.type,
            pages: [],
            status: "Pending",
          };
        });

        setUploadedFiles(initialFileInfo);
      } else if (validSubfolderFormat) {
        // Subfolders Format
        const initialFileInfo = fileStructure.subfolders.map((subfolder) => {
          return {
            name: subfolder.name,
            files: subfolder.files.map((file) => {
              const fileName = `${file.webkitRelativePath.split("/")[1]}/${
                file.webkitRelativePath.split("/")[2]
              }`;
              const extension = fileName.split(".").pop().toLowerCase();
              if (extension === "pdf") {
                return { name: fileName, pages: [], status: "Pending" };
              } else {
                return { name: fileName, data: null, status: "Pending" };
              }
            }),
            status: "Pending",
          };
        });

        setUploadedFiles(initialFileInfo);
      }

      setProgress(0);

      const formData = new FormData();
      files.forEach((file) => {
        if (validPdfFormat) {
          formData.append("images", file);
        }

        if (validSubfolderFormat) {
          formData.append("images", file);
          formData.append("parents[]", file.webkitRelativePath.split("/")[1]);
        }
      });

      // fetch(`${backendURL}/extractText`, {
      //   method: "POST",
      //   body: formData,
      //   headers: {
      //     "socket-id": socket.id,
      //   },
      // })
      formData.append("socket_id", socket.id);  // Add this line

      fetch(`${backendURL}/extractText`, {
        method: "POST",
        body: formData  // Do NOT set headers manually
      })

        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          } else {
            console.log("Files uploaded successfully");
          }
        })
        .catch((error) => {
          console.error("Error during file upload: ", error);
        });
    } else {
      console.log("No files selected");
    }
  };

  const findMostFrequentItem = (arr) => {
    if (arr && arr.length > 0) {
      const frequencyMap = {};
      let maxCount = 0;
      let mostFrequentItem = "None";

      for (let item of arr) {
        frequencyMap[item] = (frequencyMap[item] || 0) + 1;
        if (frequencyMap[item] > maxCount) {
          maxCount = frequencyMap[item];
          mostFrequentItem = item;
        }
      }

      let countOfMax = 0;
      for (let key in frequencyMap) {
        if (frequencyMap[key] === maxCount) {
          countOfMax++;
        }
        if (countOfMax > 1) return ["None", maxCount];
      }

      return [mostFrequentItem, maxCount];
    } else {
      return ["None", 0];
    }
  };

  const getCommonVehicleNumber = (selectedRow) => {
    if (selectedRow) {
      if (uploadType === "subfolders") {
        const vehicleNumbers = uploadedFiles
          .find((subfolder) => subfolder.name === selectedRow)
          ?.files.filter((file) => file.data && file.data["Vehicle no."])
          .map((file) => file.data["Vehicle no."]);

        return findMostFrequentItem(vehicleNumbers);
      } else {
        const vehicleNumbers = uploadedFiles
          .find((pdf) => pdf.name === selectedRow)
          ?.pages.filter((page) => page.data && page.data["Vehicle no."])
          .map((page) => page.data["Vehicle no."]);

        return findMostFrequentItem(vehicleNumbers);
      }
    } else {
      return ["None", 0];
    }
  };

  const onViewFile = (name, pageNumber) => {
    if (pageNumber) {
      pageNumber = parseInt(pageNumber);
      if (viewer === name && viewerPageNumber === pageNumber) {
        setViewer(null);
      } else {
        setViewer(name);
      }
      setViewerPageNumber(pageNumber);
    } else {
      setViewer(viewer === name ? null : name);
    }
  };

  // Calculate pagination details
  let paginatedFiles = null;
  let paginatedSubfolders = null;

  const totalPages =
    uploadType === "files"
      ? Math.ceil(uploadedFiles.length / rowsPerPage)
      : Math.ceil(subfolders.length / rowsPerPage);
  if (uploadType === "files") {
    paginatedFiles = uploadedFiles.slice(
      (currentPage - 1) * rowsPerPage,
      currentPage * rowsPerPage
    );
  } else {
    paginatedSubfolders = uploadedFiles.slice(
      (currentPage - 1) * rowsPerPage,
      currentPage * rowsPerPage
    );
  }

  return (
    <div>
      <Navbar />
      <div className="p-4 md:p-8 flex flex-col gap-4 md:gap-8">
        <div className="flex flex-col md:flex-row justify-between items-start gap-4">
          <div>
            <div className="text-2xl md:text-3xl">Recircle Document OCR</div>
            <div className="text-sm md:text-lg pt-2 text-[#666]">
              <p className="font-semibold">Valid Format:</p>
              <p className="pl-2">
                Folder containing subfolders of images (PNGs, JPGs, JPEGs, PDFs)
              </p>
            </div>
          </div>
          <div
            className="bg-primaryD rounded flex items-center px-4 py-3 gap-4 cursor-pointer hover:bg-primaryD-dark w-auto"
            onClick={handleClick}
          >
            <img className="w-[15px]" src={plus} alt={plus} />
            <span className="text-white">Upload Folder</span>
            <input
              ref={inputRef}
              type="file"
              multiple=""
              directory=""
              webkitdirectory=""
              mozdirectory=""
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
          </div>
        </div>
        <div className={`flex max-md:flex-col gap-4 items-start flex-col`}>
          <div
            className={`flex-1 border-[1px] border-[#D2D0CE] rounded-lg flex flex-col overflow-x-auto w-full`}
          >
            <div className="text-textL text-lg md:text-xl p-4 font-semibold flex justify-between items-center">
              {uploadType === "files" ? (
                <span>Number of files detected: {uploadedFiles.length}</span>
              ) : (
                <span>Number of subfolders detected: {subfolders.length}</span>
              )}
              {uploadedFiles.length > 0 && uploadType !== "files" && (
                <div className="flex flex-row gap-4">
                  <button
                    onClick={() => downloadCompleteCSV(uploadedFiles)}
                    disabled={!(progress == 100)}
                    className={`bg-primaryD text-white rounded px-4 py-2 flex items-center text-sm ${
                      progress == 100
                        ? "hover:bg-primaryD-dark"
                        : "opacity-50 cursor-not-allowed"
                    }`}
                  >
                    <img
                      className="w-[20px] h-[20px] mr-2"
                      src={downloadIcon}
                    />
                    Download CSV
                  </button>
                  <button
                    onClick={() => downloadCompletePDF(uploadedFiles)}
                    disabled={!(progress == 100)}
                    className={`bg-primaryD text-white rounded px-4 py-2 flex items-center text-sm ${
                      progress == 100
                        ? "hover:bg-primaryD-dark"
                        : "opacity-50 cursor-not-allowed"
                    }`}
                  >
                    <img
                      className="w-[20px] h-[20px] mr-2"
                      src={downloadIcon}
                    />
                    Download PDF
                  </button>
                </div>
              )}
              {uploadType === "files" &&
                uploadedFiles[0]?.status === "Pending" && (
                  <div className="flex items-center gap-4">
                    <ClipLoader size={20} />
                    <p>PDFs to JPG Conversion</p>
                  </div>
                )}
            </div>
            {progress > 0 && !(progress == 100) && (
              <div className="px-2 mb-4 mx-2 max-md:mx-0 max-md:px-2 flex items-center gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-lg md:text-md font-bold text-primaryD">
                    {Math.round(progress)}%
                  </span>
                </div>
                <div className="overflow-hidden h-3 text-xs flex rounded-lg bg-primaryD-light w-full">
                  <div
                    style={{
                      width: `${progress}%`,
                      transition: "width 0.5s ease",
                    }}
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-primary"
                  ></div>
                </div>
              </div>
            )}
            <div className="overflow-x-auto max-md:w-full">
              <table className="w-full min-w-[600px]">
                <thead>
                  {uploadType === "files" ? (
                    <tr className="bg-[#CEDEFF]">
                      <th className="text-start p-2 text-sm md:text-base">
                        Sr No.
                      </th>
                      <th className="text-start p-2 text-sm md:text-base">
                        File Name
                      </th>
                      <th className="text-start p-2 text-sm md:text-base">
                        File Size
                      </th>
                      <th className="text-start p-2 text-sm md:text-base">
                        File Type
                      </th>
                      <th className="text-start p-2 text-sm md:text-base">
                        Status
                      </th>
                    </tr>
                  ) : (
                    <tr className="bg-[#CEDEFF]">
                      <th className="text-start p-2 text-sm md:text-base">
                        Sr No.
                      </th>
                      <th className="text-start p-2 text-sm md:text-base">
                        Subfolder Name
                      </th>
                      <th className="text-start p-2 text-sm md:text-base">
                        No. of files
                      </th>
                      <th className="text-start p-2 text-sm md:text-base">
                        Status
                      </th>
                      <th className="text-start p-2 text-sm md:text-base">
                        Download
                      </th>
                    </tr>
                  )}
                </thead>
                <tbody>
                  {uploadType === "files"
                    ? paginatedFiles.map((file, index) => (
                        <TableRow
                          key={index}
                          type="files"
                          file={file}
                          index={(currentPage - 1) * rowsPerPage + index}
                          isSelected={selectedRow === file.name}
                          onRowClick={() => setSelectedRow(file.name)}
                        />
                      ))
                    : paginatedSubfolders.map((subfolder, index) => (
                        <TableRow
                          key={index}
                          type="subfolders"
                          file={subfolder}
                          index={(currentPage - 1) * rowsPerPage + index}
                          extractedData={extractedData}
                          isSelected={selectedRow === subfolder.name}
                          onRowClick={() => setSelectedRow(subfolder.name)}
                        />
                      ))}
                </tbody>
              </table>
            </div>
            {totalPages > 1 && (
              <div className="flex justify-between p-4">
                <button
                  onClick={() =>
                    setCurrentPage((prev) => Math.max(prev - 1, 1))
                  }
                  disabled={currentPage === 1}
                  className={`bg-primaryD text-white px-4 py-2 rounded hover:bg-primaryD-dark ${
                    currentPage !== 1
                      ? "hover:bg-primaryD-dark"
                      : "opacity-50 cursor-not-allowed"
                  }`}
                >
                  Previous
                </button>
                <span>
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() =>
                    setCurrentPage((prev) => Math.min(prev + 1, totalPages))
                  }
                  disabled={currentPage === totalPages}
                  className={`bg-primaryD text-white px-4 py-2 rounded hover:bg-primaryD-dark ${
                    currentPage !== totalPages
                      ? "hover:bg-primaryD-dark"
                      : "opacity-50 cursor-not-allowed"
                  }`}
                >
                  Next
                </button>
              </div>
            )}
          </div>
          <div className="flex w-full">
            {uploadType === "files" ? (
              <div className="flex w-full gap-4 flex-wrap justify-center mt-4 items-start">
                {selectedRow &&
                  uploadedFiles
                    .find((file) => file.name === selectedRow)
                    ?.pages?.map((page, index) => (
                      <ExtractedDataDisplay
                        key={index}
                        uploadType={uploadType}
                        selectedRow={selectedRow}
                        setUploadedFiles={setUploadedFiles}
                        page={page}
                        onViewFile={onViewFile}
                      />
                    ))}
              </div>
            ) : (
              <div className="flex w-full gap-4 flex-wrap justify-center mt-4 items-start">
                {selectedRow &&
                  uploadedFiles
                    .find((subfolder) => subfolder.name === selectedRow)
                    ?.files.map((file, index) => {
                      const extension = file.name
                        .split(".")
                        .pop()
                        .toLowerCase();

                      if (extension === "pdf") {
                        return file.pages.map((page, index2) => {
                          return (
                            <NestedPDFDataDisplay
                              key={index2}
                              page={page}
                              onViewFile={onViewFile}
                              setUploadedFiles={setUploadedFiles}
                              selectedRow={selectedRow}
                              subFolderfile={file}
                            />
                          );
                        });
                      } else {
                        return (
                          <ExtractedDataDisplay
                            key={index}
                            uploadType={uploadType}
                            selectedRow={selectedRow}
                            setUploadedFiles={setUploadedFiles}
                            subFolderfile={file}
                            onViewFile={onViewFile}
                          />
                        );
                      }
                    })}
              </div>
            )}
            {viewer && (
              <div className="w-1/2 sticky top-20 max-h-[80vh] border-[1px] border-[#D2D0CE] rounded-lg p-4 mt-4 mx-2 overflow-auto">
                {(() => {
                  const currentFile = displayFiles.find(
                    (file) => file.name === viewer
                  );

                  if (!currentFile) return null;

                  const { type, src } = currentFile;

                  return (
                    <div>
                      <div className="flex justify-between items-center mb-4">
                        <p className="text-xl font-bold max-w-[70%] overflow-hidden text-ellipsis">
                          {viewer}
                        </p>
                        {type === "pdf" && (
                          <p className="bg-primaryL px-2 py-1 rounded-lg text-primaryD font-semibold">
                            Page {viewerPageNumber}
                          </p>
                        )}
                      </div>

                      {type === "image" ? (
                        <img
                          className="rounded-lg w-full h-auto object-contain"
                          src={src}
                        />
                      ) : (
                        <Document className="w-full h-auto" file={src}>
                          <Page
                            className="w-full h-auto"
                            pageNumber={viewerPageNumber}
                            renderMode="canvas"
                            scale={0.8}
                          />
                        </Document>
                      )}
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
          {/* {selectedRow && (
            <div className="text-xl mt-4">
              <p className="font-semibold">{`Common Vehicle Number:`}</p>
              <p className="font-bold">{`${removeConfidenceValue(
                getCommonVehicleNumber(selectedRow)[0]
              )} (${getCommonVehicleNumber(selectedRow)[1]})`}</p>
            </div>
          )} */}
        </div>
      </div>
      <ToastContainer />
    </div>
  );
}

export default App;
