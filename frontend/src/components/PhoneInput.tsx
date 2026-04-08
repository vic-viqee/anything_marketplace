'use client';

import { useState } from 'react';

interface PhoneInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
}

export default function PhoneInput({ label, value, onChange, placeholder = '700000000', required = true }: PhoneInputProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-foreground mb-2">
        {label}
      </label>
      <div className="relative">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-foreground">+</span>
        <input
          type="tel"
          value={value}
          onChange={(e) => {
            const val = e.target.value;
            if (val.startsWith('+254')) {
              onChange(val);
            } else if (val.startsWith('254')) {
              onChange('+' + val);
            } else if (val.startsWith('+')) {
              onChange('+254' + val.slice(1));
            } else {
              onChange('+254' + val);
            }
          }}
          className="w-full px-4 py-3 pl-8 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          placeholder={placeholder}
          required={required}
        />
      </div>
    </div>
  );
}
