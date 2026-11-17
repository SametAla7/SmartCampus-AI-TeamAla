import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div style="padding: 40px; font-family: DM Sans, Arial;">
      <h1>SmartCampus AI - Dashboard</h1>
      <p *ngIf="user">Bienvenue {{user.nom}} ({{user.role}})</p>
      <button (click)="logout()">Déconnexion</button>
      <p>Backend API : http://127.0.0.1:8000/api</p>
    </div>
  `
})
export class DashboardComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  user = this.auth.getUser();

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
