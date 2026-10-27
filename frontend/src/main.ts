import 'zone.js';
import { bootstrapApplication } from '@angular/platform-browser';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({selector:'app-root',standalone:true,imports:[FormsModule,CommonModule],templateUrl:'./app.html'})
export class AppComponent { mode:'login'|'signup'='login'; email=''; password=''; firstName=''; lastName=''; loading=false; message='';
  submit(){this.loading=true;this.message='';setTimeout(()=>{this.loading=false;this.message=this.mode==='signup'?'Check your email to verify your account.':'Welcome back to SmartCampus AI.'},700)}
  google(){this.message='Google sign-in will open here when OAuth credentials are configured.'}
}
bootstrapApplication(AppComponent);
