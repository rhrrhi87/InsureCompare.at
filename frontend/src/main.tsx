// File: frontend/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./i18n/config";
import "./styles/index.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found in index.html");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
