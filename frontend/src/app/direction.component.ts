import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

interface ParcoursStat {
  parcours_id: string | null;
  nom: string | null;
  etablissement: string | null;
  total: number;
}

interface DashboardStats {
  total_candidatures: number;
  candidatures_par_statut: Record<string, number>;
  candidatures_par_parcours: ParcoursStat[];
  nombre_entretiens: number;
  evolution: Array<{ mois: string; total: number }>;
}

@Component({
  selector: 'app-direction',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './direction.component.html',
  styleUrls: ['./direction.component.css']
})
export class DirectionComponent implements OnInit {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private router = inject(Router);
  private apiUrl = 'http://127.0.0.1:8000/api';

  stats: DashboardStats | null = null;
  loading = true;
  exporting = false;
  error = '';

  get userName(): string {
    return this.auth.getUser()?.nom || 'Direction';
  }

  get initials(): string {
    return this.userName.split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase();
  }

  get conversations(): number {
    return this.stats?.total_candidatures ?? 0;
  }

  get validated(): number {
    return this.stats?.candidatures_par_statut?.['VALIDEE'] ?? 0;
  }

  get pending(): number {
    return this.stats?.candidatures_par_statut?.['EN_ATTENTE'] ?? 0;
  }

  get maxParcoursTotal(): number {
    return Math.max(...(this.stats?.candidatures_par_parcours.map(item => item.total) ?? [1]), 1);
  }

  ngOnInit(): void {
    this.http.get<DashboardStats>(`${this.apiUrl}/dashboard/stats`).subscribe({
      next: stats => {
        this.stats = stats;
        this.loading = false;
      },
      error: err => {
        this.loading = false;
        this.error = err.error?.detail ?? 'Impossible de charger les statistiques.';
      }
    });
  }

  exportReport(format: 'pdf' | 'xlsx'): void {
    if (this.exporting) return;
    this.exporting = true;
    this.http.get(`${this.apiUrl}/dashboard/export?format=${format}`, { responseType: 'blob' }).subscribe({
      next: content => {
        const url = URL.createObjectURL(content);
        const link = window.document.createElement('a');
        link.href = url;
        link.download = `smartcampus_dashboard.${format}`;
        link.click();
        URL.revokeObjectURL(url);
        this.exporting = false;
      },
      error: err => {
        this.exporting = false;
        this.error = err.error?.detail ?? 'Le rapport n’a pas pu être exporté.';
      }
    });
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
