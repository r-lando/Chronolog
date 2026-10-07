import { api } from "./client";
import type { LoginPayload, RegisterPayload, User } from "../types/user";

export const authApi = {
  register: (payload: RegisterPayload) => api.post<User>("/auth/register", payload),
  login: (payload: LoginPayload) => api.post<User>("/auth/login", payload),
  logout: () => api.post<void>("/auth/logout"),
  me: () => api.get<User>("/auth/me"),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<void>("/auth/password", { current_password: currentPassword, new_password: newPassword }),
};
