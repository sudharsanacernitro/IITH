import React from "react";

const ImageViewer = ({ url }) => {
  return (
    <img
      src={url}
      alt="Loaded"
      style={{ maxWidth: "100%", height: "auto" }}
      onError={(e) => console.error("Failed to load image:", e)}
    />
  );
};

function OutputViewer() {
  return (
    <>
      <ImageViewer url="http://localhost:5000/Output" />
    </>
  );
}

export default OutputViewer;
