import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';
import { Conversation, ConversationService, Message } from './services/conversation.service';

interface Parcours {
  id: string;
  nom: string;
  description: string | null;
  etablissement: 'IIT' | 'ISB';
  created_at: string;
}

@Component({
  selector: 'app-conversations',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './conversations.component.html',
  styleUrls: ['./conversations.component.css']
})
export class ConversationsComponent implements OnInit {
  private conversations = inject(ConversationService);
  private auth = inject(AuthService);
  private router = inject(Router);
  private http = inject(HttpClient);

  conversation: Conversation | null = null;
  messages: Message[] = [];
  parcours: Parcours[] = [];
  draft = '';
  loading = true;
  sending = false;
  error = '';

  get initials(): string {
    const name = this.auth.getUser()?.nom?.trim() || 'YB';
    return name.split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase();
  }

  ngOnInit(): void {
    const id = sessionStorage.getItem('conversation_id');
    id ? this.load(id) : this.newConversation();
    this.http.get<{ items: Parcours[] }>('http://127.0.0.1:8000/api/parcours').subscribe({
      next: response => this.parcours = response.items,
      error: () => this.parcours = []
    });
  }

  newConversation(): void {
    this.loading = true;
    this.error = '';
    this.conversations.create().subscribe({
      next: conversation => {
        this.setConversation(conversation);
        this.loading = false;
      },
      error: err => this.showError(err, 'Impossible de créer une conversation.')
    });
  }

  send(): void {
    if (!this.conversation || !this.draft.trim()) return;
    const content = this.draft.trim();
    this.draft = '';
    this.sending = true;
    this.error = '';
    this.conversations.sendMessage(this.conversation.id, content).subscribe({
      next: () => this.loadMessages(this.conversation!.id),
      error: err => {
        this.draft = content;
        this.sending = false;
        this.showError(err, 'Le message n’a pas pu être envoyé.');
      }
    });
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  openOrientation(): void {
    this.router.navigate(['/orientation']);
  }

  openPreinscription(): void {
    this.router.navigate(['/preinscription']);
  }

  private load(id: string): void {
    this.loading = true;
    this.conversations.get(id).subscribe({
      next: conversation => {
        this.setConversation(conversation);
        this.loading = false;
      },
      error: err => {
        sessionStorage.removeItem('conversation_id');
        this.showError(err, 'Cette conversation est indisponible.');
      }
    });
  }

  private loadMessages(id: string): void {
    this.conversations.get(id).subscribe({
      next: conversation => {
        this.setConversation(conversation);
        this.sending = false;
      },
      error: err => {
        this.sending = false;
        this.showError(err, 'Impossible de rafraîchir les messages.');
      }
    });
  }

  private setConversation(conversation: Conversation): void {
    this.conversation = conversation;
    this.messages = conversation.messages ?? [];
    sessionStorage.setItem('conversation_id', conversation.id);
  }

  private showError(err: { error?: { detail?: string } }, fallback: string): void {
    this.loading = false;
    this.error = err.error?.detail ?? fallback;
  }
}
