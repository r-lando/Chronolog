import { useState, type KeyboardEvent } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "../../context/AuthContext";

const NAV_ITEMS = [
  { label: "Dashboard", to: "/" },
  { label: "Labs", to: "/labs" },
  { label: "CTFs", to: "/ctfs" },
  { label: "Skills", to: "/skills" },
  { label: "Tools", to: "/tools" },
  { label: "MITRE ATT&CK", to: "/mitre" },
  { label: "Evidence", to: "/evidence" },
  { label: "Learning Roadmap", to: "/roadmap" },
  { label: "Portfolio", to: "/portfolio" },
  { label: "Reports", to: "/reports" },
  { label: "Settings", to: "/settings" },
];

export function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchValue, setSearchValue] = useState("");

  function handleSearchSubmit(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && searchValue.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchValue.trim())}`);
    }
  }

  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 bg-surface-900 border-r border-surface-700 flex flex-col">
      <div className="px-5 py-6 border-b border-surface-700">
        <h1 className="text-lg font-bold text-slate-100">TALA</h1>
        <p className="text-xs text-slate-500 mt-0.5">Cybersecurity Lab Journal</p>
      </div>

      <div className="px-3 pt-3">
        <input
          type="search"
          placeholder="Search..."
          className="input-field text-sm py-1.5"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          onKeyDown={handleSearchSubmit}
        />
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              clsx(
                "block px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-accent-500/15 text-accent-400"
                  : "text-slate-400 hover:bg-surface-800 hover:text-slate-200"
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      {user && (
        <div className="px-5 py-4 border-t border-surface-700">
          <p className="text-sm text-slate-300 truncate">{user.display_name}</p>
          <p className="text-xs text-slate-500 truncate mb-3">{user.email}</p>
          <button
            onClick={() => void logout()}
            className="text-xs text-slate-500 hover:text-status-danger transition-colors"
          >
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}
