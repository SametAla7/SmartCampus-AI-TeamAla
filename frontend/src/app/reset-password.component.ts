import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <main class="auth-shell" style="display:block">
      <section class="panel" style="min-height:100vh"><div class="form-wrap">
        <p class="eyebrow">NAU SMARTCAMPUS AI</p>
        <h1>Nouveau mot de passe</h1>
        <p class="sub">Choisissez un mot de passe d'au moins 8 caractères.</p>
        <form (ngSubmit)="submit()" *ngIf="!done">
          <label>NOUVEAU MOT DE PASSE<input type="password" name="pwd" [(ngModel)]="password" required minlength="8"></label>
          <label>CONFIRMATION<input type="password" name="pwd2" [(ngModel)]="confirm" required minlength="8"></label>
          <button class="primary" [disabled]="loading || !token">{{ loading ? 'Enregistrement…' : 'Mettre à jour' }}</button>
        </form>
        <p class="notice" *ngIf="message">{{ message }}</p>
        <p class="error" *ngIf="error" style="text-align:center;color:#dc2626;font-size:13px">{{ error }}</p>
        <p class="switch"><button type="button" (click)="back()">{{ done ? 'Se connecter' : 'Retour à la connexion' }}</button></p>
      </div></section>
    </main>
  `
})
export class ResetPasswordComponent implements OnInit {
  private auth = inject(AuthService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  token = '';
  password = '';
  confirm = '';
  loading = false;
  done = false;
  message = '';
  error = '';

  ngOnInit() {
    this.token = this.route.snapshot.queryParamMap.get('token') || '';
    if (!this.token) this.error = 'Lien invalide : jeton manquant.';
  }

  submit() {
    this.error = '';
    if (this.password !== this.confirm) { this.error = 'Les mots de passe ne correspondent pas.'; return; }
    this.loading = true;
    this.auth.resetPassword(this.token, this.password).subscribe({
      next: res => { this.loading = false; this.done = true; this.message = res.message; },
      error: err => {
        this.loading = false;
        this.error = typeof err.error?.detail === 'string' ? err.error.detail : 'Impossible de mettre à jour le mot de passe.';
      }
    });
  }

  back() { this.router.navigate(['/login']); }
}
