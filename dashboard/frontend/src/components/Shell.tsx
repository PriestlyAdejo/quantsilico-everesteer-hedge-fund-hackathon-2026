import { Outlet } from "react-router";
import TopBar from "./TopBar";
import Sidebar from "./Sidebar";
import ActivityStrip from "./ActivityStrip";
import CommandPalette from "./CommandPalette";
import DocumentTitle from "./DocumentTitle";

export default function Shell() {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      width: "100vw",
      background: "var(--background)",
      overflow: "hidden",
    }}>
      <DocumentTitle />
      <TopBar />
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <Sidebar />
        <main style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          background: "var(--background)",
        }}>
          <Outlet />
        </main>
      </div>
      <ActivityStrip />
      <CommandPalette />
    </div>
  );
}
