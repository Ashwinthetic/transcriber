"use client";


import Image from "next/image";
import { FileText } from "lucide-react";

export function Sidebar() {
  const navItems = [
    { label: "Speech to Text", icon: FileText, badge: null, active: true },
  ];

  return (
    <aside className="w-16 lg:w-56 glass-sidebar flex flex-col justify-between h-[50vh] sticky top-0 transition-all duration-200 z-30 select-none rounded-br-3xl border-b border-white/15 overflow-hidden">
      {/* Top Header & Logo */}
      <div>
        <div className="h-16 border-b border-white/40 flex items-center px-4 lg:px-6 gap-3">
          <div className="w-9 h-9 relative rounded-xl border border-white/20 bg-white/10 flex items-center justify-center shrink-0">
            <Image
              src="/assets/hhgoa/logo.png"
              alt="HHGOA Logo"
              width={26}
              height={26}
              className="object-contain"
            />
          </div>
          <div className="hidden lg:flex flex-col">
            <span className="font-heading font-bold text-base tracking-tight text-white leading-none flex items-center gap-2">
              hhgoa
              <Image src="/assets/hhgoa/goa_hindi.svg" alt="Goa Hindi" width={32} height={16} />
            </span>
            <span className="text-[10px] text-white/60 font-bold uppercase tracking-wider mt-0.5">
              Content Agents
            </span>
          </div>
        </div>

        {/* Navigation Section */}
        <div className="p-3 lg:p-4">
          <div className="hidden lg:block text-[11px] font-semibold uppercase tracking-wider text-white/50 px-3 mb-2">
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
                      ? "bg-white/20 text-white font-semibold border border-white/30 shadow-subtle"
                      : "text-gray-300 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${item.active ? "text-white" : "text-gray-400"}`} />
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

      {/* Bottom Footer Logo */}
      <div className="p-3 lg:p-4 relative">
        <div className="hidden lg:flex justify-center mb-2">
          <div className="drop-shadow-[0_0_12px_rgba(250,204,21,0.8)] brightness-[1.2] hover:scale-105 transition-transform cursor-pointer">
            <Image src="/assets/hhgoa/2-47.svg" alt="2:47 pm Studio" width={80} height={40} />
          </div>
        </div>
      </div>
    </aside>
  );
}
