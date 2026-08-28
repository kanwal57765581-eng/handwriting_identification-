import React, { useState } from "react";
import MenuAppBar from "../../components/Navbar/Navbar";
import "../../App.css";

const Register = () => {
const [authorName, setAuthorName] = useState("");
const [registerFile, setRegisterFile] = useState(null);
const [registerResult, setRegisterResult] = useState(null);
const [registerLoading, setRegisterLoading] = useState(false);
const [preview, setPreview] = useState(null);

const handleFileChange = (e) => {
    const file = e.target.files[0];
    setRegisterFile(file);
    if (file) {
    const reader = new FileReader();
    reader.onload = (ev) => setPreview(ev.target.result);
    reader.readAsDataURL(file);
    }
};

const handleRegister = async () => {
    if (!authorName || !registerFile) {
    alert("Please enter author name and upload an image!");
    return;
    }
    const formData = new FormData();
    formData.append("author_name", authorName);
    formData.append("image", registerFile);
    try {
    setRegisterLoading(true);
    setRegisterResult(null);
    const response = await fetch("http://127.0.0.1:5000/register", {
        method: "POST",
        body: formData,
    });
    const result = await response.json();
    setRegisterResult(result);
    setAuthorName("");
    setRegisterFile(null);
    
    } catch (err) {
    setRegisterResult({ error: "Something went wrong!" });
    } finally {
    setRegisterLoading(false);
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
        <h1 className="centered-title-white"style={{ fontSize: '40px' }}>Register New Author</h1>
        <div className="top-border-line"></div>
        </div>

        {/* REGISTER FORM */}
        <div className="output-box" style={{ maxWidth: '550px',
        margin: '20px auto' }}>

        <h2 style={{ marginBottom: '10px', color: '#2c2c2c' }}>
            📝 Add New Author
        </h2>

        {/* Author Name */}
        <p style={{ fontWeight: 'bold', marginBottom: '8px',
            color: '#56412d' }}>
            Author Name
        </p>
        <input
            type="text"
            placeholder="Enter author name"
            value={authorName}
            onChange={(e) => setAuthorName(e.target.value)}
            style={{
            width: '100%',
            padding: '12px',
            marginBottom: '20px',
            border: '1px solid #c0392b',
            borderRadius: '8px',
            fontSize: '15px',
            backgroundColor: '#faf8f5',
            fontFamily: 'inherit',
            boxSizing: 'border-box'
            }}
        />

        {/* Upload Area */}
        <p style={{ fontWeight: 'bold', marginBottom: '8px',
            color: '#56412d' }}>
            Handwriting Sample
        </p>
        <div
            onClick={() =>
            document.getElementById('registerInput').click()}
            style={{
            border: '2px dashed #c0392b',
            borderRadius: '5px',
            padding: '15px',
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
                maxHeight: '150px',
                borderRadius: '8px',
                border: '1px solid #ddd',
                marginBottom: '8px'
                }}
            />
            ) : (
            <div style={{ fontSize: '40px' }}>📄</div>
            )}
            <p style={{ color: '#56412d', marginTop: '10px' }}>
            {registerFile
                ? `✅ ${registerFile.name}`
                : 'Click to upload handwriting image'}
            </p>
            <p style={{ color: '#aaa', fontSize: '12px' }}>
            PNG, JPG supported
            </p>
            <input
            id="registerInput"
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleFileChange}
            />
        </div>

        {/* Register Button */}
        <button
            onClick={handleRegister}
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
            {registerLoading ? '⏳ Registering...' : 'Register Author'}
        </button>

        {/* Result */}
        {registerResult && (
            <div style={{
            marginTop: '20px',
            padding: '15px',
            borderRadius: '10px',
            textAlign: 'center',
            backgroundColor: registerResult.message
                ? '#eafaf1' : '#fdecea',
            border: registerResult.message
                ? '1px solid #27ae60' : '1px solid #e74c3c',
            color: registerResult.message ? '#27ae60' : '#e74c3c',
            fontWeight: 'bold'
            }}>
            {registerResult.message || registerResult.error}
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

export default Register;