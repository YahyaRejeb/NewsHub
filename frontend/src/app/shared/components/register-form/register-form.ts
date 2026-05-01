import { Component, Output, EventEmitter } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-register-form',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './register-form.html',
  styleUrls: ['./register-form.css']
})
export class RegisterForm {
  form = {
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  };

  errorMessage: string = '';
  showPassword: boolean = false;
  @Output() nextStep = new EventEmitter<{
    full_name: string;
    email: string;
    password: string;
  }>();

  togglePassword() {
    this.showPassword = !this.showPassword;
  }

  onSubmit() {
    const normalizedName = this.form.name.trim();
    const normalizedEmail = this.form.email.trim().toLowerCase();

    if (!normalizedName || !normalizedEmail || !this.form.password || !this.form.confirmPassword) {
      this.errorMessage = 'Please fill in all fields.';
      return;
    }

    if (!normalizedEmail.includes('@')) {
      this.errorMessage = 'Please enter a valid email address.';
      return;
    }

    if (this.form.password !== this.form.confirmPassword) {
      this.errorMessage = 'Passwords do not match!';
      return;
    }

    this.errorMessage = '';
    this.nextStep.emit({
      full_name: normalizedName,
      email: normalizedEmail,
      password: this.form.password
    });
  }
}
