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
          this.error = err.error?.detail || 'Identifiants invalides';
        }
      });
    } else {
      const nom = `${this.firstName} ${this.lastName}`.trim();
      this.auth.register(nom, this.email, this.password).subscribe({
        next: () => {
          this.loading = false;
          this.message = 'Compte cr�� avec succ�s. Vous pouvez vous connecter.';
          this.mode = 'login';
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Erreur lors de la cr�ation du compte';
        }
      });
    }
  }

  private formatError(err: any, fallback: string): string {
    const detail = err?.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length) {
      const labels: Record<string, string> = { mot_de_passe: 'Mot de passe', email: 'Email', nom: 'Nom' };
      return detail
        .map((d: any) => {
          const field = labels[d?.loc?.[d.loc.length - 1]] || '';
          const min = d?.ctx?.min_length;
          if (d?.type === 'string_too_short' && min) return `${field || 'Champ'} : ${min} caracteres minimum.`;
          return `${field ? field + ' : ' : ''}${d?.msg || 'valeur invalide'}`;
        })
        .join(' ');
    }
    return err?.status === 0 ? 'Serveur injoignable (backend arretee ?).' : fallback;
  }

  googleEnabled = false;

  private static readonly OAUTH_ERRORS: Record<string, string> = {
    oauth_denied: 'Connexion Google annulee.',
    oauth_state_invalid: 'Session de connexion expiree, veuillez reessayer.',
    oauth_invalid_request: 'Reponse Google invalide, veuillez reessayer.',
    oauth_email_not_verified: "L'email de votre compte Google n'est pas verifie.",
    oauth_code_exchange_failed: "Echec de l'authentification Google.",
    oauth_profile_failed: 'Impossible de charger votre profil.',
    oauth_provider_unreachable: 'Google est injoignable pour le moment.',
    user_inactive: 'Ce compte est desactive.'
  };

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
          this.error = this.formatError(err, 'Impossible de confirmer cette adresse email.');
          this.router.navigate(['/login'], { replaceUrl: true });
        }
      });
    }

    const code = this.route.snapshot.queryParamMap.get('error');
    if (code && !verificationToken) {
      this.error = LoginComponent.OAUTH_ERRORS[code] || 'Echec de la connexion.';
    }

    this.auth.oauthProviders().subscribe({
      next: p => (this.googleEnabled = p.google),
      error: () => (this.googleEnabled = false)
    });
  }

  google() {
    this.message = 'Google sign-in sera disponible prochainement.';
  }
}
