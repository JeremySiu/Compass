"use client";

import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { User } from "@supabase/supabase-js";

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

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

  const handleSignOut = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.replace("/");
  };

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-black">
        <p className="font-sans text-white">Loading…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black p-8">
      <div className="mx-auto max-w-2xl">
        <h1
          className="text-2xl font-normal text-white"
          style={{ fontFamily: "Zodiak, sans-serif" }}
        >
          Signed in as {user.email ?? user.user_metadata?.email ?? "User"}
        </h1>
        <button
          type="button"
          onClick={handleSignOut}
          className="mt-6 inline-flex items-center justify-center rounded-md border-0 bg-white px-6 py-3 text-lg font-normal text-black transition-opacity hover:opacity-90"
          style={{ fontFamily: "Zodiak, sans-serif" }}
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
