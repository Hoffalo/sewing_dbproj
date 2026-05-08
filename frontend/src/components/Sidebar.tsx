import { NavLink } from "react-router-dom";
import { Home, KanbanSquare, Users, LogOut, Scissors } from "lucide-react";
import toast from "react-hot-toast";

import { useLogout, useMe } from "../lib/queries";

const navItems = [
  { to: "/", label: "Home", icon: Home, end: true },
  { to: "/crm", label: "CRM", icon: KanbanSquare, end: false },
  { to: "/clients", label: "Clients", icon: Users, end: false },
];

export default function Sidebar() {
  const { data: user } = useMe();
  const logout = useLogout();

  return (
    <aside className="fixed top-0 left-0 h-screen w-[260px] flex flex-col px-5 py-6 border-r border-lavender-100 bg-white/60 backdrop-blur-sm z-30">
      <div className="flex items-center gap-3 px-2 mb-10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-lavender-300 to-lavender-600 flex items-center justify-center shadow-glow">
          <Scissors className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="font-semibold text-ink leading-tight">Costuras</div>
          <div className="font-semibold text-lavender-600 leading-tight -mt-0.5">
            Lucía
          </div>
        </div>
      </div>

      <nav className="flex-1 flex flex-col gap-1.5">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              [
                "group flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[15px] font-medium transition-all duration-200",
                isActive
                  ? "bg-gradient-to-r from-lavender-50 to-transparent text-lavender-700 shadow-soft"
                  : "text-ink-soft hover:bg-lavender-50/60 hover:text-ink",
              ].join(" ")
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  className={[
                    "w-5 h-5 transition-colors",
                    isActive
                      ? "text-lavender-600"
                      : "text-ink-soft group-hover:text-lavender-500",
                  ].join(" ")}
                  strokeWidth={2}
                />
                <span>{label}</span>
                {isActive && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-lavender-500 shadow-glow" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto pt-4 border-t border-lavender-100">
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-lavender-200 to-lavender-400 flex items-center justify-center text-white text-sm font-semibold shadow-soft">
            {(user?.full_name ?? "?").slice(0, 1).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-ink truncate">
              {user?.full_name ?? "—"}
            </div>
            <div className="text-xs text-ink-soft truncate">
              {user?.role ?? "User"}
            </div>
          </div>
          <button
            onClick={() =>
              logout.mutate(undefined, {
                onSuccess: () => toast.success("Signed out"),
              })
            }
            className="p-2 rounded-lg text-ink-soft hover:bg-lavender-50 hover:text-lavender-700 transition-colors"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
