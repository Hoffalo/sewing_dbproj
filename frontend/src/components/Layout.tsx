import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      <Sidebar />
      <main className="flex-1 min-w-0 ml-[260px] px-10 py-10">
        <Outlet />
      </main>
    </div>
  );
}
