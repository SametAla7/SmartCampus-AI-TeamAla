import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  
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
    
    if (this.mode === 'login') {
      this.auth.login(this.email, this.password).subscribe({
        next: (response) => {
          this.loading = false;
          const destinationByRole: Record<string, string> = {
            ADMINISTRATEUR: '/administration',
            DIRECTION: '/direction',
            RESPONSABLE_ACADEMIQUE: '/responsable-academique',
            RESPONSABLE_ENTRETIEN: '/responsable-entretien',
            CANDIDAT: '/dashboard'
          };
          this.router.navigate([destinationByRole[response.user.role] ?? '/dashboard']);
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Identifiants invalides';
        }
      });
    } else {
      const nom = `${this.firstName} ${this.lastName}`.trim();
      this.auth.register(nom, this.email, this.password).subscribe({
        next: () => {
          this.loading = false;
          this.message = 'Compte créé avec succès. Vous pouvez vous connecter.';
          this.mode = 'login';
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.detail || 'Erreur lors de la création du compte';
        }
      });
    }
  }

  google() {
    this.message = 'Google sign-in sera disponible prochainement.';
  }
}
