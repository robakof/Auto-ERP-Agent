import { api } from "./client";
import type {
  UserRead,
  UpdateProfileRequest,
  ChangeUsernameRequest,
  ChangeEmailRequest,
  ChangePhoneRequest,
  ChangePasswordRequest,
  SoftDeleteBody,
  MessageResponse,
} from "./types";

export const users = {
  getMe: () =>
    api.get<UserRead>("/users/me"),

  updateProfile: (data: UpdateProfileRequest) =>
    api.patch<UserRead>("/users/me", data),

  changeUsername: (data: ChangeUsernameRequest) =>
    api.post<MessageResponse>("/users/me/username", data),

  changeEmail: (data: ChangeEmailRequest) =>
    api.post<MessageResponse>("/users/me/email", data),

  confirmEmailChange: (data: { token: string }) =>
    api.post<MessageResponse>("/users/me/email/confirm", data),

  changePhone: (data: ChangePhoneRequest) =>
    api.post<MessageResponse>("/users/me/phone", data),

  verifyPhoneChange: (data: { new_phone_number: string; code: string }) =>
    api.post<MessageResponse>("/users/me/phone/verify", data),

  changePassword: (data: ChangePasswordRequest) =>
    api.post<MessageResponse>("/users/me/password", data),

  deleteAccount: (data: SoftDeleteBody) =>
    api.delete<MessageResponse>("/users/me", data),
};
