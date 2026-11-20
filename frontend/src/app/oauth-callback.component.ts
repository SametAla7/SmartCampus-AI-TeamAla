import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

/** Page de retour OAuth : lit les jetons dans le fragment (#...) puis ouvre le tableau de bord. */
@Component({
  selector: 'app-oauth-callback',
  standalone: true,
  template: `<p style="padding:40px;font-family:DM Sans,Arial">Connexion en cours…</p>`
})
export class OAuthCallbackComponent implements OnInit {
  private auth = inject(AuthService);
  private router = inject(Router);

  ngOnInit() {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    const access = params.get('access_token');
    const refresh = params.get('refresh_token');
    // Retire les jetons de l'URL / de l'historique du navigateur.
    history.replaceState(null, '', window.location.pathname);

    if (!access || !refresh) {
      this.router.navigate(['/login'], { queryParams: { error: 'oauth_invalid_request' } });
      return;
    }
    this.auth.completeOAuth(access, refresh).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: () => {
        this.auth.logout();
        this.router.navigate(['/login'], { queryParams: { error: 'oauth_profile_failed' } });
      }
    });
  }
}
