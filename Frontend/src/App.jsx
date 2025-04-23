import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";

import { Outline,VerifyDataPoints,OutputViewer } from "./pages";

function App() {
  return (
    <Router>
        <Routes>
          <Route path="/" element={<Outline />} />
          <Route path="/VerifyDataPoints" element={<VerifyDataPoints />} />
          <Route path="/Output" element={<OutputViewer />} />

        </Routes>
      
    </Router>
  );
}

export default App;
