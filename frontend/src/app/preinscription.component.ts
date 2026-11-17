import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

interface Parcours {
  id: string;
  nom: string;
  description: string | null;
  etablissement: 'IIT' | 'ISB';
}

interface Candidature {
  id: string;
  statut: string;
  parcours: Parcours;
}

@Component({
  selector: 'app-preinscription',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './preinscription.component.html',
  styleUrls: ['./preinscription.component.css']
})
export class PreinscriptionComponent implements OnInit {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private router = inject(Router);
  private apiUrl = 'http://127.0.0.1:8000/api';

  parcours: Parcours[] = [];
  selectedParcoursId = '';
  candidature: Candidature | null = null;
  loading = true;
  submitting = false;
  error = '';
  success = '';
  firstName = '';
  lastName = '';
  email = '';

  ngOnInit(): void {
    const user = this.auth.getUser();
    const parts = (user?.nom || '').trim().split(/\s+/);
    this.firstName = parts[0] || '';
    this.lastName = parts.slice(1).join(' ');
    this.email = user?.email || '';

    this.http.get<{ items: Parcours[] }>(`${this.apiUrl}/parcours`).subscribe({
      next: response => {
        this.parcours = response.items;
        this.selectedParcoursId = this.parcours[0]?.id || '';
        this.loading = false;
        this.loadExistingCandidature();
      },
      error: err => {
        this.error = err.error?.detail ?? 'Impossible de charger les formations.';
        this.loading = false;
      }
    });
  }

  submit(): void {
    if (!this.selectedParcoursId) {
      this.error = 'Sélectionnez une formation avant de valider.';
      return;
    }

    this.submitting = true;
    this.error = '';
    this.success = '';
    this.http.post<Candidature>(`${this.apiUrl}/candidatures`, {
      parcours_id: this.selectedParcoursId
    }).subscribe({
      next: candidature => {
        this.candidature = candidature;
        this.success = 'Votre préinscription a été enregistrée.';
        this.submitting = false;
      },
      error: err => {
        this.error = err.error?.detail ?? 'La préinscription n’a pas pu être enregistrée.';
        this.submitting = false;
      }
    });
  }

  backToConversation(): void {
    this.router.navigate(['/conversations']);
  }

  backToOrientation(): void {
    this.router.navigate(['/orientation']);
  }

  openQcm(): void {
    this.router.navigate(['/qcm']);
  }

  openDossier(): void {
    this.router.navigate(['/dossier']);
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  get initials(): string {
    const name = this.auth.getUser()?.nom?.trim() || 'YB';
    return name.split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase();
  }

  private loadExistingCandidature(): void {
    this.http.get<{ items: Candidature[] }>(`${this.apiUrl}/candidatures?limit=1`).subscribe({
      next: response => {
        this.candidature = response.items[0] || null;
        if (this.candidature) this.selectedParcoursId = this.candidature.parcours.id;
      },
      error: () => undefined
    });
  }
}
