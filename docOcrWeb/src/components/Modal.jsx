import { useEffect } from "react";

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

export default function Modal({ open, setOpen, modalData }) {
  return (
    <div className="fixed">
      <img src={modalData}/>
    </div>
  );
}
