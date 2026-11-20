import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

interface Parcours {
  id: string;
  nom: string;
  etablissement: 'IIT' | 'ISB';
}

interface Candidature {
  id: string;
  statut: string;
  parcours: Parcours;
}

interface QcmRecord {
  score: number | null;
  date: string | null;
}

interface Entretien {
  id: string;
  candidature_id: string;
  date: string;
  approuve: boolean;
}

interface DocumentRecord {
  id: string;
  nom: string;
  type: string;
  date_ajout: string;
}

interface ComplementRequest {
  id: string;
  contenu: string;
  statut: string;
  date_demande: string;
}

@Component({
  selector: 'app-dossier',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dossier.component.html',
  styleUrls: ['./dossier.component.css']
})
export class DossierComponent implements OnInit {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private router = inject(Router);
  private apiUrl = '/api';

  candidature: Candidature | null = null;
  qcm: QcmRecord | null = null;
  entretien: Entretien | null = null;
  documents: DocumentRecord[] = [];
  complements: ComplementRequest[] = [];
  loading = true;
  uploading = false;
  error = '';

  get userName(): string {
    return this.auth.getUser()?.nom || 'candidat';
  }

  get initials(): string {
    return this.userName.split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase();
  }

  get isCandidatureDone(): boolean {
    return this.candidature !== null;
  }

  get isQcmDone(): boolean {
    return this.qcm !== null;
  }

  get isInterviewDone(): boolean {
    return this.entretien !== null;
  }

  get isInterviewApproved(): boolean {
    return this.entretien?.approuve === true;
  }

  ngOnInit(): void {
    this.http.get<{ items: Candidature[] }>(`${this.apiUrl}/candidatures?limit=1`).subscribe({
      next: response => {
        this.candidature = response.items[0] ?? null;
        if (!this.candidature) {
          this.loading = false;
          return;
        }
        this.loadDossierData(this.candidature.id);
      },
      error: err => this.showError(err, 'Impossible de charger votre dossier.')
    });
  }

  openConversation(): void {
    this.router.navigate(['/conversations']);
  }

  openOrientation(): void {
    this.router.navigate(['/orientation']);
  }

  openPreinscription(): void {
    this.router.navigate(['/preinscription']);
  }

  openQcm(): void {
    this.router.navigate(['/qcm']);
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  uploadDocument(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || !this.candidature) return;

    const formData = new FormData();
    formData.append('file', file);
    this.uploading = true;
    this.error = '';
    this.http.post<DocumentRecord>(`${this.apiUrl}/candidatures/${this.candidature.id}/documents`, formData).subscribe({
      next: document => {
        this.documents = [document, ...this.documents];
        this.uploading = false;
        input.value = '';
      },
      error: err => {
        this.uploading = false;
        this.error = err.error?.detail ?? 'Le document n’a pas pu être envoyé.';
        input.value = '';
      }
    });
  }

  downloadDocument(record: DocumentRecord): void {
    this.http.get(`${this.apiUrl}/documents/${record.id}/download`, { responseType: 'blob' }).subscribe({
      next: content => {
        const url = URL.createObjectURL(content);
        const link = window.document.createElement('a');
        link.href = url;
        link.download = record.nom;
        link.click();
        URL.revokeObjectURL(url);
      },
      error: err => {
        this.error = err.error?.detail ?? 'Le document n’a pas pu être téléchargé.';
      }
    });
  }

  private loadDossierData(candidatureId: string): void {
    let pending = 4;
    const complete = (): void => {
      pending--;
      if (pending === 0) this.loading = false;
    };

    this.http.get<QcmRecord>(`${this.apiUrl}/candidatures/${candidatureId}/qcm`).subscribe({
      next: qcm => { this.qcm = qcm; complete(); },
      error: err => {
        if (err.status !== 404) this.error = err.error?.detail ?? 'Impossible de charger le résultat du QCM.';
        complete();
      }
    });
    this.http.get<Entretien[]>(`${this.apiUrl}/entretiens`).subscribe({
      next: entretiens => {
        this.entretien = entretiens.find(item => item.candidature_id === candidatureId) ?? null;
        complete();
      },
      error: err => {
        if (err.status !== 404) this.error = err.error?.detail ?? 'Impossible de charger le rendez-vous.';
        complete();
      }
    });
    this.http.get<DocumentRecord[]>(`${this.apiUrl}/candidatures/${candidatureId}/documents`).subscribe({
      next: documents => { this.documents = documents; complete(); },
      error: err => {
        if (err.status !== 404) this.error = err.error?.detail ?? 'Impossible de charger les documents.';
        complete();
      }
    });
    this.http.get<ComplementRequest[]>(`${this.apiUrl}/candidatures/${candidatureId}/demandes-complement`).subscribe({
      next: complements => { this.complements = complements; complete(); },
      error: err => {
        if (err.status !== 404) this.error = err.error?.detail ?? 'Impossible de charger les demandes.';
        complete();
      }
    });
  }

  private showError(err: { error?: { detail?: string } }, fallback: string): void {
    this.error = err.error?.detail ?? fallback;
    this.loading = false;
  }
}
