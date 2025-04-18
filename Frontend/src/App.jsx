import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";

import { Outline,VerifyDataPoints } from "./pages";

function App() {
  return (
    <Router>
        <Routes>
          <Route path="/" element={<Outline />} />
          <Route path="/VerifyDataPoints" element={<VerifyDataPoints />} />
         
        </Routes>
      
    </Router>
  );
}

export default App;
