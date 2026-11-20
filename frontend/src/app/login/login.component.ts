import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  private auth = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  mode: 'login' | 'signup' = 'login';
  email = '';
  password = '';
  firstName = '';
  lastName = '';
  loading = false;
  message = '';
  error = '';
  emailVerificationRequired = false;
  googleEnabled = false;
  googleLoginUrl = '';

  ngOnInit() {
    const verificationToken = this.route.snapshot.queryParamMap.get('verify_token');
    if (verificationToken) {
      this.loading = true;
      this.auth.verifyEmail(verificationToken).subscribe({
        next: result => {
          this.loading = false;
          this.message = result.message;
          this.router.navigate(['/login'], { replaceUrl: true });
        },
        error: err => {
          this.loading = false;
          this.error = err?.error?.detail || 'Could not verify this email address.';
          this.router.navigate(['/login'], { replaceUrl: true });
        }
      });
    }

    const error = this.route.snapshot.queryParamMap.get('error');
    if (error && !verificationToken) {
      this.error = error === 'oauth_denied'
        ? 'Google sign-in was cancelled.'
        : 'Google sign-in failed. Please try again.';
    }

    this.auth.oauthProviders().subscribe({
      next: providers => {
        this.googleEnabled = providers.google;
        this.googleLoginUrl = providers.google_login_url;
      },
      error: () => (this.googleEnabled = false)
    });
  }

  submit() {
    this.loading = true;
    this.message = '';
    this.error = '';
    this.emailVerificationRequired = false;

    if (this.mode === 'login') {
      this.auth.login(this.email, this.password).subscribe({
        next: () => {
          this.loading = false;
          this.router.navigate(['/conversations']);
        },
        error: err => {
          this.loading = false;
          this.emailVerificationRequired = err?.error?.error?.code === 'EMAIL_NOT_VERIFIED';
          this.error = err?.error?.detail || 'Invalid email or password.';
        }
      });
      return;
    }

    const nom = `${this.firstName} ${this.lastName}`.trim();
    this.auth.register(nom, this.email, this.password).subscribe({
      next: () => {
        this.loading = false;
        this.message = 'Account created. Check your email for a verification link before signing in.';
        this.mode = 'login';
      },
      error: err => {
        this.loading = false;
        this.error = err?.error?.detail || 'Could not create your account.';
      }
    });
  }

  google() {
    if (this.googleEnabled && this.googleLoginUrl) {
      this.auth.startGoogleLogin(this.googleLoginUrl);
    }
  }

  resendVerification() {
    this.loading = true;
    this.auth.resendVerification(this.email).subscribe({
      next: result => {
        this.loading = false;
        this.message = result.message;
      },
      error: err => {
        this.loading = false;
        this.error = err?.error?.detail || 'Could not resend the verification email.';
      }
    });
  }
}
