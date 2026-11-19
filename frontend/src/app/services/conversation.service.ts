import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string | null;
  contenu: string;
  est_assistant: boolean;
  created_at: string;
}

export interface Conversation {
  id: string;
  candidat_id: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

@Injectable({ providedIn: 'root' })
export class ConversationService {
  private http = inject(HttpClient);
  private apiUrl = '/api/conversations';

  create(): Observable<Conversation> {
    return this.http.post<Conversation>(this.apiUrl, {});
  }

  get(id: string): Observable<Conversation> {
    return this.http.get<Conversation>(`${this.apiUrl}/${id}`);
  }

  sendMessage(id: string, contenu: string): Observable<Message> {
    return this.http.post<Message>(`${this.apiUrl}/${id}/messages`, { contenu });
  }
}
