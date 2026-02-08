"use client";

import {
  CRM_DATABASE_VALUE,
  DashboardProvider,
  useDashboard,
} from "@/app/dashboard/dashboard-context";
import { AppSidebar } from "@/components/app-sidebar";
import { BoohooRive } from "@/components/boohoo-rive";
import { GlowEffect } from "@/components/glow-effect";
import { SiteHeader } from "@/components/site-header";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { ChatMessageView } from "@/components/chat-message-view";
import { useAudioRecorder } from "@/hooks/use-audio-recorder";
import { useBackendChat } from "@/hooks/use-backend-chat";
import { useTextToSpeech } from "@/hooks/use-text-to-speech";
import { createClient } from "@/lib/supabase/client";
import type { User } from "@supabase/supabase-js";
import { ArrowRight, Loader2, Mic, Volume, VolumeX } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useVoice } from "@/contexts/voice-context";

function mapSupabaseUser(user: User): {
  name: string;
  email: string;
  avatar: string;
} {
  const name =
    user.user_metadata?.full_name ??
    user.user_metadata?.name ??
    user.email?.split("@")[0] ??
    "User";
  const email = user.email ?? "";
  const avatar =
    user.user_metadata?.avatar_url ?? user.user_metadata?.picture ?? "";
  return { name, email, avatar };
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [showGlow, setShowGlow] = useState(false);
  const router = useRouter();

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.shiftKey && (e.key === "U" || e.key === "u")) {
      e.preventDefault();
      setShowGlow((prev) => !prev);
    }
  }, []);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
      if (!session?.user) {
        router.replace("/");
      }
    });
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      if (!session?.user) {
        router.replace("/");
      }
    });
    return () => subscription.unsubscribe();
  }, [router]);

  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.replace("/");
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const sidebarUser = mapSupabaseUser(user);

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <DashboardProvider>
        <DashboardLayoutContent
          user={sidebarUser}
          onLogout={handleLogout}
          showGlow={showGlow}
        >
          {children}
        </DashboardLayoutContent>
      </DashboardProvider>
    </SidebarProvider>
  );
}

function DashboardLayoutContent({
  user,
  onLogout,
  showGlow,
  children,
}: {
  user: { name: string; email: string; avatar: string };
  onLogout: () => void;
  showGlow: boolean;
  children: React.ReactNode;
}) {
  const { expansionPhase, selectedDatabase, ready } = useDashboard();
  const isExpandingOrHolding =
    expansionPhase === "expanding" || expansionPhase === "holding";
  const isCrmSelected = selectedDatabase === CRM_DATABASE_VALUE;
  const boohooFullWidth = isCrmSelected;

  return (
    <>
      <AppSidebar variant="inset" user={user} onLogout={onLogout} />
      <SidebarInset className="min-h-0">
        <SiteHeader />
        <div className="relative flex min-h-0 flex-1 flex-col">
          <div className="@container/main flex min-h-0 flex-1 flex-col gap-2">
            <div
              className={`flex min-h-0 flex-1 gap-4 overflow-hidden px-4 py-4 md:px-6 md:py-6 ${boohooFullWidth ? "justify-end" : ""}`}
            >
              {!boohooFullWidth && (
                <div className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-xl">
                  <div className="min-h-0 flex-1 overflow-auto">{children}</div>
                  <GlowEffect active={showGlow} />
                </div>
              )}
              <div
                className={`relative flex h-full max-h-full shrink-0 flex-col overflow-hidden rounded-xl border border-border bg-zinc-200 dark:bg-zinc-800 transition-[flex-basis] duration-[1.8s] ease-out ${
                  boohooFullWidth
                    ? "basis-full"
                    : isExpandingOrHolding
                      ? "basis-3/4"
                      : "basis-80 md:basis-96"
                }`}
              >
                <BoohooRive glowActive={showGlow} />
                {boohooFullWidth && ready && <CrmReadyOverlay />}
              </div>
            </div>
          </div>
        </div>
      </SidebarInset>
    </>
  );
}

const ML_MODELS = [
  { value: "gpt-4o", label: "GPT-4o", icon: "/openai.png" },
  {
    value: "claude-3-5-sonnet",
    label: "Claude 3.5 Sonnet",
    icon: "/claude.svg",
  },
  { value: "gemini-1-5-pro", label: "Gemini 1.5 Pro", icon: "/gemini.png" },
  { value: "deepseek-r1", label: "DeepSeek R1", icon: "/deepseek.png" },
] as const;

function CrmReadyOverlay() {
  const router = useRouter();
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastSpokenMessageRef = useRef<string>("");
  const [model, setModel] = useState<string>(ML_MODELS[0].value);
  const [isTTSEnabled, setIsTTSEnabled] = useState(true);

  const {
    messages,
    input,
    setInput,
    isLoading,
    pendingMessage,
    handleSubmit,
    handleConfirmation,
    backendHealthy,
    checkHealth,
  } = useBackendChat(router);

  const voiceContext = useVoice();
  const { isRecording, startRecording, stopRecording } = useAudioRecorder();
  const { speak, stop: stopSpeaking, isSpeaking, isSupported: isTTSSupported } = useTextToSpeech();

  useEffect(() => {
    voiceContext.setIsSpeaking(isSpeaking);
  }, [isSpeaking, voiceContext]);
  useEffect(() => {
    voiceContext.setIsListening(isRecording);
  }, [isRecording, voiceContext]);
  useEffect(() => {
    voiceContext.setIsProcessing(isLoading);
  }, [isLoading, voiceContext]);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (!isTTSEnabled || !isTTSSupported) return;
    const last = messages[messages.length - 1];
    if (!last || (last.type !== "answer" && last.type !== "chat")) return;
    if (last.content === lastSpokenMessageRef.current) return;
    lastSpokenMessageRef.current = last.content;
    speak(last.content);
  }, [messages, isTTSEnabled, isTTSSupported, speak]);

  const handleMicClick = async () => {
    if (isRecording) {
      voiceContext.setIsProcessing(true);
      await stopRecording();
      voiceContext.setIsProcessing(false);
    } else {
      await startRecording((transcript) => setInput(transcript));
    }
  };

  const toggleTTS = () => {
    if (isSpeaking) stopSpeaking();
    setIsTTSEnabled((v) => !v);
  };

  return (
    <div
      className="absolute inset-0 z-10 flex flex-col gap-4 px-6 pb-6 pt-4 md:px-8 md:pb-8 md:pt-4 animate-in fade-in-0 duration-700"
      style={{ fontFamily: "Zodiak, sans-serif" }}
    >
      {/* Notes placeholder (static) */}
      <div className="flex shrink-0 justify-center">
        <div className="flex w-full max-w-md min-h-24 flex-col justify-center rounded-lg bg-zinc-400/60 dark:bg-zinc-600/60 px-4 py-3 text-sm text-zinc-700 dark:text-zinc-300">
          <p className="text-balance">Notes or context appear here.</p>
        </div>
      </div>

      {/* Conversation history */}
      <ScrollArea className="flex min-h-0 flex-1">
        <div ref={scrollRef} className="space-y-1 pr-2">
          {messages.length === 0 && (
            <div className="flex items-center justify-center py-6 text-center text-sm text-zinc-500 dark:text-zinc-400">
              <p>Ask a question or click the mic to speak. Use &quot;analysis&quot; for deep analysis.</p>
            </div>
          )}
          {messages.map((msg) => (
            <ChatMessageView
              key={msg.id}
              message={msg}
              onConfirmation={handleConfirmation}
              isLoading={isLoading}
            />
          ))}
        </div>
      </ScrollArea>

      {/* Input + mic + send + model + voice */}
      <div className="flex shrink-0 justify-center">
        <div className="flex w-full max-w-md flex-col gap-3 rounded-lg border border-border bg-white dark:bg-zinc-100 px-4 py-3 text-sm text-zinc-800 dark:text-zinc-900 shadow-sm min-h-24">
          {backendHealthy === false && (
            <p className="text-xs text-amber-600 dark:text-amber-400">
              Backend unavailable. Start the server on port 8000.
            </p>
          )}
          <div className="flex items-center gap-2">
            {isTTSSupported && (
              <button
                type="button"
                onClick={toggleTTS}
                className="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-zinc-200 dark:hover:bg-zinc-600"
                title={isTTSEnabled ? "Voice On" : "Voice Off"}
              >
                {isTTSEnabled ? (
                  <Volume className="size-3.5" />
                ) : (
                  <VolumeX className="size-3.5" />
                )}
              </button>
            )}
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              {isRecording ? (
                <span className="text-red-500 animate-pulse">Recording...</span>
              ) : (
                "Click mic to speak"
              )}
            </span>
          </div>
          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isRecording ? "Speaking..." : "How Can I Help You?"}
              disabled={isLoading}
              className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-zinc-500 dark:placeholder:text-zinc-400 text-base disabled:opacity-60"
              aria-label="How Can I Help You?"
            />
            <button
              type="button"
              onClick={handleMicClick}
              disabled={isLoading}
              className={`flex size-8 shrink-0 items-center justify-center rounded-md transition-colors ${
                isRecording
                  ? "bg-red-600 text-white"
                  : "bg-zinc-200 text-zinc-700 hover:bg-zinc-300 dark:bg-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-500"
              } ${isRecording ? "animate-pulse" : ""}`}
              aria-label={isRecording ? "Stop recording" : "Activate microphone"}
            >
              <Mic className="size-4" />
            </button>
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="flex size-8 shrink-0 items-center justify-center rounded-md bg-foreground text-background hover:opacity-90 transition-opacity disabled:opacity-50"
              aria-label="Send"
            >
              {isLoading ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <ArrowRight className="size-4" />
              )}
            </button>
          </form>
          <Select value={model} onValueChange={setModel}>
            <SelectTrigger
              size="sm"
              className="h-7 w-fit max-w-[10rem] border-zinc-300 dark:border-zinc-600 bg-transparent text-zinc-700 dark:text-zinc-300 text-xs px-2"
            >
              <SelectValue placeholder="Model" />
            </SelectTrigger>
            <SelectContent>
              {ML_MODELS.map((m) => (
                <SelectItem key={m.value} value={m.value}>
                  <span className="flex items-center gap-2">
                    <img src={m.icon} alt="" className="size-3.5 shrink-0 object-contain" />
                    {m.label}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}
