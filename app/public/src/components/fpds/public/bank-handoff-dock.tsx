"use client";
import { useEffect, useRef, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import type { PublicProduct } from '@/lib/public-api';
import { bankHandoffCopy, officialDestination } from '@/lib/public-bank-handoff';
import { TrackedOfficialBankLink } from '@/components/fpds/public/product-engagement-link';
import { Button } from '@/components/ui/button';

export function BankHandoffDock({ products, locale }: { products: PublicProduct[]; locale: string }) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [keyboard, setKeyboard] = useState(false);
  const dockRef = useRef<HTMLDivElement>(null);
  const ids = products.map(product => product.product_id).join('|');
  useEffect(() => {
    const viewport = window.visualViewport;
    const update = () => {
      const element = document.activeElement;
      const editing = element instanceof HTMLElement && element.matches('input, textarea, select, [contenteditable="true"]');
      setKeyboard(editing || !!(viewport && viewport.scale === 1 && window.innerHeight - viewport.height > 120));
      const articles = [...document.querySelectorAll<HTMLElement>('[data-handoff-product]')].filter(node => ids.split('|').includes(node.dataset.handoffProduct ?? ''));
      const midpoint = window.innerHeight * 0.4;
      const visible = articles.filter(node => { const rect = node.getBoundingClientRect(); return rect.bottom > 80 && rect.top < window.innerHeight - 140; });
      if (visible.length) {
        const nearest = visible.find(node => { const rect = node.getBoundingClientRect(); return rect.top <= midpoint && rect.bottom >= midpoint; }) ?? visible.reduce((best, node) => Math.abs(node.getBoundingClientRect().top - midpoint) < Math.abs(best.getBoundingClientRect().top - midpoint) ? node : best);
        setActiveId(nearest.dataset.handoffProduct ?? null);
      }
    };
    let frame = 0;
    const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(update); };
    update();
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    document.addEventListener('focusin', schedule);
    document.addEventListener('focusout', schedule);
    viewport?.addEventListener('resize', schedule);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('scroll', schedule); window.removeEventListener('resize', schedule);
      document.removeEventListener('focusin', schedule); document.removeEventListener('focusout', schedule);
      viewport?.removeEventListener('resize', schedule);
    };
  }, [ids]);
  const product = products.find(item => item.product_id === activeId) ?? products[0];
  const destination = officialDestination(product?.product_url);
  useEffect(() => {
    const dock = dockRef.current;
    if (!dock || !destination) return;
    const update = () => document.documentElement.style.setProperty('--bank-handoff-height', dock.getBoundingClientRect().height + 'px');
    const observer = new ResizeObserver(update);
    observer.observe(dock); update();
    return () => { observer.disconnect(); document.documentElement.style.removeProperty('--bank-handoff-height'); };
  }, [destination]);
  if (!product || !destination) return null;
  const copy = bankHandoffCopy(locale);
  return <div ref={dockRef} data-bank-handoff-dock data-keyboard={keyboard ? 'open' : 'closed'} className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 md:hidden">
    <p className="truncate text-sm font-semibold" title={product.product_name}>{product.product_name}</p>
    <Button asChild className="mt-2 min-h-11 w-full">
      <TrackedOfficialBankLink countryCode={product.country_code} productId={product.product_id} href={destination.href}>
        {copy.action}<ExternalLink className="size-4 shrink-0" aria-hidden="true" /><span className="sr-only">({copy.external})</span>
      </TrackedOfficialBankLink>
    </Button>
  </div>;
}
