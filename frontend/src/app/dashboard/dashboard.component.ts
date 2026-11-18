import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div style="padding: 40px; font-family: DM Sans, Arial; color: #14233f;">
      <h1 style="color: #1742b5;">SmartCampus AI - Dashboard</h1>
      <p *ngIf="user">Bienvenue {{user.nom}} ({{user.role}})</p>
      <button style="background:linear-gradient(90deg,#2869ee,#1742b5);color:#fff;border:0;border-radius:6px;padding:10px 14px;margin-right:8px;cursor:pointer" (click)="logout()">Déconnexion</button>
      <button style="background:#fff;color:#1742b5;border:1px solid #74bce5;border-radius:6px;padding:10px 14px;cursor:pointer" (click)="openConversations()">Mon conseiller</button>
      <p>Backend API : /api</p>
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

  openConversations() {
    this.router.navigate(['/conversations']);
  }
}
