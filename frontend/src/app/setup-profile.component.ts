import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-setup-profile',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <main class="auth-shell" style="display:block">
      <section class="panel" style="min-height:100vh">
        <div class="form-wrap">
          <p class="eyebrow">NAU SMARTCAMPUS AI</p>
          <h1>Set up your profile</h1>
          <p class="sub">Choose a password for your new account to finish setup.</p>
          <form (ngSubmit)="submit()">
            <label>PASSWORD<input type="password" name="password" [(ngModel)]="password" autocomplete="new-password" required minlength="8" maxlength="128"></label>
            <label>CONFIRM PASSWORD<input type="password" name="confirmPassword" [(ngModel)]="confirmPassword" autocomplete="new-password" required minlength="8" maxlength="128"></label>
            <button class="primary" [disabled]="loading">{{loading ? 'Please wait...' : 'Save password'}}</button>
          </form>
          <p class="error" *ngIf="error">{{error}}</p>
        </div>
      </section>
    </main>
  `
})
export class SetupProfileComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  password = '';
  confirmPassword = '';
  loading = false;
  error = '';

  constructor() {
    if (!this.auth.getToken()) {
      this.router.navigate(['/login']);
    }
  }

  submit() {
    this.error = '';
    if (this.password !== this.confirmPassword) {
      this.error = 'Passwords do not match.';
      return;
    }

    this.loading = true;
    this.auth.setupPassword(this.password).subscribe({
      next: () => this.router.navigate(['/conversations']),
      error: err => {
        this.loading = false;
        this.error = err?.error?.detail || 'Could not save your password. Please try again.';
      }
    });
  }
}
