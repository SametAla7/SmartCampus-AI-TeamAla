import 'zone.js';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter, Routes } from '@angular/router';
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { authInterceptor } from './app/services/auth.interceptor';

const routes: Routes = [
  { path: 'login', loadComponent: () => import('./app/login/login.component').then(m => m.LoginComponent) },
  { path: 'dashboard', loadComponent: () => import('./app/dashboard/dashboard.component').then(m => m.DashboardComponent) },
  { path: 'conversations', loadComponent: () => import('./app/conversations/conversations.component').then(m => m.ConversationsComponent) },
  { path: 'orientation', loadComponent: () => import('./app/orientation/orientation.component').then(m => m.OrientationComponent) },
  { path: 'preinscription', loadComponent: () => import('./app/preinscription/preinscription.component').then(m => m.PreinscriptionComponent) },
  { path: 'qcm', loadComponent: () => import('./app/qcm/qcm.component').then(m => m.QcmComponent) },
  { path: 'dossier', loadComponent: () => import('./app/dossier/dossier.component').then(m => m.DossierComponent) },
  { path: 'responsable-academique', loadComponent: () => import('./app/responsable-academique/responsable-academique.component').then(m => m.ResponsableAcademiqueComponent) },
  { path: 'responsable-entretien', loadComponent: () => import('./app/responsable-entretien/responsable-entretien.component').then(m => m.ResponsableEntretienComponent) },
  { path: 'direction', loadComponent: () => import('./app/direction/direction.component').then(m => m.DirectionComponent) },
  { path: 'administration', loadComponent: () => import('./app/administration/administration.component').then(m => m.AdministrationComponent) },
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: '**', redirectTo: 'login' }
];

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: '<router-outlet></router-outlet>'
})
export class AppComponent {}

bootstrapApplication(AppComponent, {
  providers: [
    provideHttpClient(withInterceptors([authInterceptor])),
    provideRouter(routes)
  ]
});
