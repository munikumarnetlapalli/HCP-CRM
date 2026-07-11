import LogInteractionForm from "./components/LogInteractionForm.jsx";
import AIAssistantChat from "./components/AIAssistantChat.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <div className="split-layout">
        <LogInteractionForm />
        <AIAssistantChat />
      </div>
    </div>
  );
}
