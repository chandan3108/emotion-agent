"use client";

import React from "react";

export default function GamesLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="theme-dark games-layout" style={{ minHeight: "100vh", width: "100%" }}>
      {children}
    </div>
  );
}
