"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token && pathname !== "/login") {
      setAuthorized(false);
      router.push("/login");
    } else {
      setAuthorized(true);
    }
  }, [pathname, router]);

  useEffect(() => {
    const handleExtensionError = (event: ErrorEvent) => {
      if (
        (event.filename && (event.filename.includes("chrome-extension://") || event.filename.includes("moz-extension://"))) ||
        (event.error?.stack && (event.error.stack.includes("chrome-extension://") || event.error.stack.includes("moz-extension://")))
      ) {
        event.stopImmediatePropagation();
        event.preventDefault();
      }
    };
    window.addEventListener("error", handleExtensionError, true);
    return () => window.removeEventListener("error", handleExtensionError, true);
  }, []);

  // If path is login, we don't guard it
  if (pathname === "/login") {
    return <>{children}</>;
  }

  if (!authorized) {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        background: "#000000",
        color: "#C6AC85",
        fontFamily: "var(--font-mono)",
        fontSize: "0.8rem",
        letterSpacing: "0.15em",
        textTransform: "uppercase"
      }}>
        ◈ REM System / Authenticating...
      </div>
    );
  }

  return <>{children}</>;
}
