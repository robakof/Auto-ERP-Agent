import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Nieprawidlowy email"),
  password: z.string().min(1, "Haslo wymagane"),
});

export const registerSchema = z.object({
  email: z.string().email("Nieprawidlowy email"),
  username: z
    .string()
    .min(3, "Min. 3 znaki")
    .max(30, "Max. 30 znakow"),
  password: z
    .string()
    .min(8, "Min. 8 znakow")
    .max(128, "Max. 128 znakow"),
  tos_accepted: z.literal(true, {
    error: "Wymagana akceptacja regulaminu",
  }),
  privacy_policy_accepted: z.literal(true, {
    error: "Wymagana akceptacja polityki prywatnosci",
  }),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
