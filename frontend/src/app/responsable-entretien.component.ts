import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

interface Parcours {
  id: string;
  nom: string;
  etablissement: string;
}

interface Candidature {
  id: string;
  candidat_id: string;
  parcours: Parcours;
  statut: string;
}

interface Entretien {
  id: string;
  candidature_id: string;
  date: string;
  approuve: boolean;
}

interface QcmResult {
  score: number | null;
  date: string | null;
}

interface ComplementRequest {
  id: string;
  contenu: string;
  statut: string;
  date_demande: string;
}

@Component({
  selector: 'app-responsable-entretien',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './responsable-entretien.component.html',
  styleUrls: ['./responsable-entretien.component.css']
})
export class ResponsableEntretienComponent implements OnInit {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private router = inject(Router);
  private apiUrl = 'http://127.0.0.1:8000/api';

  entretiens: Entretien[] = [];
  candidatures = new Map<string, Candidature>();
  selected: Entretien | null = null;
  candidature: Candidature | null = null;
  qcm: QcmResult | null = null;
  complements: ComplementRequest[] = [];
  loading = true;
  detailsLoading = false;
  saving = false;
  error = '';
  actionError = '';
  newDate = '';
  complement = '';

  get userName(): string {
    return this.auth.getUser()?.nom || 'Responsable entretien';
  }

  get initials(): string {
    return this.userName.split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase();
  }

  get pendingCount(): number {
    return this.entretiens.filter(item => !item.approuve).length;
  }

  ngOnInit(): void {
    this.http.get<Entretien[]>(`${this.apiUrl}/entretiens`).subscribe({
      next: entretiens => {
        this.entretiens = entretiens;
        this.loading = false;
        this.selected = entretiens[0] ?? null;
        if (this.selected) this.loadDetails(this.selected);
      },
      error: err => {
        this.loading = false;
        this.error = err.error?.detail ?? 'Impossible de charger les entretiens.';
      }
    });
  }

  select(entretien: Entretien): void {
    this.selected = entretien;
    this.loadDetails(entretien);
  }

  approve(): void {
    if (!this.selected || this.selected.approuve || this.saving) return;
    this.saving = true;
    this.actionError = '';
    this.http.patch<Entretien>(`${this.apiUrl}/entretiens/${this.selected.id}/approval`, { approuve: true }).subscribe({
      next: updated => {
        this.selected = updated;
        this.entretiens = this.entretiens.map(item => item.id === updated.id ? updated : item);
        this.saving = false;
      },
      error: err => {
        this.saving = false;
        this.actionError = err.error?.detail ?? 'L’approbation n’a pas pu être enregistrée.';
      }
    });
  }

  schedule(): void {
    if (!this.candidature || !this.newDate || this.saving) return;
    this.saving = true;
    this.actionError = '';
    this.http.post<Entretien>(`${this.apiUrl}/candidatures/${this.candidature.id}/entretiens`, {
      date: new Date(this.newDate).toISOString()
    }).subscribe({
      next: entretien => {
        this.entretiens = [entretien, ...this.entretiens];
        this.selected = entretien;
        this.saving = false;
        this.newDate = '';
      },
      error: err => {
        this.saving = false;
        this.actionError = err.error?.detail ?? 'Le rendez-vous n’a pas pu être planifié.';
      }
    });
  }

  requestComplement(): void {
    if (!this.candidature || !this.complement.trim() || this.saving) return;
    this.saving = true;
    this.actionError = '';
    this.http.post<ComplementRequest>(`${this.apiUrl}/candidatures/${this.candidature.id}/demandes-complement`, {
      contenu: this.complement.trim(),
      informations_attendues: this.complement.trim()
    }).subscribe({
      next: request => {
        this.complements = [request, ...this.complements];
        this.complement = '';
        this.saving = false;
      },
      error: err => {
        this.saving = false;
        this.actionError = err.error?.detail ?? 'La demande de complément n’a pas pu être envoyée.';
      }
    });
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  private loadDetails(entretien: Entretien): void {
    this.detailsLoading = true;
    this.actionError = '';
    this.qcm = null;
    this.complements = [];
    this.http.get<Candidature>(`${this.apiUrl}/candidatures/${entretien.candidature_id}`).subscribe({
      next: candidature => {
        this.candidature = candidature;
        this.loadQcm(entretien.candidature_id);
        this.loadComplements(entretien.candidature_id);
      },
      error: err => {
        this.detailsLoading = false;
        this.actionError = err.error?.detail ?? 'Impossible de charger la candidature.';
      }
    });
  }

  private loadQcm(candidatureId: string): void {
    this.http.get<QcmResult>(`${this.apiUrl}/candidatures/${candidatureId}/qcm/result`).subscribe({
      next: result => { this.qcm = result; this.detailsLoading = false; },
      error: err => {
        if (err.status !== 404) this.actionError = err.error?.detail ?? 'Impossible de charger le résultat du QCM.';
        this.detailsLoading = false;
      }
    });
  }

  private loadComplements(candidatureId: string): void {
    this.http.get<ComplementRequest[]>(`${this.apiUrl}/candidatures/${candidatureId}/demandes-complement`).subscribe({
      next: requests => this.complements = requests,
      error: () => undefined
    });
  }
}
