"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import Link from "next/link";
import HCaptcha from "@hcaptcha/react-hcaptcha";

import { useAuth } from "@/hooks/use-auth";
import { registerSchema, type RegisterFormData } from "@/lib/validators/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const HCAPTCHA_SITEKEY = process.env.NEXT_PUBLIC_HCAPTCHA_SITEKEY ?? "";

export default function RegisterPage() {
  const router = useRouter();
  const { user, register: authRegister, isLoading } = useAuth();
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [captchaKey, setCaptchaKey] = useState(0);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      tos_accepted: false as unknown as true,
      privacy_policy_accepted: false as unknown as true,
    },
  });

  useEffect(() => {
    if (user) router.replace("/dashboard");
  }, [user, router]);

  const onSubmit = async (data: RegisterFormData) => {
    if (!captchaToken && HCAPTCHA_SITEKEY) {
      toast.error("Wykonaj weryfikacje captcha");
      return;
    }
    try {
      await authRegister({
        email: data.email,
        username: data.username,
        password: data.password,
        tos_accepted: true,
        privacy_policy_accepted: true,
        captcha_token: captchaToken,
      });
      router.push("/verify-email-sent");
    } catch (err) {
      setCaptchaKey((k) => k + 1);
      setCaptchaToken(null);
      if (err instanceof ApiError) {
        toast.error(err.detail);
      } else {
        toast.error("Wystapil nieoczekiwany blad");
      }
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Rejestracja</CardTitle>
          <CardDescription>Utworz konto w serwisie Serce</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="jan@example.com"
                autoComplete="email"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="username">Nazwa uzytkownika</Label>
              <Input
                id="username"
                type="text"
                placeholder="janek123"
                autoComplete="username"
                {...register("username")}
              />
              {errors.username && (
                <p className="text-sm text-red-500">{errors.username.message}</p>
              )}
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="password">Haslo</Label>
              <Input
                id="password"
                type="password"
                placeholder="Min. 8 znakow"
                autoComplete="new-password"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-sm text-red-500">{errors.password.message}</p>
              )}
            </div>

            <div className="flex items-start gap-2">
              <input
                id="tos_accepted"
                type="checkbox"
                className="mt-1"
                {...register("tos_accepted")}
              />
              <Label htmlFor="tos_accepted" className="text-sm font-normal">
                Akceptuje regulamin serwisu
              </Label>
            </div>
            {errors.tos_accepted && (
              <p className="-mt-2 text-sm text-red-500">{errors.tos_accepted.message}</p>
            )}

            <div className="flex items-start gap-2">
              <input
                id="privacy_policy_accepted"
                type="checkbox"
                className="mt-1"
                {...register("privacy_policy_accepted")}
              />
              <Label htmlFor="privacy_policy_accepted" className="text-sm font-normal">
                Akceptuje polityke prywatnosci
              </Label>
            </div>
            {errors.privacy_policy_accepted && (
              <p className="-mt-2 text-sm text-red-500">{errors.privacy_policy_accepted.message}</p>
            )}

            {HCAPTCHA_SITEKEY && (
              <div className="flex justify-center">
                <HCaptcha
                  key={captchaKey}
                  sitekey={HCAPTCHA_SITEKEY}
                  onVerify={setCaptchaToken}
                  onExpire={() => setCaptchaToken(null)}
                  onError={() => toast.error("Weryfikacja nie powiodla sie")}
                />
              </div>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Rejestracja..." : "Zarejestruj sie"}
            </Button>

            <div className="text-center text-sm">
              <Link href="/login" className="text-primary hover:underline">
                Masz konto? Zaloguj sie
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
