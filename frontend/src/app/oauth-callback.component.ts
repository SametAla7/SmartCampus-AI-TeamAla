import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-oauth-callback',
  standalone: true,
  template: '<p style="padding:40px;font-family:Arial,sans-serif">Completing Google sign-in...</p>'
})
export class OAuthCallbackComponent implements OnInit {
  private auth = inject(AuthService);
  private router = inject(Router);

  ngOnInit() {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');
    const requiresPasswordSetup = params.get('requires_password_setup') === 'true';
    history.replaceState(null, '', window.location.pathname);

    if (!accessToken || !refreshToken) {
      this.router.navigate(['/login'], { queryParams: { error: 'oauth_invalid_request' } });
      return;
    }

    this.auth.completeOAuth(accessToken, refreshToken, requiresPasswordSetup).subscribe({
      next: () => this.router.navigate([requiresPasswordSetup ? '/setup-profile' : '/conversations']),
      error: err => {
        if (err?.error?.error?.code === 'PASSWORD_SETUP_REQUIRED') {
          this.router.navigate(['/setup-profile']);
          return;
        }
        this.auth.logout();
        this.router.navigate(['/login'], { queryParams: { error: 'oauth_profile_failed' } });
      }
    });
  }
}