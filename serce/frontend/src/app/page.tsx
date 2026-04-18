"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

type HealthStatus = "loading" | "ok" | "error";

export default function Home() {
  const [health, setHealth] = useState<HealthStatus>("loading");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => {
        setHealth(res.ok ? "ok" : "error");
      })
      .catch(() => {
        setHealth("error");
      });
  }, []);

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold tracking-tight">Serce</h1>
      <p className="text-lg text-neutral-600">
        Platforma wzajemnej pomocy
      </p>
      <div className="flex items-center gap-2 rounded-lg border px-4 py-2 text-sm">
        <span>Backend:</span>
        {health === "loading" && (
          <span className="text-neutral-400">sprawdzam...</span>
        )}
        {health === "ok" && (
          <span className="font-medium text-green-600">polaczony</span>
        )}
        {health === "error" && (
          <span className="font-medium text-red-600">niedostepny</span>
        )}
      </div>
    </main>
  );
}
