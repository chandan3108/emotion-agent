import type { Metadata } from "next";
import { Space_Grotesk, JetBrains_Mono, Caveat } from "next/font/google";
import "./globals.css";
import { Sidebar } from "./components/Sidebar";
import FloatingParticles from "./components/FloatingParticles";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

const caveat = Caveat({
  variable: "--font-caveat",
  subsets: ["latin"],
  weight: ["400", "700"],
});

export const metadata: Metadata = {
  title: "Rem — Your AI Companion",
  description: "A relationship that evolves, remembers, and grows with you.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${spaceGrotesk.variable} ${jetbrainsMono.variable} ${caveat.variable}`} style={{ fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
        <FloatingParticles />
        <div style={{ display: "flex", minHeight: "100vh" }}>
          <Sidebar />
          <main style={{ flex: 1, position: "relative", zIndex: 1 }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}


