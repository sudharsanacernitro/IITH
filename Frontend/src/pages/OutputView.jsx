import React from "react";

const ImageViewer = ({ url }) => {
  return (
    <img
      src={url}
      alt="Loaded"
      style={{ maxWidth: "100%", height: "100%" }}
      onError={(e) => console.error("Failed to load image:", e)}
    />
  );
};

function OutputViewer() {
  return (
    <div className="w-full h-screen flex justify-center items-center ">
      <div className="w-[80%] h-[90%] border-2 border-black rounded-2xl">
            <ImageViewer url="http://localhost:5000/Output" />
      </div>
    </div>
  );
}

export default OutputViewer;
