import ClipLoader from "react-spinners/ClipLoader";
import crossIcon from "../assets/icons/cross.png";
import timeLeftIcon from "../assets/icons/time-left.png";
import editIcon from "../assets/icons/edit.png";
import eyeIcon from "../assets/icons/eye.png";
import { useState } from "react";

const ExtractedDataDisplay = ({
  uploadType,
  selectedRow,
  subFolderfile,
  page,
  setUploadedFiles,
  onViewFile,
}) => {
  const [editable, setEditable] = useState(null);

  const colorCode = (value) => {
    const regex = /<<\((.*?)\)>>/;
    const match = value.match(regex);
    if (match != null && match[1] != "") {
      const confidence = parseFloat(match[1]);
      if (confidence > 95) {
        return "#3c991d";
      } else if (confidence > 80) {
        return "#ffa722";
      } else if (confidence > 15) {
        return "#ff0000"
      } else {
        return "#616161";
      }
    } else {
      return "#000000";
    }
  };

  const removeConfidenceValue = (ans) => {
    const regex = /<<\((.*?)\)>>/;
    const match = ans.match(regex);
    if (match != null) {
      return ans.replace(match[0], "");
    }
    return ans;
  };

  const getCurrentFileStatus = () => {
    if (uploadType === "files") {
      if (page.data) {
        if (page.data === "Failed") {
          return "Failed";
        } else {
          return "Success";
        }
      } else {
        return "Processing";
      }
    } else {
      return subFolderfile.status;
    }
  };

  const parsePdfName = (nameString) => {
    const name = nameString.split("_").slice(0, -2).join("_");
    const page = nameString.split("_")[nameString.split("_").length - 1];

    return [name, page];
  };

  const currentFileData =
    uploadType === "files" ? page.data : subFolderfile.data;

  return (
    <div
      className={`border-[1px] border-[#D2D0CE] rounded-lg duration-300 max-md:w-full max-w-[30vw]`}
    >
      {selectedRow ? (
        <div className="w-full">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold p-4 max-w-[70%] overflow-hidden text-ellipsis">
              {uploadType === "files"
                ? parsePdfName(page.name)[0]
                : subFolderfile.name.split("/")[1]}
            </h2>
            {uploadType === "files" && (
              <p className="bg-primaryL rounded-lg px-2 py-1 font-semibold text-primaryD">
                Page {parsePdfName(page.name)[1]}
              </p>
            )}
            <button
              onClick={() => {
                if (uploadType === "files") {
                  onViewFile(
                    parsePdfName(page.name)[0],
                    parsePdfName(page.name)[1]
                  );
                } else {
                  onViewFile(subFolderfile.name.split("/").slice(1).join("/"));
                }
              }}
              className="p-2 pr-3"
            >
              <img
                src={eyeIcon}
                alt="Eye Icon"
                className="w-[20px] cursor-pointer opacity-50 hover:opacity-75 active:opacity-100 duration-300"
              />
            </button>
          </div>
          {getCurrentFileStatus() === "Success" ? (
            parseFloat(currentFileData["Category Confidence"]) * 100 > 80 ? (
              <div className="w-full pb-4">
                <table className="w-full border-collapse">
                  <tbody className="w-full">
                    {currentFileData &&
                      Object.entries(currentFileData)
                        .filter(([key, value]) => key != "Category Confidence")
                        .map(([key, value], index) => {
                          return (
                            <tr
                              key={index}
                              className={`w-full ${
                                index % 2 === 0 ? "bg-[#e8f0ff]" : ""
                              }`}
                            >
                              <td className="py-2 px-4 text-sm md:text-base font-semibold">
                                {key}
                              </td>
                              {editable !== key ? (
                                <td
                                  className={`py-2 pl-4 pr-2 text-sm md:text-base ${
                                    value === "" ? "text-[#999]" : ""
                                  }`}
                                  style={{ color: colorCode(value) }}
                                >
                                  {value === "" ? (
                                    <p className="text-[#777]">N/A</p>
                                  ) : (
                                    removeConfidenceValue(value)
                                  )}
                                </td>
                              ) : (
                                <td>
                                  <input
                                    className={`w-full ${
                                      index % 2 === 0
                                        ? "bg-[#e8f0ff]"
                                        : "bg-[#fff]"
                                    } outline-dashed outline-1 py-2 pl-4 text-sm md:text-base rounded outline-primary`}
                                    value={removeConfidenceValue(value)}
                                    onKeyDown={(e) => {
                                      if (e.key === "Enter") {
                                        e.target.blur();
                                        setEditable(null);
                                      }
                                    }}
                                    onChange={(e) => {
                                      setUploadedFiles((prevUploadedFiles) => {
                                        return prevUploadedFiles.map(
                                          (prevUploadedFile) => {
                                            if (
                                              prevUploadedFile.name ===
                                              selectedRow
                                            ) {
                                              if (uploadType === "files") {
                                                return {
                                                  ...prevUploadedFile,
                                                  pages:
                                                    prevUploadedFile.pages.map(
                                                      (_page) => {
                                                        if (
                                                          _page.name ===
                                                          page.name
                                                        ) {
                                                          return {
                                                            ..._page,
                                                            data: {
                                                              ..._page.data,
                                                              [editable]:
                                                                e.target.value,
                                                            },
                                                          };
                                                        } else {
                                                          return _page;
                                                        }
                                                      }
                                                    ),
                                                };
                                              } else {
                                                return {
                                                  ...prevUploadedFile,
                                                  files:
                                                    prevUploadedFile.files.map(
                                                      (_file) => {
                                                        if (
                                                          _file.name ===
                                                          subFolderfile?.name
                                                        ) {
                                                          return {
                                                            ..._file,
                                                            data: {
                                                              ..._file.data,
                                                              [editable]:
                                                                e.target.value,
                                                            },
                                                          };
                                                        } else {
                                                          return _file;
                                                        }
                                                      }
                                                    ),
                                                };
                                              }
                                            } else {
                                              return prevUploadedFile;
                                            }
                                          }
                                        );
                                      });
                                    }}
                                  />
                                </td>
                              )}
                              <td>
                                {key !== "Category" && (
                                  <div className="w-[15px] mx-2">
                                    <img
                                      onClick={() => {
                                        editable === key
                                          ? setEditable(null)
                                          : setEditable(key);
                                      }}
                                      className="w-full cursor-pointer opacity-30 hover:opacity-75 active:opacity-100 duration-300 "
                                      src={editIcon}
                                      alt="Edit Icon"
                                    />
                                  </div>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 bg-[#e8f0ff] flex items-center justify-center gap-4 rounded-b-lg">
                <img className="w-[25px]" src={crossIcon} alt="Cross Icon" />
                <p className="text-[#ff0000] text-lg text-center">
                  Image Category not Recognized
                </p>
              </div>
            )
          ) : getCurrentFileStatus() === "Processing" ? (
            <div className="py-8 px-4 bg-[#e8f0ff] flex items-center justify-center gap-4 rounded-b-lg">
              <ClipLoader loading={true} color={"#07004D"} size={30} />
              <p className="text-lg">Processing Document</p>
            </div>
          ) : getCurrentFileStatus() === "Pending" ? (
            <div className="py-8 px-4 bg-[#e8f0ff] flex items-center justify-center gap-4 rounded-b-lg">
              <img className="w-[25px]" src={timeLeftIcon} alt="Cross Icon" />
              <p className="text-lg">Document in Queue</p>
            </div>
          ) : (
            <div className="py-8 px-4 bg-[#e8f0ff] flex items-center justify-center gap-4 rounded-b-lg">
              <img className="w-[25px]" src={crossIcon} alt="Cross Icon" />
              <p className="text-[#ff0000] text-lg">Error Loading Data</p>
            </div>
          )}
        </div>
      ) : (
        <p className="p-4">Select a row to view details</p>
      )}
    </div>
  );
};

export default ExtractedDataDisplay;
