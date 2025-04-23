import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function VerifyDataPoints() {

  const [htmlMap, setHtmlMap] = useState(null);
  const navigate=useNavigate();

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('shapefile', file);

    try {
      const response = await fetch('http://localhost:5000/uploadMarkers', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      setHtmlMap(blobUrl);
    } catch (err) {
      console.error('Upload error:', err);
    }
  };



    function UploadButton()
    {
      return( 
        <>
          <input
            type="file"
            accept=".zip"
            id="hiddenInput"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <button
            onClick={() => document.getElementById('hiddenInput').click()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow hover:bg-blue-700 transition duration-300"
          >
            Upload Shapefile
          </button>
        </>
      );
    }

    async function processShapeFiles ()
    {
        try {
      const response = await fetch('http://localhost:5000/processShapefiles', {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      navigate('/Output');
      
    } catch (err) {
      console.error('Upload error:', err);
    }
    }


  return (
    <div className="w-full h-screen flex bg-blue-500  items-center ">

      <div className='w-[20%] h-[90%] border-2 border-amber-200 m-4 rounded-2xl bg-white'> 

            <div className='title h-[10%] bg-orange-400 m-5 rounded-2xl flex items-center justify-center'>
                <h1 className='font-[800] text-white text-3xl'>
                    CROP-MAPPING
                </h1>            
            </div>

            <div className='flex justify-center gap-3 items-center h-[40%] flex-col flex-wrap'>

                <div className='w-[90%] h-auto p-2 bg-amber-200 rounded-2xl flex justify-evenly flex-col'>
                    <h1 className='text-2xl text-center'> Important Notice </h1>
                    <p>
                      You want to upload the outline of the district or place that you have selected
                      Ensure you have zipped your shape files into a single file with extension .zip . 
                    </p>
                </div>

                
                <UploadButton />

            </div>

           { htmlMap && <div className='flex justify-center gap-3 items-center h-[40%] flex-col flex-wrap'>

                <div className='w-[90%] h-auto p-2 bg-amber-200 rounded-2xl flex justify-evenly flex-col'>
                    <h1 className='text-2xl text-center'> Important Notice </h1>
                    <p>
                     If you ok with that uploaded zip file then click the below button to move to next page.
                    </p>
                </div>


                <button className='p-2 bg-blue-400 rounded-2xl' onClick={processShapeFiles}> Proceed</button>

                </div>
            }
      </div>
     

      <div className='w-[87%] h-screen  flex justify-center items-center'>
            {htmlMap!=null?(
              <iframe src={htmlMap} title="Map Viewer" className='w-[90%] h-[90%] rounded-2xl'></iframe>
            ):<div className='w-[90%] h-[90%] rounded-2xl bg-white flex justify-center items-center'>
                <img src="isro.png" />
            </div>}
      </div>
      
    </div>
  );
}



export default VerifyDataPoints;
