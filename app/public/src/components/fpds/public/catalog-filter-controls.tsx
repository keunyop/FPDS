"use client";

import { useEffect, useRef, useState, type ReactNode, type InputHTMLAttributes, type SelectHTMLAttributes } from "react";

// Keep controls mounted through URL updates so keyboard focus and selection survive.
export function CatalogSearchInput({ value, ...props }: Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "defaultValue"> & { value: string }) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const input = ref.current;
    // Preserve an in-flight draft, but let back/forward and cleared filters restore it.
    const editing = input && document.activeElement === input && input.form?.getAttribute("aria-busy") === "true";
    if (input && !editing) input.value = value;
  }, [value]);
  return <input {...props} defaultValue={value} ref={ref} />;
}

export function CatalogCheckbox({ checked, ...props }: Omit<InputHTMLAttributes<HTMLInputElement>, "checked" | "defaultChecked"> & { checked: boolean }) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => { if (ref.current) ref.current.checked = checked; }, [checked]);
  return <input {...props} defaultChecked={checked} ref={ref} />;
}

export function CatalogSelect({ value, ...props }: Omit<SelectHTMLAttributes<HTMLSelectElement>, "value" | "defaultValue"> & { value: string }) {
  const ref = useRef<HTMLSelectElement>(null);
  useEffect(() => { if (ref.current) ref.current.value = value; }, [value]);
  return <select {...props} defaultValue={value} ref={ref} />;
}

export function CatalogFilterDisclosure({ children, initialOpen }: { children: ReactNode; initialOpen: boolean }) {
  const [open, setOpen] = useState(initialOpen);
  return <details className="group overflow-hidden rounded-lg border border-border bg-card/55" open={open} onToggle={(event) => setOpen(event.currentTarget.open)}>{children}</details>;
}
