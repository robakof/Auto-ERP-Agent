"use client";

import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-3xl font-bold">Witaj, {user?.username}</h1>
      <p className="text-lg text-muted-foreground">
        Saldo: {user?.heart_balance ?? 0} serc
      </p>
      <button
        onClick={logout}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
      >
        Wyloguj
      </button>
    </main>
  );
}
