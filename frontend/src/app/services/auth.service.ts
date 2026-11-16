import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';

export interface User {
  id: string;
  nom: string;
  email: string;
  role: string;
  est_actif: boolean;
  date_creation: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  // Backend FastAPI (dev). Ajuster si le backend tourne sur un autre port/hôte.
  private apiUrl = 'http://127.0.0.1:8001/api';
  private tokenKey = 'access_token';
  private userSubject = new BehaviorSubject<User | null>(null);
  user$ = this.userSubject.asObservable();

  constructor(private http: HttpClient) {
    const token = localStorage.getItem(this.tokenKey);
    if (token) {
      this.me().subscribe({ error: () => this.logout() });
    }
  }

  login(email: string, mot_de_passe: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.apiUrl}/auth/login`, { email, mot_de_passe }).pipe(
      tap(res => {
        localStorage.setItem(this.tokenKey, res.access_token);
        localStorage.setItem('refresh_token', res.refresh_token);
        this.userSubject.next(res.user);
      })
    );
  }

  register(nom: string, email: string, mot_de_passe: string): Observable<User> {
    return this.http.post<User>(`${this.apiUrl}/auth/register`, { nom, email, mot_de_passe, role: 'CANDIDAT' });
  }

  me(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/auth/me`).pipe(
      tap(user => this.userSubject.next(user))
    );
  }

  forgotPassword(email: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.apiUrl}/auth/forgot-password`, { email });
  }

  resetPassword(token: string, nouveau_mot_de_passe: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.apiUrl}/auth/reset-password`, { token, nouveau_mot_de_passe });
  }

  oauthProviders(): Observable<{ google: boolean }> {
    return this.http.get<{ google: boolean }>(`${this.apiUrl}/auth/oauth/providers`);
  }

  /** Navigation pleine page (pas XHR) : le backend redirige vers Google puis revient sur /oauth/callback. */
  startGoogleLogin() {
    window.location.href = `${this.apiUrl}/auth/oauth/google/login`;
  }

  /** Enregistre les jetons recus apres OAuth puis charge l'utilisateur courant. */
  completeOAuth(accessToken: string, refreshToken: string): Observable<User> {
    localStorage.setItem(this.tokenKey, accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    return this.me();
  }

  logout() {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem('refresh_token');
    this.userSubject.next(null);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  getUser(): User | null {
    return this.userSubject.value;
  }
}
