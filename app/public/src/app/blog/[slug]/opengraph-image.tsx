import { ImageResponse } from 'next/og';
import { notFound } from 'next/navigation';
import { BLOG_POSTS, isBlogSlug } from '@/lib/public-blog';
import { blogContent } from '@/lib/public-blog-content';

export const alt = 'SwitchaBank bank account comparison';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!isBlogSlug(slug)) notFound();
  const post = BLOG_POSTS.find(item => item.slug === slug)!;
  const content = blogContent(slug, 'en');
  const chequing = post.productType === 'chequing';
  return new ImageResponse(<div style={{ display: 'flex', width: '100%', height: '100%', flexDirection: 'column', justifyContent: 'space-between', padding: 70, background: '#f4f1e9', color: '#1c2723' }}>
    <div style={{ display: 'flex', fontSize: 27, color: '#176b55' }}>SwitchaBank / Blog / {post.issue}</div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', fontSize: 66, fontWeight: 700, lineHeight: 1.1 }}>{chequing ? 'What does “free banking” cost?' : 'Read beyond the headline rate.'}</div>
      <div style={{ display: 'flex', fontSize: 34 }}>{content.rows.map(row => row.bank).join(' · ')}</div>
    </div>
    <div style={{ display: 'flex', borderTop: '2px solid #d8d4ca', paddingTop: 25, fontSize: 24 }}>
      {chequing ? 'Canadian chequing / Monthly fees, balance rebates and ATM costs' : 'Canadian savings / Rates, conditions and transaction costs'}
    </div>
  </div>, size);
}
