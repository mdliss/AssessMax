/**
 * ============================================================================
 * PULSEMAX UI DESIGN SYSTEM - PRODUCTION TEMPLATE
 * ============================================================================
 *
 * A Netflix-inspired dark theme design system featuring:
 * - Deep black backgrounds with teal accent color
 * - Modern, clean aesthetic with subtle animations
 * - Monospace typography for technical/analytics feel
 * - Comprehensive animation library with staggered page loads
 *
 * Framework: Tailwind CSS v4 + PostCSS
 * Primary Use: Analytics dashboards, data visualization, SaaS platforms
 * ============================================================================
 */

@import "tailwindcss";

/* ============================================================================
   1. COLOR SYSTEM & THEME VARIABLES
   ============================================================================ */

:root {
  /* ===== Core Colors - Netflix Inspired ===== */
  --background: #141414;           /* Netflix black - deep, pure black */
  --foreground: #ffffff;           /* Pure white text for maximum contrast */
  --card-bg: #1f1f1f;              /* Slightly lighter cards - subtle elevation */
  --border-color: #2a2a2a;         /* Subtle borders - barely visible separation */

  /* ===== Accent Colors ===== */
  --accent: #14b8a6;               /* Teal - modern, calming, professional */
  --accent-hover: #0d9488;         /* Darker teal on hover - subtle depth */

  /* ===== Text Colors ===== */
  --text-secondary: #b3b3b3;       /* Netflix gray text - secondary information */
  --text-muted: #808080;           /* More muted gray - tertiary information */

  /* ===== Semantic Colors ===== */
  /* NOTE: All semantic colors use teal for brand consistency */
  --success: #14b8a6;              /* Teal for positive states */
  --success-bg: #14b8a620;         /* Teal background with 20% opacity */

  --error: #14b8a6;                /* Teal for error states (brand consistency) */
  --error-bg: #14b8a620;           /* Teal error background */
  --error-border: #14b8a680;       /* Teal border with 50% opacity */

  --warning: #14b8a6;              /* Teal for warnings */
  --info: #14b8a6;                 /* Teal for info states */
  --live: #14b8a6;                 /* Teal for live indicators */

  /* ===== Badge Rarity Colors (Optional - for gamification) ===== */
  --rarity-common: #9CA3AF;        /* Gray */
  --rarity-rare: #3B82F6;          /* Blue */
  --rarity-epic: #A855F7;          /* Purple */
  --rarity-legendary: #F59E0B;     /* Gold */

  /* ===== Progress/Gamification Colors (Optional) ===== */
  --progress-daily: #10B981;       /* Green - daily goals */
  --progress-weekly: #3B82F6;      /* Blue - weekly goals */
  --progress-mastery: #8B5CF6;     /* Purple - mastery */
  --progress-streak: #F59E0B;      /* Orange - streaks */
  --progress-badges: #EC4899;      /* Pink - badges */
  --progress-overall: #6366F1;     /* Indigo - overall progress */
}

/* Tailwind Theme Integration */
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card-bg);
  --color-border: var(--border-color);
  --color-accent: var(--accent);
  --color-accent-hover: var(--accent-hover);
  --color-secondary: var(--text-secondary);
  --color-muted: var(--text-muted);
}

/* ============================================================================
   2. TYPOGRAPHY SYSTEM
   ============================================================================ */

body {
  background: var(--background);
  color: var(--foreground);
  font-family: 'Roboto Mono', monospace;  /* Monospace for technical/analytics aesthetic */
}

/* Custom text selection colors */
::selection {
  background-color: var(--accent);
  color: var(--background);
}

::-moz-selection {
  background-color: var(--accent);
  color: var(--background);
}

/* ============================================================================
   3. GLOBAL TRANSITIONS & BEHAVIORS
   ============================================================================ */

/* Smooth scrolling */
html {
  scroll-behavior: smooth;
}

/* Global smooth transitions for all elements */
* {
  transition-property: background-color, border-color, color, fill, stroke, opacity, box-shadow, transform, filter;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 200ms;
  scrollbar-width: thin;
  scrollbar-color: var(--border-color) var(--background);
}

/* Focus visible for accessibility */
*:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  transition: outline 150ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ============================================================================
   4. INTERACTIVE ELEMENT TRANSITIONS
   ============================================================================ */

/* ===== Button and Link Transitions ===== */
button, a {
  transition-property: all;
  transition-duration: 200ms;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

button:hover, a:hover {
  transform: translateY(-1px);
}

button:active, a:active {
  transform: scale(0.98) translateY(0);
}

/* ===== Input Field Transitions ===== */
input, textarea, select {
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

input:focus, textarea:focus, select:focus {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(20, 184, 166, 0.1),
              0 2px 4px -1px rgba(20, 184, 166, 0.06);
}

/* ===== Disabled State Transitions ===== */
button:disabled, input:disabled, select:disabled, textarea:disabled {
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
  cursor: not-allowed;
}

/* ===== List Item Transitions ===== */
li {
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ===== Icon Transitions ===== */
svg, img {
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ============================================================================
   5. COMPONENT-SPECIFIC TRANSITIONS
   ============================================================================ */

/* ===== Card Hover Effects ===== */
.card, [class*="bg-[#1f1f1f]"], [class*="bg-card"] {
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3),
              0 10px 10px -5px rgba(0, 0, 0, 0.2);
}

/* ===== Card Hover Utility Class ===== */
.card-hover {
  transition: transform 250ms cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 250ms cubic-bezier(0.4, 0, 0.2, 1),
              border-color 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3),
              0 10px 10px -5px rgba(0, 0, 0, 0.2);
  border-color: var(--accent);
}

/* ===== Badge Transitions ===== */
.badge {
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.badge:hover {
  transform: scale(1.05);
}

/* ===== Loading States ===== */
.loading {
  animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* ===== Modal Transitions ===== */
.modal-backdrop {
  animation: fadeIn 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-content {
  animation: modalSlideIn 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ===== Dropdown/Menu Transitions ===== */
.dropdown-menu {
  animation: dropdownSlideIn 200ms cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: top;
}

/* ===== Toast/Notification Transitions ===== */
.toast {
  animation: toastSlideIn 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ============================================================================
   6. KEYFRAME ANIMATIONS - CORE
   ============================================================================ */

/* ===== Fade In ===== */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* ===== Modal Slide In ===== */
@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ===== Dropdown Slide In ===== */
@keyframes dropdownSlideIn {
  from {
    opacity: 0;
    transform: scaleY(0.95) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scaleY(1) translateY(0);
  }
}

/* ===== Toast Slide In (from right) ===== */
@keyframes toastSlideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* ===== Pulse (Loading) ===== */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* ============================================================================
   7. KEYFRAME ANIMATIONS - PAGE LOAD STAGGER
   ============================================================================ */

/* ===== Drop In Animation ===== */
@keyframes dropIn {
  from {
    opacity: 0;
    transform: translateY(-60px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Staggered drop-in classes for cascading entrance effects */
.drop-in-1 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 0.1s;
}

.drop-in-2 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 0.3s;
}

.drop-in-3 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 0.5s;
}

.drop-in-4 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 0.7s;
}

.drop-in-5 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 0.9s;
}

.drop-in-6 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 1.1s;
}

.drop-in-7 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 1.3s;
}

.drop-in-8 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 1.5s;
}

.drop-in-9 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 1.7s;
}

.drop-in-10 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 1.9s;
}

.drop-in-11 {
  animation: dropIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  animation-delay: 2.1s;
}

/* ============================================================================
   8. KEYFRAME ANIMATIONS - INTERACTIONS & FEEDBACK
   ============================================================================ */

/* ===== Slide In Down ===== */
@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-in-down {
  animation: slideInDown 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ===== Bounce In Effect ===== */
@keyframes bounceIn {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    transform: scale(1);
  }
}

.animate-bounce-in {
  animation: bounceIn 600ms cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

/* ===== Scale In Effect ===== */
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-scale-in {
  animation: scaleIn 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ===== Fade In Effect ===== */
@keyframes fadeInEffect {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.animate-fade-in {
  animation: fadeInEffect 200ms ease-out;
}

/* ===== Slow Pulse for Progress Bars ===== */
@keyframes pulseSlow {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

.animate-pulse-slow {
  animation: pulseSlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* ===== Shake Effect (Error/Incorrect) ===== */
@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  10%, 30%, 50%, 70%, 90% {
    transform: translateX(-5px);
  }
  20%, 40%, 60%, 80% {
    transform: translateX(5px);
  }
}

.animate-shake {
  animation: shake 400ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ===== Shimmer Effect for Highlights ===== */
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.animate-shimmer {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.3) 50%,
    transparent 100%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite;
}

/* ===== Glow Effect ===== */
@keyframes glow {
  0%, 100% {
    box-shadow: 0 0 5px rgba(20, 184, 166, 0.5);
  }
  50% {
    box-shadow: 0 0 20px rgba(20, 184, 166, 0.8), 0 0 30px rgba(20, 184, 166, 0.6);
  }
}

.animate-glow {
  animation: glow 2s ease-in-out infinite;
}

/* ===== Spin (Loading) ===== */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ============================================================================
   9. BUTTON COMPONENT PATTERNS
   ============================================================================ */

/* ===== Primary Button (Accent) ===== */
.btn-primary {
  background-color: var(--accent);
  color: var(--background);
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-primary:hover {
  background-color: var(--accent-hover);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
  transform: translateY(-1px);
}

.btn-primary:active {
  transform: scale(0.98) translateY(0);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== Secondary Button (Neutral) ===== */
.btn-secondary {
  background-color: var(--border-color);
  color: var(--foreground);
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-secondary:hover {
  background-color: var(--accent);
  color: var(--background);
}

/* ===== Outline Button ===== */
.btn-outline {
  background-color: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-outline:hover {
  background-color: var(--accent);
  color: var(--background);
}

/* ===== Ghost Button ===== */
.btn-ghost {
  background-color: transparent;
  color: var(--text-secondary);
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-ghost:hover {
  background-color: var(--border-color);
  color: var(--foreground);
}

/* ============================================================================
   10. INPUT COMPONENT PATTERNS
   ============================================================================ */

/* ===== Text Input ===== */
.input-text {
  background-color: var(--background);
  border: 1px solid var(--border-color);
  color: var(--foreground);
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.input-text::placeholder {
  color: var(--text-muted);
}

.input-text:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 4px 6px -1px rgba(20, 184, 166, 0.1),
              0 2px 4px -1px rgba(20, 184, 166, 0.06);
}

/* ===== Textarea ===== */
.input-textarea {
  background-color: var(--background);
  border: 1px solid var(--border-color);
  color: var(--foreground);
  padding: 0.75rem;
  border-radius: 0.5rem;
  resize: vertical;
  min-height: 100px;
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.input-textarea::placeholder {
  color: var(--text-muted);
}

.input-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

/* ===== Select Dropdown ===== */
.input-select {
  background-color: var(--background);
  border: 1px solid var(--border-color);
  color: var(--foreground);
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  border-radius: 0.5rem;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%239ca3af' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.input-select:focus {
  outline: none;
  border-color: var(--accent);
}

/* ============================================================================
   11. CARD COMPONENT PATTERNS
   ============================================================================ */

/* ===== Base Card ===== */
.card-base {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.5rem;
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.card-base:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3),
              0 10px 10px -5px rgba(0, 0, 0, 0.2);
}

/* ===== Bordered Card (Hover Glow) ===== */
.card-bordered {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 1rem;
  padding: 1.5rem;
  transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

.card-bordered:hover {
  border-color: var(--accent);
}

/* ============================================================================
   12. DROPDOWN/MENU COMPONENT PATTERNS
   ============================================================================ */

/* ===== Dropdown Container ===== */
.dropdown-container {
  position: absolute;
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
  animation: dropdownSlideIn 200ms cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: top;
  z-index: 50;
}

/* ===== Dropdown Item ===== */
.dropdown-item {
  padding: 0.75rem 1rem;
  color: var(--foreground);
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.dropdown-item:hover {
  background-color: rgba(20, 184, 166, 0.1);
}

/* ============================================================================
   13. PROGRESS BAR COMPONENT PATTERNS
   ============================================================================ */

/* ===== Progress Bar Container ===== */
.progress-bar-container {
  width: 100%;
  height: 1rem;
  background-color: var(--background);
  border: 1px solid var(--border-color);
  border-radius: 9999px;
  overflow: hidden;
}

/* ===== Progress Bar Fill ===== */
.progress-bar-fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 500ms ease-out;
}

/* ===== Animated Progress Bar ===== */
.progress-bar-fill.animated {
  animation: pulseSlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* ============================================================================
   14. BADGE COMPONENT PATTERNS
   ============================================================================ */

/* ===== Badge Base ===== */
.badge-base {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border-width: 4px;
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Badge sizes */
.badge-sm { width: 3rem; height: 3rem; font-size: 1.5rem; }
.badge-md { width: 4rem; height: 4rem; font-size: 1.875rem; }
.badge-lg { width: 6rem; height: 6rem; font-size: 3rem; }

/* Badge states */
.badge-earned {
  background-color: var(--card-bg);
  opacity: 1;
}

.badge-locked {
  background-color: var(--background);
  opacity: 0.3;
  filter: grayscale(100%);
}

.badge-base:hover {
  transform: scale(1.05);
}

/* ============================================================================
   15. MESSAGE BUBBLE PATTERNS
   ============================================================================ */

/* ===== User Message ===== */
.message-user {
  background-color: var(--accent);
  color: var(--background);
  max-width: 80%;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  animation: fadeIn 300ms ease-in-out;
}

/* ===== AI/Assistant Message ===== */
.message-assistant {
  background-color: var(--card-bg);
  color: var(--foreground);
  border: 1px solid var(--border-color);
  max-width: 80%;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  animation: fadeIn 300ms ease-in-out;
}

/* ===== Error Message ===== */
.message-error {
  background-color: var(--error-bg);
  color: var(--accent);
  border: 1px solid var(--error-border);
  max-width: 80%;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
}

/* ===== Info Message (Highlighted) ===== */
.message-info {
  background-color: rgba(20, 184, 166, 0.1);
  color: var(--accent);
  border: 2px solid rgba(20, 184, 166, 0.3);
  max-width: 80%;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
}

/* ============================================================================
   16. LAYOUT & SPACING UTILITIES
   ============================================================================ */

/* Common grid patterns */
.grid-1-col { display: grid; grid-template-columns: repeat(1, 1fr); }
.grid-2-col { display: grid; grid-template-columns: repeat(2, 1fr); }
.grid-3-col { display: grid; grid-template-columns: repeat(3, 1fr); }

/* Responsive grids */
@media (min-width: 768px) {
  .grid-responsive-2 { grid-template-columns: repeat(2, 1fr); }
  .grid-responsive-3 { grid-template-columns: repeat(3, 1fr); }
}

/* Common gap values */
.gap-xs { gap: 0.25rem; }
.gap-sm { gap: 0.5rem; }
.gap-md { gap: 1rem; }
.gap-lg { gap: 1.5rem; }
.gap-xl { gap: 2rem; }

/* ============================================================================
   17. UTILITY CLASSES
   ============================================================================ */

/* ===== Text Utilities ===== */
.text-primary { color: var(--foreground); }
.text-secondary { color: var(--text-secondary); }
.text-muted { color: var(--text-muted); }
.text-accent { color: var(--accent); }
.text-error { color: var(--error); }
.text-success { color: var(--success); }

/* ===== Background Utilities ===== */
.bg-primary { background-color: var(--background); }
.bg-card { background-color: var(--card-bg); }
.bg-accent { background-color: var(--accent); }

/* ===== Border Utilities ===== */
.border-default { border-color: var(--border-color); }
.border-accent { border-color: var(--accent); }

/* ============================================================================
   18. SEMANTIC STATE PATTERNS
   ============================================================================ */

/* ===== Loading State ===== */
.state-loading {
  position: relative;
  pointer-events: none;
  opacity: 0.6;
}

.state-loading::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  width: 1.5rem;
  height: 1.5rem;
  margin: -0.75rem 0 0 -0.75rem;
  border: 2px solid var(--accent);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* ===== Disabled State ===== */
.state-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* ===== Success State ===== */
.state-success {
  background-color: var(--success-bg);
  border: 1px solid var(--success);
  color: var(--success);
}

/* ===== Error State ===== */
.state-error {
  background-color: var(--error-bg);
  border: 1px solid var(--error-border);
  color: var(--error);
}

/* ============================================================================
   19. TOOLTIP PATTERN
   ============================================================================ */

.tooltip {
  position: absolute;
  background-color: var(--background);
  border: 1px solid var(--border-color);
  color: var(--foreground);
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
  z-index: 100;
  opacity: 0;
  transition: opacity 200ms cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.tooltip.visible {
  opacity: 1;
}

/* Tooltip arrow */
.tooltip::after {
  content: "";
  position: absolute;
  width: 0.75rem;
  height: 0.75rem;
  background-color: var(--background);
  border-left: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  transform: rotate(45deg);
}

/* ============================================================================
   20. CUSTOM SCROLLBAR
   ============================================================================ */

/* Webkit browsers (Chrome, Safari, Edge) */
::-webkit-scrollbar {
  width: 0.5rem;
  height: 0.5rem;
}

::-webkit-scrollbar-track {
  background-color: var(--background);
}

::-webkit-scrollbar-thumb {
  background-color: var(--border-color);
  border-radius: 0.25rem;
}

::-webkit-scrollbar-thumb:hover {
  background-color: var(--accent);
}

/* ============================================================================
   21. COMPONENT USAGE PATTERNS - REAL EXAMPLES FROM PULSEMAX
   ============================================================================ */

/* ===== Card with Top Border Accent ===== */
/*
<div className="card-hover rounded-lg p-6 border drop-in-3"
     style={{
       backgroundColor: 'var(--card-bg)',
       borderColor: 'var(--border-color)',
       borderTopWidth: '4px',
       borderTopColor: 'var(--accent)'
     }}>
  <h2 className="text-xl font-semibold mb-2">Title</h2>
  <p className="mb-3 text-sm" style={{ color: 'var(--text-secondary)' }}>Description</p>
  <div className="font-medium" style={{ color: 'var(--accent)' }}>View →</div>
</div>
*/

/* ===== Card with Left Border Accent ===== */
/*
<div className="rounded-lg p-6 border card-hover"
     style={{
       backgroundColor: 'var(--card-bg)',
       borderColor: 'var(--border-color)',
       borderLeftWidth: '4px',
       borderLeftColor: '#14b8a6'
     }}>
  <h3 className="text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
    Metric Title
  </h3>
  <div className="text-3xl font-bold" style={{ color: 'var(--foreground)' }}>
    Value
  </div>
</div>
*/

/* ===== Live Indicator ===== */
/*
<div className="flex items-center gap-2">
  <div className="w-3 h-3 rounded-full animate-pulse"
       style={{ backgroundColor: 'var(--accent)' }} />
  <span style={{ color: 'var(--text-secondary)' }}>Live</span>
</div>
*/

/* ===== Button with Hover Effect (inline styles) ===== */
/*
<button
  className="px-4 py-2 rounded-lg font-medium transition-all"
  style={{
    backgroundColor: '#14b8a6',
    color: '#ffffff',
    transition: 'background-color 0.2s ease'
  }}
  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#5eead4'}
  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#14b8a6'}>
  Button Text
</button>
*/

/* ===== Page Header Pattern ===== */
/*
<div className="mb-8 drop-in-1">
  <h1 className="text-4xl md:text-5xl font-bold mb-2"
      style={{ color: 'var(--accent)' }}>
    Page Title
  </h1>
  <p className="text-lg md:text-xl"
     style={{ color: 'var(--text-secondary)' }}>
    Subtitle or description
  </p>
</div>
*/

/* ===== Feature List with Bullet Points ===== */
/*
<div className="flex items-start">
  <div className="w-2 h-2 rounded-full mt-2 mr-3 bg-accent"></div>
  <div>
    <h4 className="font-semibold mb-1">Feature Title</h4>
    <p className="text-secondary">Feature description</p>
  </div>
</div>
*/

/* ============================================================================
   END OF DESIGN SYSTEM
   ============================================================================ */

/* ============================================================================
   QUICK REFERENCE GUIDE
   ============================================================================ */

/*
KEY COLORS:
- Background: #141414 (Netflix black)
- Card: #1f1f1f (slightly lighter)
- Accent: #14b8a6 (teal)
- Text: #ffffff (white), #b3b3b3 (gray), #808080 (muted)

COMMON PATTERNS:
1. Card with hover: .card-hover
2. Staggered animations: .drop-in-1 through .drop-in-11
3. Border accents: borderTopColor/borderLeftColor with var(--accent)
4. Live indicator: rounded-full + animate-pulse
5. Inline CSS variables: style={{ color: 'var(--accent)' }}

COMPONENT STRUCTURE:
- Use inline styles for CSS variables
- Combine Tailwind utilities with custom classes
- Apply drop-in-X classes for page load animations
- Use card-hover for interactive cards

RESPONSIVE APPROACH:
- Mobile-first with md: and lg: breakpoints
- Grid layouts: grid-cols-1 md:grid-cols-2 lg:grid-cols-3
- Text sizing: text-xl md:text-2xl lg:text-3xl
- Padding/spacing: p-4 md:p-6 lg:p-8
*/