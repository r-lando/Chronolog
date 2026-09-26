export interface User {
  id: string;
  email: string;
  display_name: string;
  role: string;
  created_at: string;
}

export interface RegisterPayload {
  email: string;
  display_name: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}
