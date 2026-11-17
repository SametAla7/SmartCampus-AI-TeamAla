import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

interface Parcours {
  id: string;
  nom: string;
  etablissement: 'IIT' | 'ISB';
}

interface Candidature {
  id: string;
  statut: string;
  parcours: Parcours;
}

interface QcmRecord {
  id: string;
  candidature_id: string;
  score: number | null;
  date: string | null;
}

interface Question {
  text: string;
  options: string[];
  answer: number;
  category: string;
}

@Component({
  selector: 'app-qcm',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './qcm.component.html',
  styleUrls: ['./qcm.component.css']
})
export class QcmComponent implements OnInit {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private router = inject(Router);
  private apiUrl = 'http://127.0.0.1:8000/api';

  readonly questions: Question[] = [
    {
      text: 'Quelle structure de données permet d’accéder directement à un élément grâce à son indice ?',
      options: ['Un tableau', 'Une pile', 'Une file', 'Un arbre binaire'],
      answer: 0,
      category: 'Algorithmique'
    },
    {
      text: 'Quelle est la valeur de 2³ + 4 ?',
      options: ['8', '10', '12', '16'],
      answer: 1,
      category: 'Maths'
    },
    {
      text: 'Quel protocole est principalement utilisé pour consulter une API web ?',
      options: ['HTTP', 'FTP', 'SMTP', 'SSH'],
      answer: 0,
      category: 'Bases informatiques'
    },
    {
      text: 'Quelle instruction permet de répéter un bloc tant qu’une condition est vraie ?',
      options: ['if', 'switch', 'while', 'return'],
      answer: 2,
      category: 'Logique'
    },
    {
      text: 'Quel type représente une valeur vraie ou fausse ?',
      options: ['String', 'Boolean', 'Float', 'Array'],
      answer: 1,
      category: 'Bases informatiques'
    },
    {
      text: 'Si tous les A sont B et tous les B sont C, que peut-on conclure ?',
      options: ['Tous les A sont C', 'Aucun A n’est C', 'Tous les C sont A', 'On ne peut rien conclure'],
      answer: 0,
      category: 'Logique'
    },
    {
      text: 'Quelle opération permet de comparer deux valeurs dans la plupart des langages ?',
      options: ['=', '==', '++', '+='],
      answer: 1,
      category: 'Programmation'
    },
    {
      text: 'Combien vaut 15 % de 200 ?',
      options: ['15', '20', '30', '35'],
      answer: 2,
      category: 'Maths'
    }
  ];

  candidature: Candidature | null = null;
  existingQcm: QcmRecord | null = null;
  currentIndex = 0;
  selectedAnswers: Array<number | null> = Array(this.questions.length).fill(null);
  loading = true;
  submitting = false;
  error = '';

  get currentQuestion(): Question {
    return this.questions[this.currentIndex];
  }

  get initials(): string {
    const name = this.auth.getUser()?.nom?.trim() || 'YB';
    return name.split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase();
  }

  get answeredCount(): number {
    return this.selectedAnswers.filter(answer => answer !== null).length;
  }

  ngOnInit(): void {
    this.http.get<{ items: Candidature[] }>(`${this.apiUrl}/candidatures?limit=1`).subscribe({
      next: response => {
        this.candidature = response.items[0] ?? null;
        if (!this.candidature) {
          this.loading = false;
          return;
        }
        this.loadExistingQcm(this.candidature.id);
      },
      error: err => this.showError(err, 'Impossible de charger votre candidature.')
    });
  }

  selectAnswer(index: number): void {
    if (!this.existingQcm) this.selectedAnswers[this.currentIndex] = index;
  }

  previous(): void {
    if (this.currentIndex > 0) this.currentIndex--;
  }

  next(): void {
    if (this.currentIndex < this.questions.length - 1) {
      this.currentIndex++;
    } else {
      this.submit();
    }
  }

  goTo(index: number): void {
    this.currentIndex = index;
  }

  submit(): void {
    if (!this.candidature || this.existingQcm || this.answeredCount !== this.questions.length) return;
    let correct = 0;
    this.selectedAnswers.forEach((answer, index) => {
      if (answer === this.questions[index].answer) correct++;
    });
    this.submitting = true;
    this.error = '';
    this.http.post<QcmRecord>(`${this.apiUrl}/candidatures/${this.candidature.id}/qcm/submit`, {
      score: Math.round((correct / this.questions.length) * 100)
    }).subscribe({
      next: qcm => {
        this.existingQcm = qcm;
        this.submitting = false;
      },
      error: err => {
        this.submitting = false;
        this.showError(err, 'Le QCM n’a pas pu être envoyé.');
      }
    });
  }

  backToPreinscription(): void {
    this.router.navigate(['/preinscription']);
  }

  backToOrientation(): void {
    this.router.navigate(['/orientation']);
  }

  openConversation(): void {
    this.router.navigate(['/conversations']);
  }

  openDossier(): void {
    this.router.navigate(['/dossier']);
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  private loadExistingQcm(candidatureId: string): void {
    this.http.get<QcmRecord>(`${this.apiUrl}/candidatures/${candidatureId}/qcm`).subscribe({
      next: qcm => {
        this.existingQcm = qcm;
        this.loading = false;
      },
      error: err => {
        if (err.status === 404) {
          this.loading = false;
          return;
        }
        this.showError(err, 'Impossible de charger l’état du QCM.');
      }
    });
  }

  private showError(err: { error?: { detail?: string } }, fallback: string): void {
    this.error = err.error?.detail ?? fallback;
    this.loading = false;
  }
}
