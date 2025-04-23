import { useEffect, useRef } from "react";
import * as GeoTIFF from "geotiff";

const TiffViewer = ({ url }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    async function loadTiff() {
      console.log("Fetching URL:", url); // Check if the URL is correct
      try {
        const response = await fetch(url);
        console.log("Fetch Response:", response); // Check the response object
        if (!response.ok) {
          console.error(`HTTP error! status: ${response.status}`);
          return;
        }
        const arrayBuffer = await response.arrayBuffer();
        console.log("Array Buffer Length:", arrayBuffer.byteLength); // Check if data was received
        const tiff = await GeoTIFF.fromArrayBuffer(arrayBuffer);
        console.log("TIFF Object:", tiff); // Check if the TIFF object was created
        const image = await tiff.getImage();
        console.log("Image Object:", image); // Check if the image was obtained
        const raster = await image.readRasters({ interleave: true });
        console.log("Raster Data:", raster); // Check the pixel data
        const width = image.getWidth();
        const height = image.getHeight();
        console.log("Width:", width, "Height:", height); // Check dimensions

        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        const imgData = ctx.createImageData(width, height);

        for (let i = 0; i < raster.length; i += 3) {
          imgData.data[i] = raster[i];
          imgData.data[i + 1] = raster[i + 1];
          imgData.data[i + 2] = raster[i + 2];
          imgData.data[i + 3] = 255;
        }

        canvas.width = width;
        canvas.height = height;
        ctx.putImageData(imgData, 0, 0);
        console.log("Image data put on canvas");
      } catch (error) {
        console.error("Error loading TIFF:", error); // Catch any errors during the process
      }
    }

    loadTiff();
  }, [url]);

  return <canvas ref={canvasRef}></canvas>;
};

function OutputViewer() {
  return (
    <>
      <TiffViewer url="http://localhost:5000/tif" />
    </>
  );
}
export default OutputViewer;