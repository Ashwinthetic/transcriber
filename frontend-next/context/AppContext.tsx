"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import type { QueryResult } from "../app/components/ResultsPanel";

interface BenchmarkData {
  P50_ms: number;
  P70_ms: number;
  P100_ms: number;
  under_200ms_percentage: number;
  total_queries_tested: number;
}

interface AppContextType {
  mounted: boolean;
  introComplete: boolean;
  setIntroComplete: (val: boolean) => void;
  benchData: BenchmarkData | null;
  activeStrategy: string;
  setActiveStrategy: (val: string) => void;
  sttProvider: string;
  setSttProvider: (val: string) => void;
  lang: string;
  setLang: (val: string) => void;
  queryText: string;
  setQueryText: (val: string) => void;
  loading: boolean;
  setLoading: (val: boolean) => void;
  result: QueryResult | null;
  setResult: (val: QueryResult | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const [introComplete, setIntroComplete] = useState(false);
  const [benchData, setBenchData] = useState<BenchmarkData | null>(null);
  
  const [activeStrategy, setActiveStrategy] = useState("sentence_based");
  const [sttProvider, setSttProvider] = useState("sarvam");
  const [lang, setLang] = useState("hi-IN");
  
  const [queryText, setQueryText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);

  useEffect(() => {
    setMounted(true);
    fetch("/api/benchmark")
      .then((r) => r.json())
      .then((d) => setBenchData(d))
      .catch(() => {});
  }, []);

  return (
    <AppContext.Provider
      value={{
        mounted,
        introComplete,
        setIntroComplete,
        benchData,
        activeStrategy,
        setActiveStrategy,
        sttProvider,
        setSttProvider,
        lang,
        setLang,
        queryText,
        setQueryText,
        loading,
        setLoading,
        result,
        setResult,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) throw new Error("useAppContext must be used within AppProvider");
  return context;
}
