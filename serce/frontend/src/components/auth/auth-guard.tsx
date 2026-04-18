"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { AuthSkeleton } from "./auth-skeleton";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isHydrated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isHydrated && !isLoading && !user) {
      router.replace("/login");
    }
  }, [isHydrated, isLoading, user, router]);

  if (!isHydrated || isLoading) {
    return <AuthSkeleton />;
  }

  if (!user) return null; // redirecting

  return <>{children}</>;
}
