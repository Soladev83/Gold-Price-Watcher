import { LogOut, RefreshCw, Settings } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { useManualFetch } from "../hooks/useGoldData";

interface NavbarProps {
  onRefresh?: () => void;
}

export default function Navbar({ onRefresh }: NavbarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { trigger, loading, message } = useManualFetch();

  const handleFetch = async () => {
    await trigger();
    onRefresh?.();
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-10 bg-gray-950/80 backdrop-blur border-b border-gray-800">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-2.5">
          <span className="w-7 h-7 rounded-full bg-gold-500 flex items-center justify-center text-sm font-bold text-gray-950">
            G
          </span>
          <span className="font-semibold text-gray-100 tracking-tight">
            Gold Price Watcher
            <span className="ml-1.5 text-xs font-normal text-gray-500">Ethiopia</span>
          </span>
        </Link>

        <div className="flex items-center gap-2">
          {/* Fetch status message */}
          {message && (
            <span className="text-xs text-gray-400 hidden sm:block max-w-[180px] truncate">
              {message}
            </span>
          )}

          {user && (
            <>
              <button
                onClick={handleFetch}
                disabled={loading}
                title="Fetch latest price now"
                className="flex items-center gap-1.5 text-xs font-medium bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-200 px-3 py-1.5 rounded-lg border border-gray-700 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                <span className="hidden sm:inline">{loading ? "Fetching…" : "Fetch Now"}</span>
              </button>

              <Link
                to="/settings"
                title="Settings"
                className="p-2 text-gray-500 hover:text-gold-400 transition-colors"
              >
                <Settings className="w-4 h-4" />
              </Link>

              <button
                onClick={handleLogout}
                title="Sign out"
                className="p-2 text-gray-500 hover:text-red-400 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
