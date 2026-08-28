import React, { useState } from "react";
import MenuAppBar from "../../components/Navbar/Navbar";
import "../../App.css";

const Identify = () => {
const [identifyFile, setIdentifyFile] = useState(null);
const [identifyResult, setIdentifyResult] = useState(null);
const [identifyLoading, setIdentifyLoading] = useState(false);
const [preview, setPreview] = useState(null);

const handleFileChange = (e) => {
    const file = e.target.files[0];
    setIdentifyFile(file);
    if (file) {
    const reader = new FileReader();
    reader.onload = (ev) => setPreview(ev.target.result);
    reader.readAsDataURL(file);
    }
};

const handleIdentify = async () => {
    if (!identifyFile) {
    alert("Please upload a handwriting image!");
    return;
    }
    const formData = new FormData();
    formData.append("image", identifyFile);
    try {
    setIdentifyLoading(true);
    setIdentifyResult(null);
    const response = await fetch("http://127.0.0.1:5000/identify", {
        method: "POST",
        body: formData,
    });
    const result = await response.json();
    setIdentifyResult(result);
    setIdentifyFile(null);
    
    } catch (err) {
    setIdentifyResult({ error: "Something went wrong!" });
    } finally {
    setIdentifyLoading(false);
    }
};

return (
    <>
    <MenuAppBar />
    <div className="app-container">

        {/* HERO */}
        <div className="top-border">
        <div className="top-border-line"></div>
        <p className="top-border-eyebrow">Handwriting forensics</p>
        <h1 className="centered-title-white">Identify Writer</h1>
        <div className="top-border-line"></div>
        </div>

        {/* IDENTIFY FORM */}
        <div className="output-box" style={{ maxWidth: '550px',
        margin: '40px auto' }}>

        <h2 style={{ marginBottom: '20px', color: '#2c2c2c' }}>
            🔍 Upload Unknown Handwriting
        </h2>

        {/* Upload Area */}
        <div
            onClick={() =>
            document.getElementById('identifyInput').click()}
            style={{
            border: '2px dashed #c0392b',
            borderRadius: '10px',
            padding: '20px',
            textAlign: 'center',
            marginBottom: '15px',
            backgroundColor: '#faf8f5',
            cursor: 'pointer'
            }}
        >
            {preview ? (
            <img
                src={preview}
                alt="preview"
                style={{
                maxWidth: '100%',
                maxHeight: '180px',
                borderRadius: '8px',
                border: '1px solid #ddd',
                marginBottom: '8px'
                }}
            />
            ) : (
            <div style={{ fontSize: '40px' }}>🔍</div>
            )}
            <p style={{ color: '#56412d', marginTop: '10px' }}>
            {identifyFile
                ? `✅ ${identifyFile.name}`
                : 'Click to upload handwriting image'}
            </p>
            <p style={{ color: '#aaa', fontSize: '12px' }}>
            PNG, JPG supported
            </p>
            <input
            id="identifyInput"
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleFileChange}
            />
        </div>

        {/* Identify Button */}
        <button
            onClick={handleIdentify}
            style={{
            width: '100%',
            padding: '14px',
            backgroundColor: '#1a1a1a',
            color: 'white',
            border: '2px solid #c0392b',
            borderRadius: '8px',
            fontSize: '16px',
            cursor: 'pointer',
            fontFamily: 'inherit'
            }}
        >
            {identifyLoading ? '⏳ Identifying...' : 'Identify Writer'}
        </button>

        {/* Result */}
        {identifyResult && (
            <div style={{ marginTop: '10px' }}>
            {identifyResult.error
                ? <div style={{
                    padding: '15px',
                    borderRadius: '10px',
                    backgroundColor: '#fdecea',
                    border: '1px solid #e74c3c',
                    color: '#e74c3c',
                    fontWeight: 'bold',
                    textAlign: 'center'
                }}>
                    ❌ {identifyResult.error}
                </div>
                : <div style={{
                    padding: '20px',
                    borderRadius: '10px',
                    backgroundColor: '#eafaf1',
                    border: '1px solid #27ae60',
                    textAlign: 'center'
                }}>
                    <p style={{ fontSize: '16px', color: '#56412d' }}>
                    This handwriting belongs to
                    </p>
                    <p style={{
                    fontSize: '32px',
                    fontWeight: 'bold',
                    color: '#c0392b',
                    margin: '10px 0'
                    }}>
                    {identifyResult.author}
                    </p>
                    <p style={{ color: '#27ae60', fontWeight: 'bold' }}>
                    Confidence: {identifyResult.confidence}
                    </p>
                    <p style={{ color: '#56412d', marginTop: '5px' }}>
                    Source: {identifyResult.source}
                    </p>
                </div>
            }
            </div>
        )}
        </div>

        {/* FOOTER */}
        <div className="bottom-border">
        <h1 className="centered-title-white">Identities are Unique!</h1>
        </div>

    </div>
    </>
);
};

export default Identify;