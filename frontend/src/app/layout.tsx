import "./globals.css";
import { VoiceProvider } from "@/contexts/voice-context";

export const metadata = {
  title: "QHacks 2026",
};

export default function RootLayout({
  children,
}: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <VoiceProvider>{children}</VoiceProvider>
      </body>
    </html>
  );
}
