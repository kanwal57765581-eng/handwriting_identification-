import React, { useEffect, useState } from "react";
import FileUploadForm from "../../FileUploadForm";
import "../../App.css";
import MenuAppBar from "../../components/Navbar/Navbar";

const Main = () => {
  const [similarity, setSimilarity] = useState(null);
  const [showSplash, setShowSplash] = useState(true);
  const [file1, setFile1] = useState(null);
  const [file2, setFile2] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowSplash(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleSubmit = async () => {
    if (file1 && file2) {
      const formData = new FormData();
      formData.append("image1", file1);
      formData.append("image2", file2);
      try {
        setLoading(true);
        const response = await fetch("http://127.0.0.1:5000/predict", {
          method: "POST",
          body: formData,
        });
        if (response.ok) {
          const result = await response.json();
          setSimilarity(result);
          setFile1(null);
          setFile2(null);
        } else {
          console.log("Error:", response.statusText);
        }
      } catch (err) {
        console.log("Error:", err);
      } finally {
        setLoading(false);
      }
    } else {
      alert("Please select both files before uploading.");
    }
  };

  return (
    <>
      <MenuAppBar />
      <div className="app-container">

        {showSplash && (
          <div className="splash-screen">
            <h1 className="splash-text">Writer Identification App</h1>
          </div>
        )}

        {!showSplash && (
          <>
            <div className="top-border">
              <div className="top-border-line"></div>
              <p className="top-border-eyebrow">Handwriting forensics</p>
              <h1 className="centered-title-white">Who is the Writer?</h1>
              <div className="top-border-line"></div>
            </div>

            <FileUploadForm
              onFileUpload={handleSubmit}
              file1={file1}
              setFile1={setFile1}
              file2={file2}
              setFile2={setFile2}
            />

            {loading && (
              <div className="output-box" style={{ textAlign: "center" }}>
                <h2>Examining the evidence...</h2>
                <p>Please wait while we analyse the handwriting samples.</p>
              </div>
            )}

            {similarity !== null && !loading && (
              <div className="output-box">
                <h2>Analysis Result</h2>
                <p>Sample 1 writer: <strong>{similarity?.author1}</strong></p>
                <p>Sample 2 writer: <strong>{similarity?.author2}</strong></p>
                {similarity?.author1 === similarity?.author2
                  ? <p style={{ color: '#c0392b', marginTop: '12px',
                      fontWeight: 'bold' }}>
                      ✓ Same writer detected!
                    </p>
                  : <p style={{ color: '#56412d', marginTop: '12px',
                      fontWeight: 'bold' }}>
                      ✗ Different writers detected.
                    </p>
                }
              </div>
            )}

            <div className="bottom-border">
              <h1 className="centered-title-white">Identities are Unique!</h1>
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default Main;