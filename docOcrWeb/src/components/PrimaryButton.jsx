import React from "react";

const PrimaryButton = ({ icon, text, ...args }) => {
  return (
    <button
      className=" bg-primaryD text-white px-6 py-3 rounded text-xl flex flex-row items-center gap-4"
      {...args}
    >
      <img className="text-sm" src={icon} alt={icon}/>
      <div className="">{text}</div>
    </button>
  );
};

export default PrimaryButton;
