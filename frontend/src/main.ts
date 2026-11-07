import 'zone.js';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter, Routes } from '@angular/router';
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { authInterceptor } from './app/services/auth.interceptor';

const routes: Routes = [
  { path: 'login', loadComponent: () => import('./app/login.component').then(m => m.LoginComponent) },
  { path: 'dashboard', loadComponent: () => import('./app/dashboard.component').then(m => m.DashboardComponent) },
  { path: '', redirectTo: 'login', pathMatch: 'full' }
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
