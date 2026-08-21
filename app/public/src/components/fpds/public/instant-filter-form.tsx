"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, type ReactNode, useEffect, useRef, useState, useTransition } from "react";

type InstantFilterFormProps = {
  action: string;
  children: ReactNode;
  pendingMessage: string;
};

const SEARCH_DEBOUNCE_MS = 350;

export function InstantFilterForm({ action, children, pendingMessage }: InstantFilterFormProps) {
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isPending, startTransition] = useTransition();
  const [isDebouncing, setIsDebouncing] = useState(false);

  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  function navigateFromForm(form: HTMLFormElement) {
    const params = new URLSearchParams();
    const formData = new FormData(form);

    for (const [key, rawValue] of formData.entries()) {
      const value = String(rawValue);
      if (key === "q") {
        const searchQuery = value.trim().replace(/\s+/g, " ").slice(0, 120);
        if (searchQuery) {
          params.set(key, searchQuery);
        }
      } else if (
        (key === "locale" && value === "en")
        || (key === "country_code" && value === "CA")
      ) {
        continue;
      } else if (value) {
        params.append(key, value);
      }
    }

    const query = params.toString();
    startTransition(() => {
      router.replace(query ? `${action}?${query}` : action, { scroll: false });
    });
  }

  function handleChange(event: FormEvent<HTMLFormElement>) {
    const target = event.target as HTMLInputElement | HTMLSelectElement;
    if (!target.name) {
      return;
    }

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (target.name === "q") {
      setIsDebouncing(true);
      debounceRef.current = setTimeout(() => {
        setIsDebouncing(false);
        if (formRef.current) {
          navigateFromForm(formRef.current);
        }
      }, SEARCH_DEBOUNCE_MS);
      return;
    }

    setIsDebouncing(false);
    navigateFromForm(event.currentTarget);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    setIsDebouncing(false);
    navigateFromForm(event.currentTarget);
  }

  const isUpdating = isPending || isDebouncing;

  return (
    <form
      action={action}
      aria-busy={isUpdating}
      className="grid gap-4"
      onChange={handleChange}
      onSubmit={handleSubmit}
      ref={formRef}
    >
      {children}
      <p className="sr-only" aria-live="polite">
        {isUpdating ? pendingMessage : ""}
      </p>
    </form>
  );
}
