import { api } from "./client";
import type {
  TokenResponse,
  RegisterRequest,
  LoginRequest,
  RefreshRequest,
  MessageResponse,
  SessionRead,
  UserRead,
  VerifyEmailRequest,
  ResendVerificationRequest,
  SendPhoneOtpRequest,
  VerifyPhoneRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
} from "./types";

export const auth = {
  register: (data: RegisterRequest) =>
    api.post<TokenResponse>("/auth/register", data),

  login: (data: LoginRequest) =>
    api.post<TokenResponse>("/auth/login", data),

  refresh: (data: RefreshRequest) =>
    api.post<TokenResponse>("/auth/refresh", data),

  logout: () =>
    api.post<MessageResponse>("/auth/logout"),

  logoutAll: () =>
    api.post<MessageResponse>("/auth/logout-all"),

  getSessions: () =>
    api.get<SessionRead[]>("/auth/sessions"),

  revokeSession: (sessionId: string) =>
    api.delete<MessageResponse>(`/auth/sessions/${sessionId}`),

  getMe: () =>
    api.get<UserRead>("/auth/me"),

  verifyEmail: (data: VerifyEmailRequest) =>
    api.post<MessageResponse>("/auth/verify-email", data),

  resendVerification: (data: ResendVerificationRequest) =>
    api.post<MessageResponse>("/auth/resend-verification", data),

  sendPhoneOtp: (data: SendPhoneOtpRequest) =>
    api.post<MessageResponse>("/auth/send-phone-otp", data),

  verifyPhone: (data: VerifyPhoneRequest) =>
    api.post<MessageResponse>("/auth/verify-phone", data),

  forgotPassword: (data: ForgotPasswordRequest) =>
    api.post<MessageResponse>("/auth/forgot-password", data),

  resetPassword: (data: ResetPasswordRequest) =>
    api.post<MessageResponse>("/auth/reset-password", data),
};
