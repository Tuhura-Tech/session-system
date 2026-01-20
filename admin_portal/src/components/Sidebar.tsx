import React from "react";
import { NavLink } from "react-router-dom";
import {
  Home,
  Calendar,
  MapPin,
  Clock,
  XCircle,
  BookOpen,
  LogOut,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const Sidebar: React.FC = () => {
  const { logout } = useAuth();

  const navItems = [
    { to: "/dashboard", icon: Home, label: "Dashboard" },
    { to: "/sessions", icon: Calendar, label: "Sessions" },
    { to: "/locations", icon: MapPin, label: "Locations" },
    { to: "/terms", icon: Clock, label: "Terms" },
    { to: "/students", icon: BookOpen, label: "Students" },
    { to: "/exclusions", icon: XCircle, label: "Exclusions" },
  ];

  return (
    <div className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold">Admin Portal</h1>
      </div>

      <nav className="flex-1 px-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg mb-2 transition-colors ${
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
        >
          <LogOut className="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
