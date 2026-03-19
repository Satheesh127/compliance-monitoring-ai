import { Navigate, Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import ChatbotPage from "./pages/ChatbotPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/chatbot" element={<ChatbotPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
