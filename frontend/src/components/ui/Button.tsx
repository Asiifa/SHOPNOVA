import { forwardRef } from "react";

export const Button = forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ className = "", disabled, children, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled}
      className={`btn-primary ${className}`}
      {...props}
    >
      {children}
    </button>
  ),
);
Button.displayName = "Button";
