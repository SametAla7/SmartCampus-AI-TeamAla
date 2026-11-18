import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

interface UserRecord {
  id: string;
  nom: string;
  email: string;
  role: string;
  est_actif: boolean;
  date_creation: string;
}

interface UsersResponse {
  items: UserRecord[];
  total: number;
  page: number;
  limit: number;
}

interface RagStatus {
  configured: boolean;
  corpus_dir: string | null;
  vector_store: string | null;
  embedding_provider: string | null;
}

@Component({
  selector: 'app-administration',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './administration.component.html',
  styleUrls: ['./administration.component.css']
})
export class AdministrationComponent implements OnInit {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private router = inject(Router);
  private apiUrl = '/api';

  users: UserRecord[] = [];
  selected: UserRecord | null = null;
  rag: RagStatus | null = null;
  filter = '';
  loading = true;
  saving = false;
  reindexing = false;
  error = '';
  success = '';
  form = { nom: '', email: '', role: 'CANDIDAT', mot_de_passe: '' };

  get userName(): string {
    return this.auth.getUser()?.nom || 'Administrateur';
  }

  get initials(): string {
    return this.userName.split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase();
  }

  get filteredUsers(): UserRecord[] {
    const value = this.filter.toLowerCase();
    return this.users.filter(user => !value || user.nom.toLowerCase().includes(value) || user.email.toLowerCase().includes(value) || user.role.toLowerCase().includes(value));
  }

  ngOnInit(): void {
    this.loadUsers();
    this.http.get<RagStatus>(`${this.apiUrl}/admin/rag/status`).subscribe({
      next: status => this.rag = status,
      error: err => this.error = err.error?.detail ?? 'Impossible de charger le statut RAG.'
    });
  }

  select(user: UserRecord): void {
    this.selected = user;
    this.form = { nom: user.nom, email: user.email, role: user.role, mot_de_passe: '' };
    this.success = '';
  }

  resetForm(): void {
    this.selected = null;
    this.form = { nom: '', email: '', role: 'CANDIDAT', mot_de_passe: '' };
    this.success = '';
    this.error = '';
  }

  saveUser(): void {
    if (!this.form.nom.trim() || !this.form.email.trim() || (!this.selected && this.form.mot_de_passe.length < 8) || this.saving) return;
    this.saving = true;
    this.error = '';
    const creating = !this.selected;
    const request = this.selected
      ? this.http.patch<UserRecord>(`${this.apiUrl}/users/${this.selected.id}`, {
        nom: this.form.nom,
        email: this.form.email,
        role: this.form.role
      })
      : this.http.post<UserRecord>(`${this.apiUrl}/users`, this.form);
    request.subscribe({
      next: user => {
        this.replaceUser(user);
        this.select(user);
        this.success = creating ? 'Utilisateur créé.' : 'Utilisateur enregistré.';
        this.saving = false;
      },
      error: err => {
        this.saving = false;
        this.error = err.error?.detail ?? 'L’utilisateur n’a pas pu être enregistré.';
      }
    });
  }

  toggleStatus(user: UserRecord): void {
    this.http.patch<UserRecord>(`${this.apiUrl}/users/${user.id}/status`, { est_actif: !user.est_actif }).subscribe({
      next: updated => {
        this.replaceUser(updated);
        if (this.selected?.id === updated.id) this.select(updated);
      },
      error: err => this.error = err.error?.detail ?? 'Le statut du compte n’a pas pu être modifié.'
    });
  }

  reindex(): void {
    if (this.reindexing) return;
    this.reindexing = true;
    this.error = '';
    this.success = '';
    this.http.post(`${this.apiUrl}/admin/rag/reindex`, {}).subscribe({
      next: () => {
        this.success = 'Réindexation RAG lancée.';
        this.reindexing = false;
      },
      error: err => {
        this.reindexing = false;
        this.error = err.error?.detail ?? 'La réindexation RAG n’a pas pu être lancée.';
      }
    });
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  private loadUsers(): void {
    this.http.get<UsersResponse>(`${this.apiUrl}/users?limit=100`).subscribe({
      next: response => { this.users = response.items; this.loading = false; },
      error: err => { this.loading = false; this.error = err.error?.detail ?? 'Impossible de charger les utilisateurs.'; }
    });
  }

  private replaceUser(user: UserRecord): void {
    const exists = this.users.some(item => item.id === user.id);
    this.users = exists ? this.users.map(item => item.id === user.id ? user : item) : [user, ...this.users];
  }
}
