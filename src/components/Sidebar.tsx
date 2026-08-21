"use client";


import Image from "next/image";
import {
  Home,
  Volume2,
  Mic2,
  Library,
  Copy,
  FileText,
  LogOut,
  Sparkles,
  ChevronDown,
} from "lucide-react";
import { useState } from "react";

export function Sidebar() {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const navItems = [
    { label: "Home", icon: Home, badge: null, active: false },
    { label: "Text to Speech", icon: Volume2, badge: null, active: false },
    { label: "Dubbing", icon: Copy, badge: "Beta", active: false },
    { label: "Voice Library", icon: Library, badge: null, active: false },
    { label: "Voice Cloning", icon: Mic2, badge: "Beta", active: false },
    { label: "Speech to Text", icon: FileText, badge: null, active: true },
  ];

  return (
    <aside className="w-16 lg:w-64 glass-sidebar flex flex-col justify-between h-screen sticky top-0 transition-all duration-200 z-30 select-none">
      {/* Top Header & Logo */}
      <div>
        <div className="h-16 border-b border-white/40 flex items-center px-4 lg:px-6 gap-3">
          <div className="w-9 h-9 relative rounded-xl border border-[#E5E5E5] bg-[#FAFAFA] flex items-center justify-center shrink-0">
            <Image
              src="/assets/hhgoa/logo.png"
              alt="HHGOA Logo"
              width={26}
              height={26}
              className="object-contain"
            />
          </div>
          <div className="hidden lg:flex flex-col">
            <span className="font-heading font-bold text-base tracking-tight text-[#111111] leading-none flex items-center gap-2">
              hhgoa
              <Image src="/assets/hhgoa/goa_hindi.svg" alt="Goa Hindi" width={32} height={16} />
            </span>
            <span className="text-[10px] text-gray-600 font-bold uppercase tracking-wider mt-0.5">
              Content Agents
            </span>
          </div>
        </div>

        {/* Navigation Section */}
        <div className="p-3 lg:p-4">
          <div className="hidden lg:block text-[11px] font-semibold uppercase tracking-wider text-gray-400 px-3 mb-2">
            Content Agents
          </div>

          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.label}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    item.active
                      ? "bg-white/60 text-[#111111] font-semibold border border-white/80 shadow-subtle"
                      : "text-gray-700 hover:bg-white/40 hover:text-black"
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${item.active ? "text-[#111111]" : "text-gray-400"}`} />
                  <span className="hidden lg:inline flex-1 text-left">{item.label}</span>
                  {item.badge && (
                    <span className="hidden lg:inline-block text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-[#FF6B00] text-white uppercase">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Bottom User Account Menu */}
      <div className="p-3 lg:p-4 border-t border-white/40 relative">
        <div className="hidden lg:flex justify-center mb-4 opacity-80 mix-blend-multiply">
          <Image src="/assets/hhgoa/2-47.svg" alt="2:47 pm Studio" width={80} height={40} />
        </div>
        {isUserMenuOpen && (
          <div className="absolute bottom-16 left-3 right-3 bg-white border border-[#E5E5E5] rounded-2xl p-2 shadow-float z-50 animate-in fade-in slide-in-from-bottom-2">
            <div className="px-3 py-2 border-b border-[#E5E5E5] mb-1">
              <p className="text-xs font-semibold text-[#111111] truncate">
                Goa Builder
              </p>
              <p className="text-[11px] text-gray-500 truncate">
                builder@hhgoa.com
              </p>
            </div>
            <button
              onClick={() => console.log("Sign Out")}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-600 hover:bg-red-50 rounded-xl transition-colors font-medium"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>
          </div>
        )}

        <button
          onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
          className="w-full flex items-center justify-between p-2 rounded-xl hover:bg-[#FAFAFA] transition-colors"
        >
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-[#111111] text-white font-bold text-xs flex items-center justify-center shrink-0">
              G
            </div>
            <div className="hidden lg:flex flex-col text-left overflow-hidden">
              <span className="text-xs font-semibold text-[#111111] truncate">
                Goa Builder
              </span>
              <span className="text-[10px] text-gray-400 truncate">Pro Account</span>
            </div>
          </div>
          <ChevronDown className="hidden lg:block w-3.5 h-3.5 text-gray-400" />
        </button>
      </div>
    </aside>
  );
}
