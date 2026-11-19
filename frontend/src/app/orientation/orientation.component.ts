import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

interface Parcours {
  id: string;
  nom: string;
  description: string | null;
  etablissement: 'IIT' | 'ISB';
  created_at: string;
}

@Component({
  selector: 'app-orientation',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './orientation.component.html',
  styleUrls: ['./orientation.component.css']
})
export class OrientationComponent implements OnInit {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private router = inject(Router);

  parcours: Parcours[] = [];
  selected: Parcours | null = null;
  loading = true;
  error = '';

  get initials(): string {
    const name = this.auth.getUser()?.nom?.trim() || 'YB';
    return name.split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase();
  }

  ngOnInit(): void {
    this.http.get<{ items: Parcours[] }>('/api/parcours').subscribe({
      next: response => {
        this.parcours = response.items;
        this.selected = this.parcours[0] ?? null;
        this.loading = false;
      },
      error: err => {
        this.error = err.error?.detail ?? 'Impossible de charger les parcours.';
        this.loading = false;
      }
    });
  }

  select(parcours: Parcours): void {
    this.selected = parcours;
  }

  askAssistant(): void {
    this.router.navigate(['/conversations']);
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
}
