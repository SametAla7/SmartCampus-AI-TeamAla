import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <main class="auth-shell" style="display:block">
      <section class="panel" style="min-height:100vh"><div class="form-wrap">
        <p class="eyebrow">NAU SMARTCAMPUS AI</p>
        <h1>Mot de passe oublié</h1>
        <p class="sub">Saisissez votre email : nous vous enverrons un lien pour choisir un nouveau mot de passe.</p>
        <form (ngSubmit)="submit()">
          <label>EMAIL<input type="email" name="email" [(ngModel)]="email" required></label>
          <button class="primary" [disabled]="loading">{{ loading ? 'Envoi…' : 'Envoyer le lien' }}</button>
        </form>
        <p class="notice" *ngIf="message">{{ message }}</p>
        <p class="error" *ngIf="error" style="text-align:center;color:#dc2626;font-size:13px">{{ error }}</p>
        <p class="switch"><button type="button" (click)="back()">Retour à la connexion</button></p>
      </div></section>
    </main>
  `
})
export class ForgotPasswordComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  email = '';
  loading = false;
  message = '';
  error = '';

  submit() {
    this.loading = true;
    this.message = '';
    this.error = '';
    this.auth.forgotPassword(this.email).subscribe({
      next: res => { this.loading = false; this.message = res.message; },
      error: err => { this.loading = false; this.error = err.error?.detail?.[0]?.msg || 'Email invalide ou service indisponible.'; }
    });
  }

  back() { this.router.navigate(['/login']); }
}
