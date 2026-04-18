import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function VerifyEmailSentPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <CardTitle className="text-2xl">Sprawdz email</CardTitle>
          <CardDescription>
            Wyslalismy link weryfikacyjny na Twoj adres email.
            Kliknij link w wiadomosci, aby aktywowac konto.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild variant="outline" className="w-full">
            <Link href="/login">Przejdz do logowania</Link>
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
