import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

interface Parcours {
  id: string;
  nom: string;
  etablissement: string;
}

interface Candidature {
  id: string;
  candidat_id: string;
  parcours: Parcours;
  date_depot: string;
  statut: string;
  decision: Decision | null;
}

interface Decision {
  decision: string;
  commentaire: string | null;
  parcours_destination_id: string | null;
}

interface CandidatureResponse {
  items: Candidature[];
  total: number;
  page: number;
  limit: number;
}

interface QcmResult {
  score: number | null;
  date: string | null;
}

@Component({
  selector: 'app-responsable-academique',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './responsable-academique.component.html',
  styleUrls: ['./responsable-academique.component.css']
})
export class ResponsableAcademiqueComponent implements OnInit {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private router = inject(Router);
  private apiUrl = '/api';

  candidatures: Candidature[] = [];
  parcours: Parcours[] = [];
  selected: Candidature | null = null;
  qcm: QcmResult | null = null;
  filter = '';
  loading = true;
  detailsLoading = false;
  saving = false;
  error = '';
  decisionError = '';
  comment = '';
  destinationId = '';

  get filteredCandidatures(): Candidature[] {
    if (!this.filter) return this.candidatures;
    return this.candidatures.filter(item => item.statut === this.filter);
  }

  get initials(): string {
    const name = this.auth.getUser()?.nom?.trim() || 'RA';
    return name.split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase();
  }

  get userName(): string {
    return this.auth.getUser()?.nom || 'Responsable';
  }

  get pendingCount(): number {
    return this.candidatures.filter(item => item.statut === 'EN_ATTENTE').length;
  }

  ngOnInit(): void {
    this.loadCandidatures();
    this.http.get<{ items: Parcours[] }>(`${this.apiUrl}/parcours`).subscribe({
      next: response => this.parcours = response.items,
      error: () => this.parcours = []
    });
  }

  select(candidature: Candidature): void {
    this.selected = candidature;
    this.qcm = null;
    this.decisionError = '';
    this.detailsLoading = true;
    this.http.get<QcmResult>(`${this.apiUrl}/candidatures/${candidature.id}/qcm/result`).subscribe({
      next: result => {
        this.qcm = result;
        this.detailsLoading = false;
      },
      error: err => {
        if (err.status !== 404) this.decisionError = err.error?.detail ?? 'Impossible de charger le résultat du QCM.';
        this.detailsLoading = false;
      }
    });
  }

  decide(decision: 'ACCEPTER' | 'REJETER' | 'REORIENTER'): void {
    if (!this.selected || this.saving) return;
    if (decision === 'REORIENTER' && !this.destinationId) {
      this.decisionError = 'Sélectionnez un parcours de destination.';
      return;
    }

    this.saving = true;
    this.decisionError = '';
    this.http.patch<Candidature>(`${this.apiUrl}/candidatures/${this.selected.id}/decision`, {
      decision,
      commentaire: this.comment || null,
      parcours_destination_id: decision === 'REORIENTER' ? this.destinationId : null
    }).subscribe({
      next: updated => {
        this.replaceCandidature(updated);
        this.selected = updated;
        this.saving = false;
        this.comment = '';
        this.destinationId = '';
      },
      error: err => {
        this.saving = false;
        this.decisionError = err.error?.detail ?? 'La décision n’a pas pu être enregistrée.';
      }
    });
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  private loadCandidatures(): void {
    this.loading = true;
    this.error = '';
    this.http.get<CandidatureResponse>(`${this.apiUrl}/candidatures?limit=100`).subscribe({
      next: response => {
        this.candidatures = response.items;
        this.selected = this.candidatures[0] ?? null;
        this.loading = false;
        if (this.selected) this.select(this.selected);
      },
      error: err => {
        this.loading = false;
        this.error = err.error?.detail ?? 'Impossible de charger les candidatures.';
      }
    });
  }

  private replaceCandidature(updated: Candidature): void {
    this.candidatures = this.candidatures.map(item => item.id === updated.id ? updated : item);
  }
}
