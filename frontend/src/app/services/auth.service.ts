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
  private apiUrl = '/api';
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
